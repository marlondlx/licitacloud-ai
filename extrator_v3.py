import pdfplumber
import re
import json

def extrair_v3(caminho_pdf):
    print(f"--- Processando V3: {caminho_pdf} ---")
    
    specs = {
        "processador": [],
        "ram": [],
        "armazenamento": [],
        "garantia": []
    }

    try:
        with pdfplumber.open(caminho_pdf) as pdf:
            texto_completo = ""
            for pagina in pdf.pages:
                texto_completo += " " + pagina.extract_text().lower()

        # 1. PROCESSADOR: Mais flexível
        # Pega "intel core" mesmo sem número, ou "i5/i7" solto, ou "ryzen"
        p_cpu = r"(intel\s?core|ryzen|processador\s?x86|i5-\d+|i7-\d+)"
        specs["processador"] = list(set(re.findall(p_cpu, texto_completo)))

        # 2. RAM: Mais rigorosa para não pegar SSD
        # Estratégia: Procura números típicos de RAM (4, 8, 16, 32...) seguidos de GB
        # OU procura qualquer coisa que tenha "ddr4" ou "ddr5"
        p_ram_size = r"\b(4|8|16|32|64|128)\s?gb\b" 
        p_ram_type = r"(ddr\d)"
        
        matches_size = re.findall(p_ram_size, texto_completo)
        matches_type = re.findall(p_ram_type, texto_completo)
        
        # Monta uma lista combinada (ex: "16 gb", "ddr4")
        if matches_size:
            specs["ram"].extend([f"{m} gb" for m in matches_size])
        if matches_type:
            specs["ram"].extend(matches_type)
        specs["ram"] = list(set(specs["ram"]))

        # 3. ARMAZENAMENTO (SSD/HD)
        p_ssd = r"(ssd.*?|nvme|hd\s?\d+\s?tb)"
        # Pega contexto de 10 caracteres antes e depois de 'ssd' para ver o tamanho
        matches_ssd = re.findall(r"(.{0,10}ssd.{0,15}|nvme)", texto_completo)
        specs["armazenamento"] = [m.strip() for m in matches_ssd if len(m) > 3]

        # 4. GARANTIA: Ignora o texto entre parenteses (ex: 12 (doze) meses)
        # Regex explica: Digito + qualquer coisa opcional no meio + meses/anos
        p_garantia = r"(\d+)\s?.*?(meses|anos)\s?de\s?garantia"
        matches_g = re.search(p_garantia, texto_completo)
        if matches_g:
            specs["garantia"].append(f"{matches_g.group(1)} {matches_g.group(2)}")

        return specs

    except Exception as e:
        print(f"Erro: {e}")
        return {}

if __name__ == "__main__":
    # Substitua pelo nome do seu arquivo se mudou
    arquivo = "edital_exemplo.pdf"
    
    resultado = extrair_v3(arquivo)
    print(json.dumps(resultado, indent=4, ensure_ascii=False))