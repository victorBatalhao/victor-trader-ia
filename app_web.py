import streamlit as st
import threading
import time
import schedule
from bot_trader import executar_analise_total, ACOES_TRADE, ACOES_DIVIDENDOS

# --- AGENDAMENTO (Thread) ---
def rodar_agendador():
    # Agendamento fixo de segunda a sexta
    dias = ["monday", "tuesday", "wednesday", "thursday", "friday"]
    for dia in dias:
        getattr(schedule.every(), dia).at("17:05").do(executar_analise_total)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

# Inicia o agendador automático em segundo plano apenas uma vez
if 'bot_ativo' not in st.session_state:
    threading.Thread(target=rodar_agendador, daemon=True).start()
    st.session_state['bot_ativo'] = True

# --- INTERFACE WEB ---
st.set_page_config(page_title="Victor Trader AI", page_icon="📈")

st.title("🚀 Painel Victor Trader")
st.write("Status: **Bot Ativo e Agendado (17:05)**")

st.divider()

if st.button("📊 ANALISAR AGORA E ENVIAR TELEGRAM", use_container_width=True):
    with st.spinner("IA Processando dados..."):
        try:
            executar_analise_total()
            st.success("✅ Relatório enviado com sucesso!")
            st.balloons()
        except Exception as e:
            st.error(f"Erro ao processar: {e}")

st.divider()
st.write("### Ações monitoradas:")
st.write(f"⚔️ **Trade:** {', '.join(ACOES_TRADE)}")
st.write(f"💎 **Dividendos:** {', '.join(ACOES_DIVIDENDOS)}")