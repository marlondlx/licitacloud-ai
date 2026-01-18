import pdfplumber
import re

# Configuração: Palavras-chave que indicam que achamos um item de T.I.
PALAVRAS_CHAVE = [
    "processador", "intel", "amd", "core i", "ryzen", 
    "memória ram", "ddr4", "ddr5", "ssd", "nvme", 
    "placa de vídeo", "garantia", "windows 10", "windows 11"
]

def ler_edital(caminho_pdf):
    print(f"--- Iniciando leitura do arquivo: {caminho_pdf} ---")
    
    dados_encontrados = []

    try:
        with pdfplumber.open(caminho_pdf) as pdf:
            # Loop por cada página do PDF
            for i, pagina in enumerate(pdf.pages):
                texto = pagina.extract_text()
                if not texto:
                    continue # Pula página se for imagem escaneada sem OCR

                # Transformamos tudo em minúsculo para facilitar a busca
                linhas = texto.lower().split('\n')

                for linha in linhas:
                    # Verifica se alguma palavra-chave está nesta linha
                    if any(chave in linha for chave in PALAVRAS_CHAVE):
                        # Limpeza básica: remove espaços extras
                        linha_limpa = linha.strip()
                        
                        # Guarda o resultado: Página + Texto encontrado
                        dados_encontrados.append({
                            "pagina": i + 1,
                            "texto": linha_limpa
                        })
        
        return dados_encontrados

    except Exception as e:
        print(f"Erro ao ler o PDF: {e}")
        return []

# --- ÁREA DE TESTE ---
if __name__ == "__main__":
    # 1. Coloque um PDF de edital real na mesma pasta do script
    # 2. Mude o nome abaixo para o nome do seu arquivo
    arquivo_teste = "edital_exemplo.pdf" 
    
    # Verificação simples se o arquivo existe (para não dar erro bobo)
    import os
    if os.path.exists(arquivo_teste):
        resultado = ler_edital(arquivo_teste)
        
        print(f"\n--- Resultado: Encontrei {len(resultado)} linhas relevantes ---\n")
        
        for item in resultado:
            print(f"[Pág {item['pagina']}] {item['texto']}")
            print("-" * 50)
    else:
        print(f"ATENÇÃO: Não encontrei o arquivo '{arquivo_teste}'.")
        print("Coloque um PDF na pasta e atualize o nome no código.")