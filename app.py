import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import os
from main import extrair_dados_pdf, salvar_no_banco

# Configuração da Página
st.set_page_config(page_title="LicitaCloud Pro", page_icon="💰", layout="wide")

# ==========================================
# 1. FUNÇÕES DE BANCO E SEGURANÇA
# ==========================================
def get_conexao():
    return sqlite3.connect("licitacloud.db")

def criar_hash(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def verificar_login(email, senha):
    conn = get_conexao()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, senha_hash FROM usuarios WHERE email = ?", (email,))
    usuario = cursor.fetchone()
    conn.close()
    
    if usuario and usuario[2] == criar_hash(senha):
        return {"id": usuario[0], "nome": usuario[1]}
    return None

def criar_usuario(nome, email, senha):
    conn = get_conexao()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO usuarios (nome, email, senha_hash) VALUES (?, ?, ?)", 
                       (nome, email, criar_hash(senha)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False # Email já existe
    finally:
        conn.close()

def cadastrar_produto(dono_id, nome, tags, custo, venda):
    conn = get_conexao()
    cursor = conn.cursor()
    # Garante que tags sejam salvas em minúsculo para facilitar a busca
    cursor.execute("""
        INSERT INTO catalogo_produtos (dono_id, nome_produto, tags_match, custo_unitario, preco_venda)
        VALUES (?, ?, ?, ?, ?)
    """, (dono_id, nome, tags.lower(), custo, venda))
    conn.commit()
    conn.close()

# ==========================================
# 2. INTELIGÊNCIA DE NEGÓCIO (MATCH)
# ==========================================
def buscar_produto_compativel(item_edital, df_produtos):
    if df_produtos.empty or not item_edital:
        return "Sem Match", 0.0, 0.0
    
    item_texto = str(item_edital).lower()
    
    # Percorre cada produto do seu catálogo
    for _, produto in df_produtos.iterrows():
        tags = produto['tags_match'].split(',')
        # Verifica se alguma tag do produto (ex: "i7") está no texto do edital
        match = False
        for tag in tags:
            tag_limpa = tag.strip()
            if len(tag_limpa) > 1 and tag_limpa in item_texto:
                match = True
                break
        
        if match:
            margem = produto['preco_venda'] - produto['custo_unitario']
            return produto['nome_produto'], produto['preco_venda'], margem
            
    return "-", 0.0, 0.0

# ==========================================
# 3. INTERFACE (FRONTEND)
# ==========================================

# Controle de Sessão
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = None

# --- CENÁRIO A: USUÁRIO NÃO LOGADO (TELA DE LOGIN) ---
if st.session_state["usuario_logado"] is None:
    col1, col2 = st.columns(2)
    
    with col1:
        st.image("https://cdn-icons-png.flaticon.com/512/2942/2942544.png", width=120)
        st.title("LicitaCloud Pro")
        st.markdown("### A Inteligência Artificial que bota dinheiro no seu bolso.")
        st.info("Automatize a leitura de editais e encontre oportunidades de lucro instantâneas.")
    
    with col2:
        st.write("## Acesso ao Sistema")
        aba_login, aba_registro = st.tabs(["🔐 Entrar", "📝 Criar Nova Conta"])
        
        with aba_login:
            email_login = st.text_input("E-mail")
            senha_login = st.text_input("Senha", type="password")
            if st.button("Acessar Painel", type="primary"):
                usuario = verificar_login(email_login, senha_login)
                if usuario:
                    st.session_state["usuario_logado"] = usuario
                    st.rerun()
                else:
                    st.error("E-mail ou senha incorretos.")
        
        with aba_registro:
            st.warning("Preencha para começar a lucrar")
            novo_nome = st.text_input("Seu Nome Completo")
            novo_email = st.text_input("Seu E-mail (Login)")
            nova_senha = st.text_input("Sua Senha", type="password")
            if st.button("Registrar Conta"):
                if criar_usuario(novo_nome, novo_email, nova_senha):
                    st.success("Conta criada com sucesso! Acesse a aba 'Entrar'.")
                else:
                    st.error("Erro: Esse e-mail já existe.")

# --- CENÁRIO B: USUÁRIO LOGADO (DASHBOARD) ---
else:
    usuario = st.session_state["usuario_logado"]
    
    # BARRA LATERAL
    with st.sidebar:
        st.write(f"👤 **{usuario['nome']}**")
        st.caption("LicitaCloud Pro v1.0")
        
        if st.button("Sair (Logout)"):
            st.session_state["usuario_logado"] = None
            st.rerun()
            
        st.divider()
        menu = st.radio("Navegação", ["📊 Dashboard & Lucro", "📦 Meu Catálogo", "📂 Nova Licitação"])

    conn = get_conexao()

    # --- TELA 1: UPLOAD DE EDITAL ---
    if menu == "📂 Nova Licitação":
        st.title("Processar Novo Edital")
        st.markdown("Envie o PDF para a IA extrair as especificações técnicas.")
        
        uploaded_file = st.file_uploader("Arraste seu PDF aqui", type="pdf")
        if uploaded_file and st.button("Processar Arquivo"):
            with st.spinner('A IA está lendo o edital...'):
                temp = f"temp_{uploaded_file.name}"
                with open(temp, "wb") as f: f.write(uploaded_file.getbuffer())
                
                dados = extrair_dados_pdf(temp)
                if any(dados.values()):
                    salvar_no_banco(uploaded_file.name, dados, usuario['id'])
                    st.success("✅ Edital processado e salvo no Dashboard!")
                else:
                    st.warning("⚠️ A IA leu o arquivo, mas não encontrou peças de T.I. relevantes.")
                
                if os.path.exists(temp): os.remove(temp)

    # --- TELA 2: CADASTRO DE PRODUTOS ---
    elif menu == "📦 Meu Catálogo":
        st.title("Seu Estoque & Preços")
        st.info("Cadastre aqui os produtos que você vende. A IA usará isso para calcular seu lucro.")
        
        with st.form("form_produto"):
            c1, c2 = st.columns(2)
            nome_prod = c1.text_input("Nome do Produto (Ex: Dell Latitude 3420)")
            tags_prod = c2.text_input("Palavras-chave para Match (Ex: i5, 8gb, ssd)")
            
            c3, c4 = st.columns(2)
            custo_prod = c3.number_input("Seu Custo (R$)", min_value=0.0, step=100.0)
            venda_prod = c4.number_input("Preço de Venda (R$)", min_value=0.0, step=100.0)
            
            if st.form_submit_button("💾 Salvar Produto"):
                cadastrar_produto(usuario['id'], nome_prod, tags_prod, custo_prod, venda_prod)
                st.success("Produto adicionado ao catálogo!")
                st.rerun()
        
        st.divider()
        st.subheader("Produtos Cadastrados")
        df_prods = pd.read_sql_query("SELECT * FROM catalogo_produtos WHERE dono_id = ?", conn, params=(usuario['id'],))
        if not df_prods.empty:
            st.dataframe(df_prods[['nome_produto', 'tags_match', 'custo_unitario', 'preco_venda']], use_container_width=True)
        else:
            st.info("Seu catálogo está vazio.")

    # --- TELA 3: DASHBOARD DE LUCRO ---
    elif menu == "📊 Dashboard & Lucro":
        st.title("Painel de Oportunidades")
        
        # Carrega dados
        df_licitacoes = pd.read_sql_query("SELECT * FROM licitacoes WHERE dono_id=? ORDER BY id DESC", conn, params=(usuario['id'],))
        # CARREGA AS NOVAS COLUNAS
        df_itens = pd.read_sql_query("SELECT * FROM itens_extraidos", conn)
        df_meus_produtos = pd.read_sql_query("SELECT * FROM catalogo_produtos WHERE dono_id=?", conn, params=(usuario['id'],))

        if not df_licitacoes.empty:
            escolha = st.selectbox("Selecione o Edital:", df_licitacoes['nome_arquivo'].unique())
            id_lic = df_licitacoes[df_licitacoes['nome_arquivo'] == escolha]['id'].values[0]
            
            # Filtra e Copia
            itens_da_licitacao = df_itens[df_itens['licitacao_id'] == id_lic].copy()
            
            if not itens_da_licitacao.empty:
                
                # --- MÉTRICAS DO EDITAL (LIDO DO PDF) ---
                total_estimado_gov = (itens_da_licitacao['preco_medio_edital'] * itens_da_licitacao['quantidade_edital']).sum()
                
                m1, m2 = st.columns(2)
                m1.metric("Itens Identificados", len(itens_da_licitacao))
                if total_estimado_gov > 0:
                    m2.metric("Valor Estimado (Governo)", f"R$ {total_estimado_gov:,.2f}")
                else:
                    m2.metric("Valor Estimado", "Não encontrado no PDF")

                st.markdown("### 📋 Análise Detalhada")
                
                if not df_meus_produtos.empty:
                    # Match
                    resultados = itens_da_licitacao['valor_encontrado'].apply(
                        lambda x: pd.Series(buscar_produto_compativel(x, df_meus_produtos))
                    )
                    
                    itens_da_licitacao[['Produto Sugerido', 'Preço Venda', 'Margem Unit.']] = resultados
                    
                    # CÁLCULO DE LUCRO TOTAL (Margem * Quantidade do Edital)
                    itens_da_licitacao['Lucro Total Previsto'] = itens_da_licitacao['Margem Unit.'] * itens_da_licitacao['quantidade_edital']
                    
                    # Renomeia colunas para ficar bonito na tela
                    display_df = itens_da_licitacao[[
                        'tipo_componente', 
                        'valor_encontrado', 
                        'quantidade_edital',      # NOVA COLUNA
                        'preco_medio_edital',     # NOVA COLUNA
                        'Produto Sugerido', 
                        'Lucro Total Previsto'
                    ]]
                    
                    display_df.columns = ['Tipo', 'Item Edital', 'Qtd', 'Preço Gov (Est)', 'Nossa Sugestão', 'Lucro Potencial']
                    
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                    
                    total_lucro = itens_da_licitacao['Lucro Total Previsto'].sum()
                    st.success(f"🤑 **Potencial TOTAL de Lucro neste Contrato: R$ {total_lucro:,.2f}**")
                    
                else:
                    st.warning("Cadastre produtos para ver o cálculo de lucro.")
                    # Mostra tabela simples com as novas colunas
                    st.dataframe(itens_da_licitacao[['tipo_componente', 'valor_encontrado', 'quantidade_edital', 'preco_medio_edital']], use_container_width=True)
            else:
                st.info("Nada encontrado.")
            
    conn.close()