import streamlit as st
import pandas as pd
import os
import datetime
import yfinance as yf
from bot_trader import executar_analise_total, ACOES, gerar_grafico_interativo, NOME_ARQUIVO

st.set_page_config(page_title="Victor Trader Pro", layout="wide", page_icon="📈")

# Barra Lateral com Preços em Tempo Real
st.sidebar.title("📡 Mercado em Tempo Real")
for ticker in ACOES:
    try:
        # Pega o preço de agora
        tkt = yf.Ticker(ticker)
        preco = tkt.history(period="1d")['Close'].iloc[-1]
        st.sidebar.success(f"{ticker}: R$ {preco:.2f}")
    except:
        st.sidebar.error(f"{ticker}: Offline (Aguardando)")

# Painel Principal
st.title("🚀 Victor Trader IA v3.2")
st.subheader("Sistema Quantitativo de Alta Precisão")

col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    if st.button("📊 DISPARAR ANÁLISE COMPLETA", use_container_width=True):
        with st.spinner("IA treinando modelos e verificando sinais..."):
            executar_analise_total()
            st.success("Relatório enviado ao Telegram!")
            st.rerun()

with col_btn2:
    if st.button("🔄 RECARREGAR PAINEL", use_container_width=True):
        st.rerun()

st.divider()

# Histórico de Performance (Tabela que você queria ver)
st.subheader("📁 Histórico de Performance (CSV)")
if os.path.isfile(NOME_ARQUIVO):
    df_hist = pd.read_csv(NOME_ARQUIVO)
    st.dataframe(df_hist.tail(10), use_container_width=True)
    
    st.download_button(
        label="📥 BAIXAR BASE DE DADOS COMPLETA",
        data=df_hist.to_csv(index=False).encode('utf-8'),
        file_name=f"victor_trader_backup_{datetime.date.today()}.csv",
        mime="text/csv",
        use_container_width=True
    )
else:
    st.warning("Nenhum dado salvo. Execute uma análise para gerar o histórico.")

st.divider()

# Gráficos Interativos
st.subheader("📈 Visualização de Tendências")
cols = st.columns(2)
for i, ticker in enumerate(ACOES):
    with cols[i % 2]:
        fig = gerar_grafico_interativo(ticker)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"Aguardando dados de mercado para {ticker}...")

st.caption(f"Victor Trader IA | Versão Estável 3.2.3 | Atualizado em: {datetime.datetime.now().strftime('%H:%M:%S')}")