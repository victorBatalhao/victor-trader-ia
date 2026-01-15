import streamlit as st
import threading
import time
import schedule
import yfinance as yf
import pandas as pd
import os
import datetime
from bot_trader import executar_analise_total, ACOES, gerar_grafico_interativo, NOME_ARQUIVO

# 1. Configuração de Layout (Ocupa a tela inteira para facilitar no celular)
st.set_page_config(page_title="Victor Trader v3.2", page_icon="📈", layout="wide")

# 2. Monitor de Conexão na Barra Lateral
st.sidebar.title("📡 Status da Conexão")
st.sidebar.write("Verificando mercado em tempo real...")

for ticker in ACOES:
    try:
        # Tenta pegar apenas o último preço para validar se o Yahoo Finance está respondendo
        info = yf.Ticker(ticker).fast_info
        if 'last_price' in info:
            st.sidebar.success(f"● {ticker}: OK")
        else:
            st.sidebar.error(f"○ {ticker}: Sem dados")
    except:
        st.sidebar.warning(f"○ {ticker}: Erro de Conexão")

# 3. Agendador do Robô (Roda às 17:05 automaticamente)
@st.cache_resource
def iniciar_agendador_unico():
    def rodar_loop():
        schedule.clear()
        # Agenda de segunda a sexta
        dias = ["monday", "tuesday", "wednesday", "thursday", "friday"]
        for dia in dias:
            getattr(schedule.every(), dia).at("17:05").do(executar_analise_total)
        while True:
            schedule.run_pending()
            time.sleep(60)
            
    t = threading.Thread(target=rodar_loop, daemon=True)
    t.start()
    return "🔥 Relógio de IA Ativo (17:05)"

# Exibe o status do agendador na barra lateral
status_agendador = iniciar_agendador_unico()
st.sidebar.divider()
st.sidebar.info(status_agendador)

# 4. Título Principal e Botão de Ação
st.title("🚀 Victor Trader IA")
st.subheader("Sistema de Inteligência Quantitativa e Risco")

if st.button("📊 DISPARAR ANÁLISE COMPLETA AGORA", use_container_width=True):
    with st.spinner("IA processando indicadores e tendências..."):
        try:
            executar_analise_total()
            st.success("✅ Relatório enviado ao Telegram com sucesso!")
            st.balloons()
        except Exception as e:
            st.error(f"Erro ao processar: {e}")

st.divider()

# 5. Gestão de Dados e Download do CSV
st.subheader("📁 Histórico de Performance (Base de Dados)")

if os.path.isfile(NOME_ARQUIVO):
    # Carrega o CSV que o robô cria
    df_hist = pd.read_csv(NOME_ARQUIVO)
    
    # Exibe a tabela com as últimas 5 operações (KLBN11, TAEE11, etc)
    st.write("Últimos registros salvos no servidor:")
    st.dataframe(df_hist.tail(10), use_container_width=True)
    
    # Cria o botão para você baixar o arquivo e ter o controle total
    csv_bytes = df_hist.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 BAIXAR HISTÓRICO COMPLETO EM EXCEL/CSV",
        data=csv_bytes,
        file_name=f"relatorio_ia_victor_{datetime.date.today()}.csv",
        mime="text/csv",
        use_container_width=True
    )
else:
    st.info("Nenhum dado registrado ainda. O histórico aparecerá aqui após a primeira análise lucrativa.")

st.divider()

# 6. Exibição de Gráficos Interativos
st.subheader("📈 Análise Visual de Ativos")
cols = st.columns(2)

for i, ticker in enumerate(ACOES):
    # Alterna entre a coluna 1 e 2
    with cols[i % 2]:
        fig = gerar_grafico_interativo(ticker)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"Aguardando abertura do mercado para atualizar {ticker}")

st.divider()
st.caption(f"Victor Trader IA v3.2.1 | Data do Servidor: {datetime.date.today()}")