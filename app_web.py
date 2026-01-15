import streamlit as st
import pandas as pd
import os
from bot_trader import executar_analise_total, ACOES, gerar_grafico_historico, NOME_ARQUIVO, buscar_dados_brapi

st.set_page_config(page_title="Victor Trader Pro", layout="wide")

# --- SIDEBAR COM CACHE ---
st.sidebar.title("📡 Status do Mercado")
for ticker in ACOES:
    df_status = buscar_dados_brapi(ticker, "1d")
    if not df_status.empty:
        p = df_status['close'].iloc[-1]
        st.sidebar.success(f"● {ticker}: R$ {p:.2f}")
    else:
        st.sidebar.error(f"● {ticker}: Offline/Limites") #

st.title("🚀 Victor Trader IA v4.1")

if st.button("📊 ANALISAR AGORA E ENVIAR TELEGRAM", use_container_width=True):
    executar_analise_total("MANUAL")
    st.success("Comando enviado!")

st.divider()

if os.path.exists(NOME_ARQUIVO):
    st.subheader("📁 Download do Histórico")
    df_csv = pd.read_csv(NOME_ARQUIVO)
    st.download_button("📥 BAIXAR PLANILHA CSV", df_csv.to_csv(index=False), "historico.csv", "text/csv")

st.divider()

st.subheader("📈 Gráficos de Candlestick")
for ticker in ACOES:
    fig = gerar_grafico_historico(ticker)
    if fig:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error(f"⚠️ {ticker}: Erro de carregamento (Verifique o limite do Token Brapi).") #