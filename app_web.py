import streamlit as st
import threading
import time
import schedule
from bot_trader import executar_analise_total, ACOES_TRADE, ACOES_DIVIDENDOS

# --- CONFIGURAÇÃO DE SEGURANÇA PARA EVITAR DUPLICIDADE ---
# Usamos uma função decorada com @st.cache_resource para garantir que a Thread rode APENAS UMA VEZ
@st.cache_resource
def iniciar_agendador_unico():
    def rodar_loop():
        # Limpa qualquer agendamento residual antes de começar
        schedule.clear()
        
        # Agendamento de segunda a sexta às 17:05
        dias = ["monday", "tuesday", "wednesday", "thursday", "friday"]
        for dia in dias:
            getattr(schedule.every(), dia).at("17:05").do(executar_analise_total)
        
        while True:
            schedule.run_pending()
            time.sleep(60)

    t = threading.Thread(target=rodar_loop, daemon=True)
    t.start()
    return "Agendador iniciado"

# Chama a função (o Streamlit garante que ela só execute uma vez, mesmo atualizando a página)
iniciar_agendador_unico()

# --- INTERFACE WEB ---
st.set_page_config(page_title="Victor Trader AI", page_icon="📈")

st.title("🚀 Painel Victor Trader")
st.write("Status: **Monitoramento Ativo (17:05)**")

st.divider()

if st.button("📊 ANALISAR AGORA (MANUAL)", use_container_width=True):
    with st.spinner("IA Processando dados..."):
        try:
            executar_analise_total()
            st.success("✅ Relatório enviado com sucesso!")
        except Exception as e:
            st.error(f"Erro ao processar: {e}")

st.divider()
st.write("### Ativos na Carteira:")
st.write(f"⚔️ **Trade:** {', '.join(ACOES_TRADE)}")
st.write(f"💎 **Dividendos:** {', '.join(ACOES_DIVIDENDOS)}")