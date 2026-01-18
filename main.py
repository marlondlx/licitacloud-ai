import sqlite3
import pdfplumber
import re
import os
import logging
from datetime import datetime

# ==============================================================================
# CONFIGURAÇÃO DE LOGS (Para você ver o que a IA está pensando)
# ==============================================================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==============================================================================
# 1. PADRÕES DE REGEX (A "MEMÓRIA" DA IA)
# ==============================================================================
# Compilamos os regex fora da função para ganhar performance
PATTERNS = {
    "processador": r"(?:processador|cpu|chip)\s?:?\s?(i[3579]-\d{4,}\w?|ryzen\s?\d\s?\d{4,}\w?|intel\s?core\s?i\d|xeon\s?\w+|epyc)",
    "ram": r"\b(\d{1,3})\s?(?:gb|giga)\s?(?:ddr[345])?\b|(?:\bddr[345]\b\s?)(?:de\s?)?(\d{1,3}\s?gb)",
    "armazenamento": r"(ssd\s?(?:de\s?)?\d+\s?(?:gb|tb)|nvme\s?(?:m\.2)?\s?\d+\s?(?:gb|tb)|hd\s?(?:de\s?)?\d+\s?tb)",
    "monitor": r"(monitor(?:\sled)?|tela)\s(?:de\s)?(\d{2}(?:[\.,]\d)?)\s?(?:pol|legadas|\")|(\d{2,3})\s?hz|full\s?hd|4k\suhd",
    "impressao": r"(multifuncional|impressora)\s?(?:laser|jato\sde\stinta|tanque)?|toner\s(?:para\s)?([a-z0-9-]+)",
    "rede": r"(switch)\s(?:de\s)?(\d+)\s(?:portas|pts)|(cat\s?5e|cat\s?6a?)|(patch\scord|cabo\sutp)",
    "energia": r"(nobreak|ups)\s(?:de\s)?(\d+\.?\d*)\s?(k?va)|(estabilizador)",
    "perifericos": r"(teclado)\s(?:usb|abnt2)|(mouse)\s(?:optico|usb)|(webcam)\s(?:hd|4k)|(headset)",
    "software": r"(windows)\s?(10|11)\s?(pro|home)|(office)\s?(2019|2021|365)|(antivirus)"
}

# Palavras que indicam que NÃO é um item técnico (Filtro de Ruído)
DENY_LIST = ["licitacao", "pregao", "edital", "objeto", "data", "assinatura", "contrato", "cnpj", "cpf"]

# ==============================================================================
# 2. FUNÇÕES UTILITÁRIAS (FERRAMENTAS)
# ==============================================================================

def normalizar_texto(texto):
    """Limpa caracteres invisíveis e padroniza para minúsculo."""
    if not texto: return ""
    # Remove quebras de linha e múltiplos espaços
    texto = re.sub(r'\s+', ' ', texto).strip().lower()
    return texto

def converter_dinheiro(valor_str):
    """
    Transforma 'R$ 1.250,00' ou '1.250,00' em float 1250.00
    """
    try:
        # Remove R$, espaços e pontos de milhar
        limpo = valor_str.lower().replace('r$', '').strip()
        limpo = limpo.replace('.', '') # Remove ponto de milhar (1.000 -> 1000)
        limpo = limpo.replace(',', '.') # Troca vírgula decimal por ponto (1000,00 -> 1000.00)
        return float(limpo)
    except ValueError:
        return 0.0

