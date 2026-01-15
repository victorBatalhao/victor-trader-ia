import streamlit as st
import pandas as pd
import os
import datetime
from bot_trader import executar_analise_total, ACOES, gerar_grafico_historico, NOME_ARQUIVO, buscar_dados_brapi

st.set_page_config(page_title="Victor Trader Pro v4.0", layout="wide", page_icon="📈")

# --- BARRA LATERAL (SIDEBAR) ---
st.sidebar.title("📡 Status do Mercado")
for ticker in ACOES:
    try:
        # Busca o preço mais recente via Brapi para o status
        df_status = buscar_dados_brapi(ticker, "1d")
        if not df_status.empty:
            p = df_status['close'].iloc[-1]
            st.sidebar.success(f"● {ticker}: R$ {p:.2f}")
        else:
            st.sidebar.warning(f"● {ticker}: Offline")
    except:
        st.sidebar.error(f"● {ticker}: Erro")

st.title("🚀 Victor Trader IA - Versão Profissional")

# Botão de Execução Manual
if st.button("📊 REALIZAR ANÁLISE COMPLETA E NOTIFICAR TELEGRAM", use_container_width=True):
    with st.spinner("IA Consultando Brapi API e gerando sinais..."):
        executar_analise_total("SOLICITAÇÃO MANUAL")
        st.success("Análise finalizada! Verifique seu Telegram.")

st.divider()

# --- SEÇÃO DE DOWNLOAD CSV ---
if os.path.exists(NOME_ARQUIVO):
    st.subheader("📁 Histórico de Operações (CSV)")
    df_csv = pd.read_csv(NOME_ARQUIVO)
    st.dataframe(df_csv.tail(6), use_container_width=True)
    st.download_button(label="📥 BAIXAR PLANILHA COMPLETA", data=df_csv.to_csv(index=False), 
                       file_name="historico_victor_trader.csv", mime="text/csv")
else:
    st.info("Execute uma análise para começar a gerar o histórico CSV.")

st.divider()

# --- GRÁFICOS DE TENDÊNCIA ---
st.subheader("📈 Gráficos de Candlestick (Dias Anteriores)")
cols = st.columns(1) 
for ticker in ACOES:
    fig = gerar_grafico_historico(ticker)
    if fig:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error(f"Não foi possível carregar os dados de {ticker}. Verifique o limite do seu token Brapi.")

st.caption(f"Sessão iniciada em: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")