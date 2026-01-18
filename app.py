import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import os
import altair as alt
from main import extrair_dados_pdf, salvar_no_banco

# ==============================================================================
# CONFIGURAÇÃO VISUAL E CSS
# ==============================================================================
st.set_page_config(page_title="LicitaCloud AI", page_icon="🚀", layout="wide")

st.markdown("""
<style>
    div[data-testid="stMetric"] {
        background-color: #262730;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #363945;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.5);
    }
    h1, h2, h3 { font-family: 'Helvetica Neue', sans-serif; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# FUNÇÕES DE BANCO E SEGURANÇA
# ==============================================================================
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
        return False
    finally:
        conn.close()

def cadastrar_produto(dono_id, nome, tags, custo, venda):
    conn = get_conexao()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO catalogo_produtos (dono_id, nome_produto, tags_match, custo_unitario, preco_venda)
        VALUES (?, ?, ?, ?, ?)
    """, (dono_id, nome, tags.lower(), custo, venda))
    conn.commit()
    conn.close()

def buscar_produto_compativel(item_edital, df_produtos):
    if df_produtos.empty or not item_edital:
        return "Sem Match", 0.0, 0.0
    item_texto = str(item_edital).lower()
    for _, produto in df_produtos.iterrows():
        tags = produto['tags_match'].split(',')
        match = False
        for tag in tags:
            tag_limpa = tag.strip()
            if len(tag_limpa) > 1 and tag_limpa in item_texto:
                match = True
                break
        if match:
            margem = produto['preco_venda'] - produto['custo_unitario']
            return produto['nome_produto'], produto['preco_venda'], margem
    return None, 0.0, 0.0

# ==============================================================================
# INTERFACE DO USUÁRIO
# ==============================================================================

if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = None

# --- TELA DE LOGIN ---
if st.session_state["usuario_logado"] is None:
    col_vazia_esq, col_login, col_vazia_dir = st.columns([1, 2, 1])
    with col_login:
        st.markdown("<h1 style='text-align: center;'>🚀 LicitaCloud AI</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #888;'>Plataforma de Inteligência para Licitações</p>", unsafe_allow_html=True)
        st.divider()
        aba_login, aba_registro = st.tabs(["🔐 Acessar", "📝 Criar Conta"])
        
        with aba_login:
            email_login = st.text_input("E-mail")
            senha_login = st.text_input("Senha", type="password")
            if st.button("Entrar no Sistema", use_container_width=True, type="primary"):
                usuario = verificar_login(email_login, senha_login)
                if usuario:
                    st.session_state["usuario_logado"] = usuario
                    st.rerun()
                else:
                    st.error("Credenciais inválidas.")
        
        with aba_registro:
            novo_nome = st.text_input("Nome")
            novo_email = st.text_input("E-mail de Cadastro")
            nova_senha = st.text_input("Senha de Cadastro", type="password")
            if st.button("Registrar", use_container_width=True):
                if criar_usuario(novo_nome, novo_email, nova_senha):
                    st.success("Conta criada! Faça login.")
                else:
                    st.error("E-mail já existe.")