def extrair_valor_contexto(bloco_texto):
    """
    Busca agressiva por preços no bloco de texto (linhas vizinhas).
    Prioriza valores com 'R$' explicito.
    """
    # 1. Tenta achar com R$ (mais confiável)
    # Ex: R$ 1.500,00
    match_moeda = re.search(r'r\$\s?(\d{1,3}(?:\.\d{3})*,\d{2})', bloco_texto)
    if match_moeda:
        return converter_dinheiro(match_moeda.group(1))
    
    # 2. Se não achar, tenta achar formato monetário XX,XX próximo a palavras chave
    # Ex: Valor Unit: 1.500,00
    if "valor" in bloco_texto or "unit" in bloco_texto or "estimado" in bloco_texto:
        match_num = re.search(r'(\d{1,3}(?:\.\d{3})*,\d{2})', bloco_texto)
        if match_num:
            return converter_dinheiro(match_num.group(1))
            
    return 0.0

def extrair_quantidade_contexto(bloco_texto):
    """
    Busca quantidade ignorando anos (2025, 2026) e índices (1.1, 1.2).
    """
    bloco = bloco_texto.lower()
    
    # Lista de anos para ignorar (evita falso positivo)
    anos_ignorar = [str(y) for y in range(2020, 2030)]
    
    # 1. Busca explícita (qtde: 10)
    match_expl = re.search(r'(?:qtde|qtd|quant|unid|unidade)[\.:\s]*(\d+)', bloco)
    if match_expl: 
        val = int(match_expl.group(1))
        if str(val) not in anos_ignorar: return val

    # 2. Busca o primeiro número inteiro isolado na linha (comum em tabelas)
    # Ex: "10   Computador..."
    match_inicio = re.match(r'^(\d+)\s', bloco.strip())
    if match_inicio:
        val = int(match_inicio.group(1))
        # Filtros de sanidade:
        # - Menor que 10000 (ninguém compra 20 mil computadores num edital comum)
        # - Não é um ano
        if 0 < val < 10000 and str(val) not in anos_ignorar:
            return val
            
    return 1 # Padrão seguro

def validar_item(categoria, texto):
    """O Guardião: Decide se o texto é lixo ou item real."""
    texto = texto.lower()
    
    # Regra 1: Muito curto
    if len(texto) < 3: return False
    
    # Regra 2: Está na lista negra?
    for bad_word in DENY_LIST:
        if bad_word in texto: return False
        
    # Regra 3: Validacoes especificas
    if categoria == "monitor":
        # Evita '00 polegadas' ou '1.5 polegadas'
        if "00 pol" in texto or re.search(r'\b[01]\s?pol', texto): return False
        
    if categoria == "armazenamento":
        if "idade com ssd" in texto: return False # Erro comum de OCR
        
    return True

# ==============================================================================
# 3. CORE: A INTELIGÊNCIA DE EXTRAÇÃO (V9 ENTERPRISE)
# ==============================================================================
def extrair_dados_pdf(caminho_pdf):
    logger.info(f"🔄 Iniciando análise profunda em: {caminho_pdf}")
    
    dados_estruturados = {key: [] for key in PATTERNS.keys()}
    
    try:
        with pdfplumber.open(caminho_pdf) as pdf:
            for i, pagina in enumerate(pdf.pages):
                texto_pagina = pagina.extract_text()
                if not texto_pagina: continue
                
                linhas = texto_pagina.split('\n')
                total_linhas = len(linhas)
                
                # Itera sobre as linhas da página
                for idx_linha, linha in enumerate(linhas):
                    linha_clean = normalizar_texto(linha)
                    
                    # Para cada categoria de T.I.
                    for categoria, regex in PATTERNS.items():
                        match = re.search(regex, linha_clean)
                        
                        if match:
                            item_encontrado = match.group(0)
                            
                            # Validação de Qualidade
                            if not validar_item(categoria, item_encontrado):
                                continue

                            # --- CONTEXTO EXPANDIDO (VISÃO 360) ---
                            # Pega a linha anterior, a atual e as 2 próximas
                            # Isso ajuda quando o preço está acima ou abaixo
                            contexto = []
                            if idx_linha > 0: contexto.append(linhas[idx_linha-1]) # Linha anterior
                            contexto.append(linha) # Atual
                            if idx_linha + 1 < total_linhas: contexto.append(linhas[idx_linha+1]) # Próxima 1
                            if idx_linha + 2 < total_linhas: contexto.append(linhas[idx_linha+2]) # Próxima 2
                            
                            bloco_texto = " ".join(contexto)
                            
                            # Extração Financeira no Bloco
                            preco = extrair_valor_contexto(bloco_texto)
                            qtd = extrair_quantidade_contexto(linha_clean) # Qtd geralmente está na mesma linha
                            
                            # Log para debug (ajuda a entender erros)
                            logger.debug(f"[{categoria.upper()}] Item: {item_encontrado} | Preço: {preco} | Qtd: {qtd}")
                            
                            # Adiciona aos resultados
                            dados_estruturados[categoria].append({
                                "desc": item_encontrado,
                                "qtd": qtd,
                                "preco": preco,
                                "pagina": i + 1 # Bom para auditoria futura
                            })

        # Remove duplicatas exatas (mesmo item, mesmo preço, mesma qtd)
        # Isso acontece se o regex pegar a mesma coisa 2x
        for cat in dados_estruturados:
            # Truque de Python para remover dicts duplicados em lista
            dados_estruturados[cat] = [dict(t) for t in {tuple(d.items()) for d in dados_estruturados[cat]}]

        logger.info(f"✅ Análise concluída.")
        return dados_estruturados

    except Exception as e:
        logger.error(f"❌ Erro crítico ao processar PDF: {e}")
        return {}

