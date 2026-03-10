import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Resseling Pro", layout="wide")

# Ligar à Google Sheet (Base de Dados Grátis)
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read()

st.title("💰 Gestão de Stock China")

with st.form("entrada_dados"):
    nome = st.text_input("Nome do Item")
    link = st.text_input("Link acbuy")
    col1, col2, col3 = st.columns(3)
    p_china = col1.number_input("Preço China (X)", min_value=0.0)
    portes = col2.number_input("Portes (Y)", min_value=0.0)
    venda = col3.number_input("Preço Venda (Z)", min_value=0.0)

    if st.form_submit_button("Registar Produto"):
        # Adiciona à folha Google
        novo_dado = pd.DataFrame(
            [{"Nome": nome, "Link": link, "Preco_China": p_china, "Portes": portes, "Preco_Venda": venda}])
        df = pd.concat([df, novo_dado], ignore_index=True)
        conn.update(data=df)
        st.success("Gravado na nuvem!")

# Mostrar as contas que interessam
if not df.empty:
    df['Lucro'] = df['Preco_Venda'] - (df['Preco_China'] + df['Portes'])
    st.dataframe(df)