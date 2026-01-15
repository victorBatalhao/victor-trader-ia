import streamlit as st
import threading
import time
import schedule
from bot_trader import executar_analise_total, ACOES, gerar_grafico_interativo

@st.cache_resource
def iniciar_agendador_unico():
    def rodar_loop():
        schedule.clear()
        dias = ["monday", "tuesday", "wednesday", "thursday", "friday"]
        for dia in dias:
            getattr(schedule.every(), dia).at("17:05").do(executar_analise_total)
        while True:
            schedule.run_pending()
            time.sleep(60)
    t = threading.Thread(target=rodar_loop, daemon=True)
    t.start()
    return "🔥 Agendador 17:05 Ativo"

iniciar_agendador_unico()

st.set_page_config(page_title="Victor Trader IA v3.1", page_icon="📈", layout="centered")

st.title("🚀 Victor Trader IA")
st.subheader("Sistema Quantitativo Profissional")

if st.button("📊 DISPARAR ANÁLISE COMPLETA", use_container_width=True):
    with st.spinner("IA analisando dados e tendências..."):
        try:
            executar_analise_total()
            st.success("✅ Relatório detalhado enviado ao Telegram!")
        except Exception as e:
            st.error(f"Erro técnico: {e}")

st.divider()
st.write("### 📈 Visualização de Tendências")

# Cria abas para cada ação monitorada
tabs = st.tabs(ACOES)
for i, ticker in enumerate(ACOES):
    with tabs[i]:
        st.write(f"Movimentação de **{ticker}** (Últimos 6 meses)")
        try:
            fig = gerar_grafico_interativo(ticker)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Aguardando abertura do mercado para atualizar dados.")
        except:
            st.error("Erro ao carregar gráfico.")

st.divider()
st.caption("v3.1 - IA com Gráficos Interativos e Proteção de Dados.")