# --- DASHBOARD LOGADO ---
else:
    usuario = st.session_state["usuario_logado"]
    conn = get_conexao()
    
    with st.sidebar:
        st.markdown(f"### Olá, {usuario['nome']}")
        st.caption("LicitaCloud v1.3 (Pro)")
        st.divider()
        menu = st.radio("Menu", ["📊 Dashboard Executivo", "📦 Produtos & Preços", "📂 Processar Edital"])
        st.divider()
        if st.button("Sair", use_container_width=True):
            st.session_state["usuario_logado"] = None
            st.rerun()

    # --- MENU: UPLOAD MÚLTIPLO ---
    if menu == "📂 Processar Edital":
        st.title("📂 Processamento em Lote")
        st.markdown("Arraste **um ou vários** editais (PDF) para a IA processar de uma vez.")
        
        uploaded_files = st.file_uploader("Selecione os arquivos", type="pdf", accept_multiple_files=True)
        
        if uploaded_files:
            qtd = len(uploaded_files)
            if st.button(f"🚀 Processar {qtd} Editais", type="primary"):
                prog_bar = st.progress(0)
                log_box = st.expander("Logs de Processamento", expanded=True)
                sucessos = 0
                
                for i, file in enumerate(uploaded_files):
                    prog_bar.progress((i + 1) / qtd)
                    try:
                        temp = f"temp_{file.name}"
                        with open(temp, "wb") as f: f.write(file.getbuffer())
                        
                        dados = extrair_dados_pdf(temp)
                        if any(dados.values()):
                            salvar_no_banco(file.name, dados, usuario['id'])
                            log_box.write(f"✅ **{file.name}**: Processado!")
                            sucessos += 1
                        else:
                            log_box.warning(f"⚠️ **{file.name}**: Sem itens de T.I.")
                        
                        if os.path.exists(temp): os.remove(temp)
                    except Exception as e:
                        log_box.error(f"❌ Erro em {file.name}: {e}")
                
                if sucessos > 0:
                    st.balloons()
                    st.success("Processamento Finalizado!")

    # --- MENU: CATÁLOGO ---
    elif menu == "📦 Produtos & Preços":
        st.title("📦 Seu Catálogo")
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1: nome = st.text_input("Produto", placeholder="Ex: Notebook Dell")
        with c2: custo = st.number_input("Custo", 0.0)
        with c3: venda = st.number_input("Venda", 0.0)
        tags = st.text_input("Tags", placeholder="Ex: i5, 8gb, ssd")
        
        if st.button("Salvar Produto", use_container_width=True):
            cadastrar_produto(usuario['id'], nome, tags, custo, venda)
            st.success("Salvo!")
            st.rerun()
            
        df_prods = pd.read_sql_query("SELECT * FROM catalogo_produtos WHERE dono_id=?", conn, params=(usuario['id'],))
        if not df_prods.empty:
            st.dataframe(df_prods[['nome_produto', 'tags_match', 'custo_unitario', 'preco_venda']], use_container_width=True)
        else:
            st.info("Cadastre produtos para habilitar cálculos de lucro.")

    # --- MENU: DASHBOARD (CORRIGIDO) ---
    elif menu == "📊 Dashboard Executivo":
        st.title("📊 Visão Geral")
        
        df_lic = pd.read_sql_query("SELECT * FROM licitacoes WHERE dono_id=? ORDER BY id DESC", conn, params=(usuario['id'],))
        df_itens = pd.read_sql_query("SELECT * FROM itens_extraidos", conn)
        df_prods = pd.read_sql_query("SELECT * FROM catalogo_produtos WHERE dono_id=?", conn, params=(usuario['id'],))

        if not df_lic.empty:
            sel = st.selectbox("Contrato:", df_lic['nome_arquivo'].unique())
            id_lic = df_lic[df_lic['nome_arquivo'] == sel]['id'].values[0]
            itens_lic = df_itens[df_itens['licitacao_id'] == id_lic].copy()
            
            if not itens_lic.empty:
                # --- CORREÇÃO DO BUG AQUI ---
                if not df_prods.empty:
                    res = itens_lic['valor_encontrado'].apply(lambda x: pd.Series(buscar_produto_compativel(x, df_prods)))
                    itens_lic[['Produto', 'Venda', 'Lucro']] = res
                else:
                    itens_lic['Produto'] = None
                    itens_lic['Venda'] = 0.0 # <--- AQUI ESTAVA FALTANDO!
                    itens_lic['Lucro'] = 0.0

                # KPIs
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Itens", len(itens_lic))
                c2.metric("Categorias", itens_lic['tipo_componente'].nunique())
                val_gov = (itens_lic['preco_medio_edital'] * itens_lic['quantidade_edital']).sum()
                c3.metric("Estimativa Gov.", f"R$ {val_gov:,.2f}")
                lucro_total = (itens_lic['Lucro'] * itens_lic['quantidade_edital']).sum()
                c4.metric("Lucro Potencial", f"R$ {lucro_total:,.2f}", delta=f"{lucro_total:,.2f}" if lucro_total > 0 else None)

                st.divider()
                
                # Gráficos
                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    st.subheader("Categorias")
                    chart_data = itens_lic['tipo_componente'].value_counts().reset_index()
                    chart_data.columns = ['Categoria', 'Qtd']
                    c = alt.Chart(chart_data).mark_bar().encode(x='Qtd', y=alt.Y('Categoria', sort='-x'), color=alt.value('#00D4FF'))
                    st.altair_chart(c, use_container_width=True)
                
                with col_g2:
                    st.subheader("Análise Financeira")
                    # Tabela detalhada
                    display_df = itens_lic.copy()
                    display_df['Total Venda'] = display_df['Venda'] * display_df['quantidade_edital']
                    display_df['Total Lucro'] = display_df['Lucro'] * display_df['quantidade_edital']
                    
                    st.dataframe(
                        display_df[['tipo_componente', 'valor_encontrado', 'quantidade_edital', 'Produto', 'Total Lucro']],
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Total Lucro": st.column_config.NumberColumn("Lucro", format="R$ %.2f"),
                            "Produto": "Sugestão"
                        }
                    )
            else:
                st.warning("Sem itens técnicos.")
        else:
            st.info("Nenhuma licitação processada.")
            
    conn.close()