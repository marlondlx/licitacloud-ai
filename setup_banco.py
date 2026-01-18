import sqlite3
import hashlib

def criar_banco():
    print("--- Criando Banco V3 (Com Preços e Quantidades) ---")
    conexao = sqlite3.connect("licitacloud.db")
    cursor = conexao.cursor()
    
    # 1. Usuários
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        senha_hash TEXT NOT NULL,
        nome TEXT
    )
    """)
    
    # 2. Licitações
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS licitacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dono_id INTEGER NOT NULL,
        nome_arquivo TEXT NOT NULL,
        data_processamento DATETIME DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'PROCESSADO',
        FOREIGN KEY (dono_id) REFERENCES usuarios (id)
    )
    """)
    
    # 3. Itens (AGORA COM PREÇO E QUANTIDADE DO EDITAL)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS itens_extraidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        licitacao_id INTEGER,
        tipo_componente TEXT,
        valor_encontrado TEXT,
        quantidade_edital INTEGER DEFAULT 1,    -- NOVO
        preco_medio_edital REAL DEFAULT 0.0,    -- NOVO
        FOREIGN KEY (licitacao_id) REFERENCES licitacoes (id)
    )
    """)

    # 4. Catálogo
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS catalogo_produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dono_id INTEGER NOT NULL,
        nome_produto TEXT NOT NULL,
        tags_match TEXT NOT NULL,
        custo_unitario REAL,
        preco_venda REAL,
        FOREIGN KEY (dono_id) REFERENCES usuarios (id)
    )
    """)
    
    print("✅ Banco atualizado com suporte a Quantidade e Preço!")
    conexao.commit()
    conexao.close()

if __name__ == "__main__":
    criar_banco()