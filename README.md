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

### 1. Clone o repositório
```bash
git clone [https://github.com/marlondlx/licitacloud-ai.git](https://github.com/marlondlx/licitacloud-ai.git)
cd licitacloud-ai