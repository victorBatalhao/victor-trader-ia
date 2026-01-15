import streamlit as st
import pandas as pd
import os
from bot_trader import executar_analise_total, ACOES, gerar_grafico_historico, NOME_ARQUIVO

st.set_page_config(page_title="Victor Trader Pro", layout="wide")

st.title("🚀 Victor Trader IA (Powered by Brapi)")

if st.button("📊 ANALISAR AGORA E ENVIAR TELEGRAM", use_container_width=True):
    with st.spinner("IA Consultando Brapi..."):
        executar_analise_total("MANUAL")
        st.success("Enviado ao Telegram!")

st.divider()

# Botão de Download CSV
if os.path.exists(NOME_ARQUIVO):
    st.subheader("📁 Download do Histórico")
    df_csv = pd.read_csv(NOME_ARQUIVO)
    st.download_button("📥 BAIXAR PLANILHA CSV", df_csv.to_csv(index=False), "historico_victor.csv", "text/csv")

st.divider()

# Gráficos
st.subheader("📈 Gráficos de Dias Anteriores")
for ticker in ACOES:
    fig = gerar_grafico_historico(ticker)
    if fig: st.plotly_chart(fig, use_container_width=True)
    else: st.error(f"Erro ao carregar dados de {ticker} via Brapi")