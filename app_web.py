import streamlit as st
import threading
import time
import schedule
# Note que agora importamos apenas 'ACOES' em vez de 'ACOES_TRADE/DIVIDENDOS'
from bot_trader import executar_analise_total, ACOES

# --- CONFIGURAÇÃO DE SEGURANÇA PARA O SERVIDOR ---
# O cache_resource garante que o relógio de agendamento não duplique ao atualizar a página
@st.cache_resource
def iniciar_agendador_unico():
    def rodar_loop():
        # Limpa agendamentos anteriores para evitar múltiplas mensagens
        schedule.clear()
        
        # Define o horário de Brasília (17:05) de Segunda a Sexta
        dias = ["monday", "tuesday", "wednesday", "thursday", "friday"]
        for dia in dias:
            getattr(schedule.every(), dia).at("17:05").do(executar_analise_total)
        
        while True:
            schedule.run_pending()
            time.sleep(60) # Verifica o relógio a cada minuto

    # Inicia o relógio em uma Thread separada (segundo plano)
    t = threading.Thread(target=rodar_loop, daemon=True)
    t.start()
    return "🔥 Agendador 17:05 Ativo"

# Ativa o sistema de agendamento automático
status_agendador = iniciar_agendador_unico()

# --- INTERFACE VISUAL DO PAINEL ---
st.set_page_config(
    page_title="Victor Trader IA v3.0", 
    page_icon="📈", 
    layout="centered"
)

# Título e Status
st.title("🚀 Victor Trader IA")
st.subheader("Sistema Quantitativo de Alta Precisão")
st.write(f"Status do Servidor: **{status_agendador}**")

st.divider()

# Botão de Disparo Manual
st.write("### 🕹️ Controle Manual")
st.write("Clique abaixo para gerar um relatório completo agora no Telegram:")

if st.button("📊 DISPARAR ANÁLISE PROFISSIONAL", use_container_width=True):
    with st.spinner("IA analisando Correlação Macro, Alvos e Gerenciamento de Risco..."):
        try:
            executar_analise_total()
            st.balloons()
            st.success("✅ Relatório enviado com sucesso para o Telegram!")
        except Exception as e:
            st.error(f"❌ Erro ao processar análise: {e}")
            st.info("Dica: Verifique se o arquivo bot_trader.py está na mesma pasta e sem erros de sintaxe.")

st.divider()

# Exibição dos Ativos Monitorados
st.write("### 🔍 Ativos Monitorados pela IA")
# Mostra a lista de ações que definimos no bot_trader.py
st.info(", ".join(ACOES))

# Rodapé informativo
st.caption("v3.0 - IA com Gerenciamento de Risco (Stop/Alvo) e Balanço Mensal.")