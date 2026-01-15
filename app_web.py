import streamlit as st
import threading
import time
import schedule
import yfinance as yf
from bot_trader import executar_analise_total, ACOES, gerar_grafico_interativo

# Configuração de Página
st.set_page_config(page_title="Victor Trader v3.2", page_icon="📈", layout="wide")

# --- MONITOR DE DADOS (SIDEBAR) ---
st.sidebar.title("📡 Status da Conexão")
st.sidebar.write("Verificando Yahoo Finance...")

for ticker in ACOES:
    try:
        # Tenta carregar apenas o último preço para validar a conexão
        check = yf.Ticker(ticker).fast_info['last_price']
        if check:
            st.sidebar.success(f"● {ticker}: OK")
        else:
            st.sidebar.error(f"○ {ticker}: Sem dados")
    except:
        st.sidebar.warning(f"○ {ticker}: Erro/Timeout")

# --- AGENDADOR ---
@st.cache_resource
def iniciar_agendador():
    def rodar():
        schedule.clear()
        schedule.every().day.at("17:05").do(executar_analise_total)
        while True:
            schedule.run_pending()
            time.sleep(60)
    threading.Thread(target=rodar, daemon=True).start()
    return "Relógio 17:05 Ativo"

st.sidebar.divider()
st.sidebar.info(iniciar_agendador())

# --- CORPO DO SITE ---
st.title("🚀 Victor Trader IA")
st.subheader("Painel de Controle Quantitativo")

if st.button("📊 DISPARAR ANÁLISE COMPLETA AGORA", use_container_width=True):
    with st.spinner("IA processando e verificando integridade dos ativos..."):
        executar_analise_total()
        st.success("Relatório gerado! Verifique o Log de Integridade no seu Telegram.")
        st.balloons()

st.divider()

# --- GRÁFICOS EM DUAS COLUNAS ---
st.subheader("📈 Análise Visual de Tendências")
cols = st.columns(2)

for i, ticker in enumerate(ACOES):
    col_idx = i % 2
    with cols[col_idx]:
        fig = gerar_grafico_interativo(ticker)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"Dados gráficos de {ticker} temporariamente indisponíveis.")

st.divider()
st.caption("Victor Trader IA v3.2 - Sistema de Análise Modular e Gerenciamento de Dados.")