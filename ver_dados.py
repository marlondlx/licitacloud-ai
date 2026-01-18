import sqlite3

# Conecta e puxa tudo
conexao = sqlite3.connect("licitacloud.db")
cursor = conexao.cursor()

print("\n=== LICITAÇÕES CADASTRADAS ===")
cursor.execute("SELECT * FROM licitacoes")
for linha in cursor.fetchall():
    print(linha)

print("\n=== ITENS TÉCNICOS ENCONTRADOS ===")
cursor.execute("SELECT * FROM itens_extraidos")
for linha in cursor.fetchall():
    print(linha)

conexao.close()
