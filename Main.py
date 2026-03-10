import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA (Sempre o primeiro comando)
st.set_page_config(page_title="Resseling Pro", layout="wide", page_icon="💰")

# --- 2. SISTEMA DE LOGIN (Porteiro) ---
def check_password():
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
        st.error("❌ Password errada. Tenta outra vez.")
        return False
    return True

if not check_password():
    st.stop()

# --- 3. LIGAÇÃO AOS DADOS (Google Sheets) ---
conn = st.connection("gsheets", type=GSheetsConnection)
df_raw = conn.read(ttl=0)

# Colunas que o teu império exige
colunas_base = ["Nome", "Link", "Preco_China", "Portes", "Preco_Venda", "Data_Registo", "Estado"]

if df_raw.empty or df_raw is None:
    df = pd.DataFrame(columns=colunas_base)
else:
    df = df_raw.copy()

# --- 4. TRATAMENTO DE DADOS (O Filtro de Segurança) ---
# Garante que as colunas existem
for col in colunas_base:
    if col not in df.columns:
        df[col] = None

# Limpeza de buracos (Nones e NaNs)
df['Estado'] = df['Estado'].fillna("Em Stock").astype(str)
df['Data_Registo'] = df['Data_Registo'].fillna(str(datetime.now().date()))
df['Preco_China'] = pd.to_numeric(df['Preco_China'], errors='coerce').fillna(0)
df['Portes'] = pd.to_numeric(df['Portes'], errors='coerce').fillna(0)
df['Preco_Venda'] = pd.to_numeric(df['Preco_Venda'], errors='coerce').fillna(0)

# Cálculos Automáticos
df['Custo_Total'] = df['Preco_China'] + df['Portes']
df['Lucro'] = df['Preco_Venda'] - df['Custo_Total']
df['Data_Registo_DT'] = pd.to_datetime(df['Data_Registo'], errors='coerce').fillna(datetime.now())
df['Dias_Stock'] = (datetime.now() - df['Data_Registo_DT']).dt.days

# --- 5. BARRA LATERAL (Navegação) ---
st.sidebar.title("🎮 Painel de Controlo")
aba = st.sidebar.radio("Ir para:", ["📦 Inventário & Vendas", "📊 Estatísticas de Lucro"])

# --- ABA 1: INVENTÁRIO & VENDAS ---
if aba == "📦 Inventário & Vendas":
    st.title("🚀 Gestão de Stock China")
    
    # Métricas Rápidas
    mask_vendido = df['Estado'].str.contains('Vendido', case=False, na=False)
    stock_ativo = df[~mask_vendido]
    vendidos = df[mask_vendido]

    m1, m2, m3 = st.columns(3)
    m1.metric("Investimento Ativo", f"{stock_ativo['Custo_Total'].sum():.2f}€")
    m2.metric("Lucro REAL (No Bolso)", f"{vendidos['Lucro'].sum():.2f}€", delta=f"{vendidos['Lucro'].sum():.2f}€")
    m3.metric("Lucro a Caminho", f"{stock_ativo['Lucro'].sum():.2f}€")

    # Formulário para Adicionar
    with st.expander("➕ Adicionar Novo Item"):
        with st.form("novo_item_form"):
            c1, c2 = st.columns(2)
            nome = c1.text_input("Nome do Item")
            link = c1.text_input("Link acbuy")
            est = c2.selectbox("Estado", ["Encomendado", "Em Trânsito", "Em Stock"])
            pc = c2.number_input("Preço China", min_value=0.0)
            po = st.number_input("Portes (Y)", min_value=0.0)
            pv = st.number_input("Preço Venda (Z)", min_value=0.0)
            
            if st.form_submit_button("Registar"):
                novo = pd.DataFrame([{"Nome": nome, "Link": link, "Preco_China": pc, "Portes": po, 
                                      "Preco_Venda": pv, "Data_Registo": str(datetime.now().date()), "Estado": est}])
                df_to_save = pd.concat([df[colunas_base], novo], ignore_index=True)
                conn.update(data=df_to_save)
                st.cache_data.clear()
                st.success("Item lançado! O lucro espera por ti.")
                st.rerun()

    st.write("---")
    
    # Tabela de Edição
    st.subheader("📝 Editar Inventário")
    st.caption("Dica: Muda o estado para 'Vendido' e grava para o lucro subir!")
    
    edited_df = st.data_editor(
        df[colunas_base + ["Dias_Stock", "Lucro"]],
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        column_config={
            "Estado": st.column_config.SelectboxColumn("Estado", options=["Encomendado", "Em Trânsito", "Em Stock", "Vendido"]),
            "Link": st.column_config.LinkColumn("Link"),
            "Dias_Stock": st.column_config.NumberColumn("Dias", disabled=True),
            "Lucro": st.column_config.NumberColumn("Lucro Est.", format="%.2f€", disabled=True)
        }
    )

    if st.button("💾 Guardar Todas as Alterações"):
        conn.update(data=edited_df[colunas_base])
        st.cache_data.clear()
        st.success("Base de dados atualizada!")
        st.rerun()

    # Alerta de Stock Velho (Ideia 4)
    velhos = stock_ativo[stock_ativo['Dias_Stock'] > 30]
    if not velhos.empty:
        st.warning(f"⚠️ Atenção! Tens {len(velhos)} itens parados há mais de 30 dias. Estás a perder dinheiro!")

# --- ABA 2: ESTATÍSTICAS ---
elif aba == "📊 Estatísticas de Lucro":
    st.title("📊 Raio-X do Negócio")
    
    if df.empty:
        st.info("Ainda não há dados para analisar. Vai comprar umas sapatilhas!")
    else:
        c1, c2 = st.columns(2)
        
        # Gráfico de Pizza: Onde está o dinheiro?
        with c1:
            st.subheader("Distribuição de Stock")
            estado_counts = df['Estado'].value_counts()
            st.write("Itens por Estado:")
            st.table(estado_counts)
        
        # Gráfico Simples de Performance
        with c2:
            st.subheader("Performance Financeira")
            total_investido = df['Custo_Total'].sum()
            total_venda = df['Preco_Venda'].sum()
            st.bar_chart({"Gastos": total_investido, "Vendas": total_venda})

    st.info("💡 No futuro, aqui poderemos ver o lucro por mês assim que tiveres mais dados!")