import pdfplumber
import re
import json

def extrair_especificacoes_refinadas(caminho_pdf):
    print(f"--- Processando Inteligente: {caminho_pdf} ---")
    
    # Dicionário para guardar o que achamos
    especificacoes = {
        "processador": [],
        "ram": [],
        "armazenamento": [],
        "garantia_tecnica": []
    }

    try:
        with pdfplumber.open(caminho_pdf) as pdf:
            texto_completo = ""
            # Junta todas as páginas num texto só para corrigir quebras de linha
            for pagina in pdf.pages:
                texto_completo += " " + pagina.extract_text().lower()

        # --- A MÁGICA DO REGEX (PADRÕES) ---
        
        # 1. Busca RAM: Procura números seguidos de GB e palavras como DDR3/DDR4
        # Ex: Pega "8gb", "16 gb", "ddr4"
        padrao_ram = r"(\d+\s?gb\s?(?:ddr\d)?)"
        matches_ram = re.findall(padrao_ram, texto_completo)
        if matches_ram:
            especificacoes["ram"] = list(set(matches_ram)) # set() remove duplicados

        # 2. Busca Processador: Intel Core ou AMD Ryzen
        padrao_cpu = r"(intel\s?core\s?i\d|amd\s?ryzen\s?\d|processador\s?x86)"
        matches_cpu = re.findall(padrao_cpu, texto_completo)
        if matches_cpu:
            especificacoes["processador"] = list(set(matches_cpu))

        # 3. Busca SSD/HD: Procura "SSD" ou "HD" seguido de tamanho
        padrao_disco = r"(ssd\s?\.?\s?\d+\s?gb|hd\s?\d+\s?tb|nvme)"
        matches_disco = re.findall(padrao_disco, texto_completo)
        if matches_disco:
            especificacoes["armazenamento"] = list(set(matches_disco))

        # 4. Busca Garantia Técnica (e tenta ignorar FGTS)
        # Só pega se tiver "meses" ou "anos" perto da palavra garantia
        padrao_garantia = r"(\d+\s?(?:meses|anos)\s?de\s?garantia|garantia\s?de\s?\d+\s?(?:meses|anos))"
        matches_garantia = re.findall(padrao_garantia, texto_completo)
        if matches_garantia:
            especificacoes["garantia_tecnica"] = list(set(matches_garantia))

        return especificacoes

    except Exception as e:
        print(f"Erro: {e}")
        return {}

# --- TESTE ---
if __name__ == "__main__":
    arquivo = "edital_exemplo.pdf" # O mesmo arquivo que você usou antes
    
    resultado = extrair_especificacoes_refinadas(arquivo)
    
    print("\n--- DADOS ESTRUTURADOS (JSON) ---")
    # Imprime bonito (indentado) como se fosse um JSON de API
    print(json.dumps(resultado, indent=4, ensure_ascii=False))