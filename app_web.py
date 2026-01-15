import streamlit as st
import yfinance as yf
from bot_trader import executar_analise_total, ACOES, gerar_grafico_historico

st.set_page_config(page_title="Victor Trader Web", layout="wide")

# Lateral: Status detalhado da Conexão
st.sidebar.title("📡 Status das Ações")
for ticker in ACOES:
    try:
        data = yf.download(ticker, period="1d", progress=False)
        if data.empty:
            st.sidebar.error(f"⚠️ {ticker}: Erro de Dados")
        else:
            preco = data['Close'].iloc[-1]
            st.sidebar.success(f"● {ticker}: OK (R$ {preco:.2f})")
    except:
        st.sidebar.error(f"❌ {ticker}: Falha na API")

st.title("🚀 Victor Trader IA v3.2.6")

if st.button("📊 EXECUTAR ANÁLISE E ENVIAR AO TELEGRAM", use_container_width=True):
    with st.spinner("IA calculando sinais de compra e venda..."):
        executar_analise_total()
        st.success("Sinais enviados para o Telegram com sucesso!")

st.divider()

# Exibição de Gráficos Históricos
st.subheader("📈 Análise Histórica (Datas, Valores e Variações)")
for ticker in ACOES:
    fig = gerar_grafico_historico(ticker)
    if fig:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error(f"❌ Erro ao carregar histórico de {ticker}. Verifique a conexão com o Yahoo Finance.")

st.caption("Sistema Quantitativo Profissional | Dados atualizados via API")