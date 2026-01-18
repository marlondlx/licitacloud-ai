# 🚀 LicitaCloud AI

> **Inteligência Artificial para Análise e Precificação de Licitações de T.I.**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-red)
![Status](https://img.shields.io/badge/Status-MVP%20Funcional-success)

## 📄 Sobre o Projeto

O **LicitaCloud AI** é uma plataforma SaaS (Software as a Service) desenvolvida para automatizar o processo de leitura, extração e precificação de editais de licitação pública focados em Tecnologia da Informação.

O sistema utiliza **Python e Expressões Regulares (Regex)** avançadas para "ler" arquivos PDF complexos, extraindo automaticamente especificações técnicas (Processadores, RAM, SSD, Monitores, Redes, etc.), quantidades e preços estimados pelo governo.

Além da extração, o sistema possui um módulo de **Inteligência de Negócio** que cruza os itens do edital com o catálogo de produtos do usuário, calculando automaticamente a margem de lucro e sugerindo o melhor produto para a disputa.

## 🛠️ Funcionalidades Principais

* **🔐 Sistema Multi-usuário:** Autenticação completa com Login, Registro e isolamento de dados por usuário.
* **📄 Leitura Inteligente de PDF:** Upload de editais e extração automática de texto não estruturado.
* **🧠 Motor de Extração (Regex V7):** Identifica e estrutura dados de:
    * Computadores (CPU, RAM, Armazenamento)
    * Monitores e Periféricos
    * Infraestrutura de Rede (Switches, Cabos)
    * Energia (Nobreaks)
    * Impressão e Software
* **💰 Análise Financeira:** Captura automática de **Quantidade** e **Preço Estimado** nas tabelas do edital.
* **🤝 Match de Produtos:** Algoritmo que cruza os itens do edital com o estoque do usuário e sugere produtos compatíveis.
* **📊 Dashboard de Lucro:** Cálculo automático de margem e potencial total de lucro por contrato.

## 💻 Stack Tecnológica

* **Linguagem:** Python
* **Interface (Frontend):** Streamlit
* **Banco de Dados:** SQLite (Relacional)
* **Manipulação de Dados:** Pandas
* **Processamento de PDF:** pdfplumber
* **Segurança:** Hashlib (SHA-256 para senhas)

## 🚀 Como Rodar o Projeto

Siga os passos abaixo para rodar a aplicação no seu ambiente local:

1. Clone o repositório

git clone [https://github.com/marlondlx/licitacloud-ai.git](https://github.com/marlondlx/licitacloud-ai.git)
cd licitacloud-ai

2. Crie um ambiente virtual (Recomendado)

python -m venv venv
# No Windows:
venv\Scripts\activate
# No Linux/Mac:
source venv/bin/activate

3. Instale as dependências

pip install -r requirements.txt

4. Configure o Banco de Dados
Execute o script de setup para criar as tabelas limpas e zeradas:

python setup_banco.py

5. Inicie a Aplicação

streamlit run app.py
O sistema abrirá automaticamente no seu navegador em http://localhost:8501.

📂 Estrutura do Projeto
app.py: Interface do usuário (Frontend). Gerencia login, cadastro de produtos, upload e o dashboard analítico.

main.py: O "cérebro" da aplicação. Contém a lógica de extração V7, regras de limpeza de dados e Regex.

setup_banco.py: Utilitário para criar/resetar a estrutura do banco de dados SQLite.

requirements.txt: Lista de dependências do Python necessárias para execução.

🔮 Próximos Passos (Roadmap)
[ ] Deploy na Nuvem (Azure/AWS) para acesso remoto via navegador.

[ ] Integração com API da OpenAI (GPT-4) para interpretar editais jurídicos complexos (termos de contrato).

[ ] Geração automática da Proposta Comercial final em PDF.

[ ] Robô de busca automática (Crawler) no Portal de Compras Públicas.

👨‍💻 Autor
Desenvolvido por Marlon Martins

Expertise em Licitações de T.I. e Infraestrutura Cloud.

GitHub