# ==============================================================================
# 4. CAMADA DE PERSISTÊNCIA (SALVAR NO BANCO)
# ==============================================================================
def salvar_no_banco(nome_arquivo, dados_extraidos, dono_id):
    logger.info(f"💾 Persistindo dados para usuário ID {dono_id}...")
    
    # Usa Context Manager para garantir que o banco fecha mesmo se der erro
    try:
        with sqlite3.connect("licitacloud.db") as conexao:
            cursor = conexao.cursor()
            
            # Registra o Edital
            cursor.execute("""
                INSERT INTO licitacoes (dono_id, nome_arquivo, status) 
                VALUES (?, ?, ?)
            """, (dono_id, nome_arquivo, 'PROCESSADO'))
            
            id_licitacao = cursor.lastrowid
            
            contador = 0
            for categoria, lista_itens in dados_extraidos.items():
                for item in lista_itens:
                    cursor.execute("""
                        INSERT INTO itens_extraidos 
                        (licitacao_id, tipo_componente, valor_encontrado, quantidade_edital, preco_medio_edital)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        id_licitacao, 
                        categoria, 
                        normalizar_texto(item['desc']), 
                        item['qtd'], 
                        item['preco']
                    ))
                    contador += 1
            
            logger.info(f"✅ Sucesso! {contador} itens gravados na Licitação #{id_licitacao}.")
            
    except sqlite3.Error as e:
        logger.error(f"❌ Erro de Banco de Dados: {e}")
    except Exception as e:
        logger.error(f"❌ Erro genérico ao salvar: {e}")

# ==============================================================================
# 5. EXECUÇÃO LOCAL (PARA TESTES DE DESENVOLVEDOR)
# ==============================================================================
if __name__ == "__main__":
    # Área de teste rápido - Só roda se você executar 'python main.py' direto
    arquivo_teste = "edital_exemplo.pdf"
    if os.path.exists(arquivo_teste):
        print(f"--- Rodando Teste Local em {arquivo_teste} ---")
        resultado = extrair_dados_pdf(arquivo_teste)
        
        for cat, itens in resultado.items():
            if itens:
                print(f"\n📁 Categoria: {cat.upper()}")
                for item in itens:
                    print(f"   -> Item: {item['desc']}")
                    print(f"      Qtd: {item['qtd']} | Preço: R$ {item['preco']:,.2f}")
    else:
        print("⚠️ Arquivo de teste não encontrado.")