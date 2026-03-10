import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Resseling Pro", layout="wide")

# --- LOGIN (Mantém a tua pass nas Secrets) ---
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False
    if "password_correct" not in st.session_state:
        st.title("🔐 Acesso Restrito")
        st.text_input("Password do Império", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.error("❌ Errado. Tenta outra vez.")
        return False
    return True

if not check_password():
    st.stop()

# --- LIGAÇÃO E DADOS ---
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(ttl=0)

# Colunas base para o negócio não descarrilar
colunas_base = ["Nome", "Link", "Preco_China", "Portes", "Preco_Venda", "Data_Registo", "Estado"]

if df.empty or df is None:
    df = pd.DataFrame(columns=colunas_base)

st.title("🚀 Gestão de Importação & Vendas")

# --- FORMULÁRIO COM DATA E ESTADO (Ideia 1 e 4) ---
with st.expander("➕ Registar Nova Carga da China", expanded=False):
    with st.form("entrada_dados"):
        col_a, col_b = st.columns(2)
        with col_a:
            nome = st.text_input("O que compraste?")
            link = st.text_input("Link acbuy")
            data_hoje = st.date_input("Data da Compra", datetime.now())
        with col_b:
            estado = st.selectbox("Estado Inicial", ["Encomendado", "Em Trânsito", "Em Stock", "Vendido"])
            p_china = st.number_input("Preço China (X)", min_value=0.0)
            portes = st.number_input("Portes (Y)", min_value=0.0)
            venda = st.number_input("Preço Venda (Z)", min_value=0.0)
        
        if st.form_submit_button("Lançar no Sistema"):
            novo = pd.DataFrame([{"Nome": nome, "Link": link, "Preco_China": p_china, "Portes": portes, 
                                  "Preco_Venda": venda, "Data_Registo": str(data_hoje), "Estado": estado}])
            df = pd.concat([df, novo], ignore_index=True)
            conn.update(data=df)
            st.cache_data.clear()
            st.rerun()

# --- LOGICA DE TRATAMENTO DE DADOS ---
if not df.empty:
    df['Data_Registo'] = pd.to_datetime(df['Data_Registo'])
    df['Dias_Stock'] = (datetime.now() - df['Data_Registo']).dt.days
    df['Custo_Total'] = df['Preco_China'] + df['Portes']
    df['Lucro'] = df['Preco_Venda'] - df['Custo_Total']

    # --- MÉTRICAS (Ideia 2: Lucro Real vs Potencial) ---
    stock_ativo = df[df['Estado'] != 'Vendido']
    vendidos = df[df['Estado'] == 'Vendido']

    m1, m2, m3 = st.columns(3)
    m1.metric("Investimento em Trânsito/Stock", f"{stock_ativo['Custo_Total'].sum():.2f}€")
    m2.metric("Lucro REAL (Dinheiro no Bolso)", f"{vendidos['Lucro'].sum():.2f}€")
    m3.metric("Itens Críticos (+30 dias)", len(stock_ativo[stock_ativo['Dias_Stock'] > 30]))

    # --- TABELA DE GESTÃO (Ideia 1 e 4) ---
    st.subheader("📦 Inventário em Tempo Real")
    
    # Configuração visual da tabela
    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        column_order=("Estado", "Nome", "Dias_Stock", "Preco_China", "Portes", "Preco_Venda", "Lucro", "Link"),
        column_config={
            "Estado": st.column_config.SelectboxColumn("Estado", options=["Encomendado", "Em Trânsito", "Em Stock", "Vendido"], required=True),
            "Dias_Stock": st.column_config.NumberColumn("Dias em Stock", help="Há quanto tempo este item está a ocupar espaço"),
            "Lucro": st.column_config.NumberColumn("Lucro Est.", format="%.2f€"),
            "Link": st.column_config.LinkColumn("Link")
        }
    )

    if st.button("💾 Guardar Todas as Alterações"):
        # Limpamos as colunas calculadas antes de gravar na Google
        final_save = edited_df[colunas_base]
        conn.update(data=final_save)
        st.cache_data.clear()
        st.success("Sistema atualizado!")
        st.rerun()

    # --- ALERTA DE STOCK PODRE (Ideia 4) ---
    itens_velhos = stock_ativo[stock_ativo['Dias_Stock'] > 30]
    if not itens_velhos.empty:
        st.warning(f"⚠️ Tens {len(itens_velhos)} produtos a ganhar pó há mais de um mês! Hora de baixar o preço?")