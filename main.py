import sqlite3
import pdfplumber
import re
import os

# ==============================================================================
# 1. FUNÇÕES DE LIMPEZA E EXTRAÇÃO FINANCEIRA (V7 - GANANCIOSA)
# ==============================================================================
def limpar_texto(texto):
    if not texto: return ""
    # Remove caracteres estranhos e espaços duplos
    return re.sub(r'\s+', ' ', texto.replace('\n', ' ').strip())

def extrair_valor_monetario(linha):
    """
    V7: Pega valores mesmo sem R$. Procura padrão: numeros.numeros,centavos
    Ex: Pega '1.500,00' e 'R$ 1500,00'
    """
    # Regex explica: 
    # (?:r\$\s?)? -> "R$" é opcional
    # (\d{1,3}(?:\.\d{3})*,\d{2}) -> Padrão brasileiro 1.000,00
    match = re.search(r'(?:r\$\s?)?(\d{1,3}(?:\.\d{3})*,\d{2})', linha.lower())
    if match:
        valor_str = match.group(1).replace('.', '').replace(',', '.')
        try:
            return float(valor_str)
        except:
            return 0.0
    return 0.0

def extrair_quantidade(linha):
    """
    V7: Pega números no INÍCIO da linha (padrão de tabela) ou com palavras chaves.
    """
    linha = linha.lower().strip()
    
    # Prioridade 1: Palavras explícitas (qtde, quant: 10)
    match_expl = re.search(r'(?:qtde|qtd|quant|quantidade)[\.:\s]*(\d+)', linha)
    if match_expl:
        return int(match_expl.group(1))
        
    # Prioridade 2: Número solto no começo da linha (Ex: "10   Computador...")
    # Pega apenas se for número entre 1 e 9999 (evita pegar código do item tipo 'Item 1.1')
    match_inicio = re.match(r'^(\d+)\s', linha)
    if match_inicio:
        qtd = int(match_inicio.group(1))
        if 0 < qtd < 10000: 
            return qtd
            
    return 1 # Padrão se não achar nada

def validar_lixo(categoria, texto):
    texto = texto.lower()
    
    # Filtro de tamanho mínimo
    if len(texto) < 4: return False
    
    # Filtros específicos por categoria
    if categoria == "monitor":
        # Remove lixo como "00 pol" ou polegadas irreais
        nums = re.findall(r'\d+', texto)
        if nums:
            tamanho = int(nums[0])
            if tamanho < 15 or tamanho > 100: return False # Ignora menor que 15"
            if texto.startswith("0"): return False # Ignora "00"
            
    if categoria == "armazenamento":
        if "idade com ssd" in texto: return False
        
    return True

# ==============================================================================
# 2. O CÉREBRO (EXTRAÇÃO V7)
# ==============================================================================
def extrair_dados_pdf(caminho_pdf):
    print(f"🔄 Processando V7 (Smath Match): {caminho_pdf}...")
    
    dados_brutos = {
        "processador": [], "ram": [], "armazenamento": [], "monitor": [],
        "impressao": [], "rede": [], "energia": [], "perifericos": [], "software": []
    }
    
    try:
        with pdfplumber.open(caminho_pdf) as pdf:
            for pagina in pdf.pages:
                texto_pagina = pagina.extract_text()
                if not texto_pagina: continue
                
                linhas = texto_pagina.split('\n')
                
                for linha in linhas:
                    linha_lower = linha.lower()
                    
                    # Dicionário de Regex (Mesmo da versão anterior)
                    padroes = {
                        "processador": r"(i[3579]-\d{4,}|ryzen\s?\d|intel\s?core\s?i\d|xeon)",
                        "ram": r"\b(4|8|16|32|64|128)\s?gb\b",
                        "armazenamento": r"(ssd\s?(?:de\s?)?\d+\s?(?:gb|tb)|nvme\s?\d+\s?(?:gb|tb)|hd\s?\d+\s?tb)",
                        # Monitor: Ajustado para ser mais restrito e evitar '00 pol'
                        "monitor": r"(monitor\sled|\d{2}[\.,]?\d?\s?polegadas|\d{2}\"?\s?pol|full\s?hd)", 
                        "impressao": r"(multifuncional|impressora\s(?:laser|tanque)|toner\s[a-z0-9]+)",
                        "rede": r"(switch\s\d+\sportas|cat\s?6|rack\s\d+u|patch\scord)",
                        "energia": r"(nobreak\s\d+\.?\d*\s?k?va|estabilizador)",
                        "perifericos": r"(teclado\sabnt2|mouse\soptico|webcam|headset\susb)",
                        "software": r"(windows\s1[01]\spro|office\s20\d{2})"
                    }

                    for cat, regex in padroes.items():
                        match = re.search(regex, linha_lower)
                        if match:
                            item_encontrado = match.group(0)
                            
                            if validar_lixo(cat, item_encontrado):
                                # Extrai Preço e Qtd da MESMA LINHA onde achou o item
                                qtd = extrair_quantidade(linha_lower)
                                preco = extrair_valor_monetario(linha_lower)
                                
                                dados_brutos[cat].append({
                                    "desc": item_encontrado,
                                    "qtd": qtd,
                                    "preco": preco
                                })
        return dados_brutos

    except Exception as e:
        print(f"❌ Erro: {e}")
        return {}

# ==============================================================================
# 3. O SALVADOR (SALVA NO BANCO)
# ==============================================================================
def salvar_no_banco(nome_arquivo, dados_extraidos, dono_id):
    conexao = sqlite3.connect("licitacloud.db")
    cursor = conexao.cursor()

    try:
        cursor.execute("INSERT INTO licitacoes (dono_id, nome_arquivo, status) VALUES (?, ?, ?)", 
                       (dono_id, nome_arquivo, 'PROCESSADO'))
        id_licitacao = cursor.lastrowid 
        
        contador = 0
        for categoria, lista_itens in dados_extraidos.items():
            for item_obj in lista_itens:
                item_limpo = limpar_texto(item_obj['desc'])
                
                cursor.execute("""
                    INSERT INTO itens_extraidos (licitacao_id, tipo_componente, valor_encontrado, quantidade_edital, preco_medio_edital)
                    VALUES (?, ?, ?, ?, ?)
                """, (id_licitacao, categoria, item_limpo, item_obj['qtd'], item_obj['preco']))
                contador += 1
        
        conexao.commit()
        print(f"✅ Sucesso! {contador} itens salvos.")

    except Exception as e:
        print(f"❌ Erro SQL: {e}")
        conexao.rollback()
    finally:
        conexao.close()