import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# OBRIGATÓRIO: Ser o primeiro comando do Streamlit a correr
st.set_page_config(page_title="Resseling Pro", layout="wide")

# --- SISTEMA DE LOGIN ---
def check_password():
    """Retorna True se o utilizador introduziu a password correta."""
    def password_entered():
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("🔐 Acesso Restrito")
        st.text_input("Introduz a Password do Império", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.title("🔐 Acesso Restrito")
        st.text_input("Introduz a Password do Império", type="password", on_change=password_entered, key="password")
        st.error("❌ Password errada. Tenta outra vez ou volta para a China.")
        return False
    else:
        return True

if not check_password():
    st.stop()

# --- INÍCIO DO DASHBOARD (SÓ CORRE SE LOGADO) ---
st.success("Bem-vindo de volta, Boss!")

# 1. Ligar à Google Sheet (ttl=0 para dados sempre frescos)
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(ttl=0)

# Garantir que as colunas existem (caso a folha esteja vazia)
if df.empty or df is None:
    df = pd.DataFrame(columns=["Nome", "Link", "Preco_China", "Portes", "Preco_Venda"])

st.title("💰 Gestão de Stock China")

# --- FORMULÁRIO DE ENTRADA ---
with st.expander("➕ Adicionar Novo Produto", expanded=False):
    with st.form("entrada_dados"):
        nome = st.text_input("Nome do Item")
        link = st.text_input("Link acbuy")
        col1, col2, col3 = st.columns(3)
        p_china = col1.number_input("Preço China (X)", min_value=0.0)
        portes = col2.number_input("Portes (Y)", min_value=0.0)
        venda = col3.number_input("Preço Venda (Z)", min_value=0.0)
        
        if st.form_submit_button("Registar"):
            novo_dado = pd.DataFrame([{"Nome": nome, "Link": link, "Preco_China": p_china, "Portes": portes, "Preco_Venda": venda}])
            df_atualizado = pd.concat([df, novo_dado], ignore_index=True)
            conn.update(data=df_atualizado)
            st.cache_data.clear() # Limpa a memória para forçar a leitura do novo dado
            st.success("Gravado na nuvem!")
            st.rerun()

# --- CÁLCULOS E ESTATÍSTICAS ---
if not df.empty:
    # Contas feitas pelo computador para não te cansares
    df['Custo Total'] = df['Preco_China'] + df['Portes']
    df['Lucro'] = df['Preco_Venda'] - df['Custo Total']
    
    # Métricas de Topo
    m1, m2, m3 = st.columns(3)
    investimento = df['Custo Total'].sum()
    lucro_total = df['Lucro'].sum()
    
    m1.metric("Investimento Total", f"{investimento:.2f}€")
    m2.metric("Lucro Potencial", f"{lucro_total:.2f}€", delta=f"{lucro_total:.2f}€")
    m3.metric("Margem Média", f"{(lucro_total/investimento*100 if investimento > 0 else 0):.1f}%")

    st.write("---")
    st.subheader("📦 Gestão de Inventário")
    st.info("Podes editar os valores ou apagar linhas (clica na linha e faz Delete). Grava no fim!")

    # Editor de dados: permite mudar tudo menos as colunas calculadas
    # Definimos as colunas que queremos ver na tabela de edição
    colunas_para_editar = ["Nome", "Link", "Preco_China", "Portes", "Preco_Venda"]
    
    edited_df = st.data_editor(
        df[colunas_para_editar], 
        num_rows="dynamic", 
        use_container_width=True,
        hide_index=True,
        column_config={
            "Link": st.column_config.LinkColumn("Link Produto"),
            "Preco_China": st.column_config.NumberColumn("China (€)", format="%.2f€"),
            "Portes": st.column_config.NumberColumn("Portes (€)", format="%.2f€"),
            "Preco_Venda": st.column_config.NumberColumn("Venda (€)", format="%.2f€"),
        }
    )

    if st.button("💾 Gravar Alterações na Google Sheet"):
        # Grava apenas o que foi editado (as colunas base)
        conn.update(data=edited_df)
        st.cache_data.clear()
        st.success("Tudo atualizado!")
        st.rerun()

else:
    st.warning("Ainda não tens nada no stock. Começa a faturar!")