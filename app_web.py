import streamlit as st
import datetime
import yfinance as yf
# Importação direta garantida para evitar o ImportError
from bot_trader import executar_analise_total, ACOES, gerar_grafico_historico

st.set_page_config(page_title="Victor Trader Pro", layout="wide", page_icon="📈")

# --- LÓGICA DE ALERTA AUTOMÁTICO PÓS-FECHAMENTO ---
if 'alerta_enviado' not in st.session_state:
    st.session_state.alerta_enviado = False

agora = datetime.datetime.now()
# Dispara alerta automático após o fechamento (ex: 18:05)
if agora.hour == 18 and agora.minute >= 5 and not st.session_state.alerta_enviado:
    executar_analise_total(tipo_alerta="FECHAMENTO AUTOMÁTICO")
    st.session_state.alerta_enviado = True

# --- INTERFACE WEB ---
st.title("🚀 Victor Trader IA - v3.5.0")
st.subheader("Análise Quantitativa com Alertas em Tempo Real")

# Barra Lateral: Status das informações
st.sidebar.title("📡 Verificação de Dados")
for ticker in ACOES:
    try:
        # Verifica se há dados de hoje ou do último fechamento
        data = yf.download(ticker, period="1d", progress=False)
        if data.empty:
            st.sidebar.error(f"⚠️ {ticker}: FALTANDO INFORMAÇÃO")
        else:
            p = data['Close'].iloc[-1]
            st.sidebar.success(f"● {ticker}: OK (R$ {p:.2f})")
    except:
        st.sidebar.error(f"❌ {ticker}: ERRO DE CONEXÃO")

# Botão de Análise Manual sob demanda
if st.button("📊 REALIZAR ANÁLISE EM TEMPO REAL AGORA", use_container_width=True):
    with st.spinner("IA processando previsões e enviando sinais..."):
        executar_analise_total(tipo_alerta="SOLICITAÇÃO MANUAL")
        st.success("Sinais de Compra/Venda enviados ao Telegram!")

st.divider()

# Exibição dos Gráficos Históricos (Dias Anteriores)
st.subheader("📈 Histórico Visual (Candlestick - Valores e Datas)")
st.info("Os gráficos abaixo utilizam dados consolidados de dias anteriores e do fechamento mais recente.")

for ticker in ACOES:
    with st.container():
        fig = gerar_grafico_historico(ticker)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"Não foi possível carregar o histórico de {ticker}. Verifique sua conexão.")

st.divider()
st.caption(f"Victor Trader IA | Sessão Atual: {agora.strftime('%d/%m/%Y %H:%M:%S')}")