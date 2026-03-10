import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Resseling Pro", layout="wide")

# 1. Ligar à Google Sheet
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(ttl=0)

# Garantir que as colunas existem (caso a folha esteja vazia)
if df.empty:
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
            df = pd.concat([df, novo_dado], ignore_index=True)
            conn.update(data=df)
            st.success("Gravado!")
            st.rerun()

# --- CÁLCULOS E ESTATÍSTICAS ---
if not df.empty:
    # Contas de cabeça (feitas pelo computador)
    df['Custo Total'] = df['Preco_China'] + df['Portes']
    df['Lucro'] = df['Preco_Venda'] - df['Custo Total']
    
    # 2. Métricas de Topo
    m1, m2, m3 = st.columns(3)
    investimento = df['Custo Total'].sum()
    lucro_total = df['Lucro'].sum()
    
    m1.metric("Investimento Total", f"{investimento:.2f}€")
    m2.metric("Lucro Potencial", f"{lucro_total:.2f}€", delta=f"{lucro_total:.2f}€")
    m3.metric("Margem Média", f"{(lucro_total/investimento*100 if investimento > 0 else 0):.1f}%")

    st.write("---")
    st.subheader("📦 Gestão de Inventário")
    st.info("Podes editar os valores diretamente na tabela ou apagar linhas. Não te esqueças de clicar em 'Gravar Alterações'!")

    # 3. Cores e Edição (Verde/Vermelho)
    def style_lucro(v):
        color = 'red' if v < 0 else 'green' if v > 0 else 'white'
        return f'color: {color}; font-weight: bold'

    # Editor de dados (permite apagar e editar)
    edited_df = st.data_editor(
        df, 
        num_rows="dynamic", # Isto permite-te apagar linhas!
        use_container_width=True,
        hide_index=True,
        column_config={
            "Link": st.column_config.LinkColumn("Link Produto"),
            "Lucro": st.column_config.NumberColumn("Lucro (€)", format="%.2f€")
        }
    )

    if st.button("💾 Gravar Alterações na Google Sheet"):
        # Limpar colunas calculadas antes de gravar para não sujar a Google Sheet
        to_save = edited_df.drop(columns=['Custo Total', 'Lucro'])
        conn.update(data=to_save)
        st.cache_data.clear() # Isto limpa a memória "à bruta"
        st.success("Gravado na nuvem!")
        st.rerun()

else:
    st.warning("Ainda não tens nada no stock.")