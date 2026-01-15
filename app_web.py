import streamlit as st
import pandas as pd
import os
import datetime
import yfinance as yf
from bot_trader import executar_analise_total, ACOES, gerar_grafico_interativo, NOME_ARQUIVO

# Configuração da Página
st.set_page_config(page_title="Victor Trader Pro", layout="wide", page_icon="📈")

# Sidebar com Monitor de Preços em tempo real
st.sidebar.title("📡 Status da Conexão")
for ticker in ACOES:
    try:
        # Busca o último preço disponível agora
        price = yf.Ticker(ticker).fast_info['last_price']
        st.sidebar.success(f"● {ticker}: R$ {price:.2f}")
    except:
        st.sidebar.error(f"○ {ticker}: Sem dados")

# Título e Ação
st.title("🚀 Victor Trader IA v3.2.4")
st.subheader("Painel de Controle e Inteligência Quantitativa")

if st.button("📊 DISPARAR ANÁLISE COMPLETA AGORA", use_container_width=True):
    with st.spinner("IA treinando modelos e validando sinais..."):
        executar_analise_total()
        st.success("Análise concluída! Verifique o Log de Integridade no Telegram.")
        st.rerun()

st.divider()

# Histórico de Performance e Download
st.subheader("📁 Histórico e Backup de Dados")
if os.path.isfile(NOME_ARQUIVO):
    df_hist = pd.read_csv(NOME_ARQUIVO)
    st.write("Últimos registros salvos:")
    st.dataframe(df_hist.tail(8), use_container_width=True)
    
    # Botão de Download do CSV
    csv = df_hist.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 BAIXAR PLANILHA COMPLETA (Backup)",
        data=csv,
        file_name=f"backup_ia_trader_{datetime.date.today()}.csv",
        mime="text/csv",
        use_container_width=True
    )
else:
    st.info("Aguardando a primeira análise de mercado para gerar a base de dados.")

st.divider()

# Visualização de Gráficos (MA10 e Preço)
st.subheader("📈 Análise Visual de Tendências")
cols = st.columns(2)
for i, ticker in enumerate(ACOES):
    with cols[i % 2]:
        fig = gerar_grafico_interativo(ticker)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"Dados gráficos de {ticker} temporariamente indisponíveis.")

st.divider()
st.caption(f"Victor Trader IA | Versão 3.2.4 Estável | Data: {datetime.date.today()}")