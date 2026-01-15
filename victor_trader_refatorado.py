import os
import pandas as pd
import requests
import datetime
import numpy as np
import streamlit as st
import plotly.graph_objects as go
from sklearn.ensemble import RandomForestClassifier

# ==========================================
# 1. CONFIGURAÇÕES TÉCNICAS E TOKENS
# ==========================================
# Tokens diretos para evitar erro de inicialização
TOKEN_TELEGRAM = "8238619023:AAEcPr19DnbSpb3Ufoo6sL6ylzTRzdItp80"
CHAT_ID = "5584195780"
TOKEN_BRAPI = "ngaj1shkPqZhAYL6Hcq5wB"

ACOES = ["PETR4", "VALE3", "ITUB4", "KLBN11", "BBAS3", "TAEE11"]
ARQ_CSV = "historico_victor_ia.csv"

# ==========================================
# 2. MOTOR DE DADOS (BRAPI)
# ==========================================
@st.cache_data(ttl=900) # Cache para economizar requisições
def buscar_dados_completos(ticker):
    try:
        url = f"https://brapi.dev/api/quote/{ticker}?range=1y&interval=1d&token={TOKEN_BRAPI}"
        r = requests.get(url, timeout=15).json()
        if 'results' not in r: return pd.DataFrame()
        df = pd.DataFrame(r['results'][0]['historicalData'])
        df['date'] = pd.to_datetime(df['date'], unit='s')
        df.set_index('date', inplace=True)
        return df[['open','high','low','close','volume']]
    except:
        return pd.DataFrame()

# ==========================================
# 3. INTELIGÊNCIA ARTIFICIAL (TRADE VS DIVIDENDOS)
# ==========================================
def motor_ia_avancado(df):
    try:
        df = df.copy()
        # Engenharia de Features: Médias, Volatilidade e Retornos
        df['retorno'] = df['close'].pct_change()
        df['vol_20d'] = df['retorno'].rolling(20).std()
        df['mm7'] = df['close'].rolling(7).mean()
        df['mm21'] = df['close'].rolling(21).mean()
        df['alvo'] = (df['close'].shift(-1) > df['close']).astype(int)
        
        dados = df.dropna()
        X = dados[['close', 'retorno', 'vol_20d', 'mm7', 'mm21']]
        y = dados['alvo']
        
        # Modelo de Floresta Aleatória para previsão de tendência
        modelo = RandomForestClassifier(n_estimators=200, random_state=42)
        modelo.fit(X[:-1], y[:-1])
        
        prob = modelo.predict_proba(X.tail(1))[0]
        pred = modelo.predict(X.tail(1))[0]
        vol_atual = df['vol_20d'].iloc[-1]
        
        # Lógica de Gestão: Dividendos (estabilidade) vs Trade (oscilação)
        perfil = "💰 DIVIDENDOS (Conservador)" if vol_atual < 0.018 else "⚔️ TRADE (Agressivo)"
        return pred, max(prob)*100, perfil, vol_atual
    except:
        return 0, 50.0, "Indefinido", 0.0

# ==========================================
# 4. SISTEMA DE RELATÓRIOS (TELEGRAM & CSV)
# ==========================================
def executar_analise_e_notificar():
    relatorio = f"🚀 **VICTOR TRADER IA v5.1 - RELATÓRIO MESTRE**\n"
    relatorio += f"📅 {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
    sucesso_geral = False

    for acao in ACOES:
        df = buscar_dados_completos(acao)
        if not df.empty and len(df) > 30:
            sucesso_geral = True
            pred, conf, perfil, vol = motor_ia_avancado(df)
            preco = df['close'].iloc[-1]
            sinal = "🟢 COMPRA FORTE" if pred == 1 and conf > 60 else "🔴 VENDA/AGUARDAR"
            status = "🚀 Valorização" if pred == 1 else "⚠️ Depreciação"

            relatorio += f"\n📊 **{acao}** | R$ {preco:.2f}\n"
            relatorio += f"👉 **{sinal}** ({conf:.1f}%)\n"
            relatorio += f"🎯 Estratégia: {perfil}\n"
            relatorio += f"📈 Tendência: {status}\n"

            # Registro em CSV para auditoria futura
            registro = pd.DataFrame([[datetime.datetime.now(), acao, preco, sinal, perfil, conf]], 
                                     columns=["Data", "Ativo", "Preco", "Sinal", "Perfil", "Confianca"])
            registro.to_csv(ARQ_CSV, mode='a', header=not os.path.exists(ARQ_CSV), index=False)

    if sucesso_geral:
        requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage", 
                      data={'chat_id': CHAT_ID, 'text': relatorio, 'parse_mode': 'Markdown'})
        return True
    return False

# ==========================================
# 5. INTERFACE DO USUÁRIO (STREAMLIT)
# ==========================================
st.set_page_config(page_title="Victor Trader Pro IA", layout="wide", page_icon="📈")

# Barra Lateral de Status
st.sidebar.title("📡 Conexão B3")
for acao in ACOES:
    d_check = buscar_dados_completos(acao)
    if not d_check.empty:
        st.sidebar.success(f"{acao}: Online")
    else:
        st.sidebar.error(f"{acao}: Erro de Token") # Alerta de limite da Brapi

st.title("🚀 Victor Trader IA – Inteligência de Mercado")
st.info("Esta IA analisa volatilidade para separar oportunidades de Trade e Dividendos automaticamente.")

if st.button("📡 EXECUTAR ANÁLISE COMPLETA E NOTIFICAR TELEGRAM", use_container_width=True):
    with st.spinner("IA Processando dados históricos e tendências..."):
        if executar_analise_e_notificar():
            st.success("Relatório Mestre enviado ao Telegram!")
        else:
            st.error("Falha ao coletar dados. Verifique seu token no painel Brapi.")

st.divider()

# Histórico e Download
if os.path.exists(ARQ_CSV):
    st.subheader("📥 Banco de Dados de Operações")
    df_hist = pd.read_csv(ARQ_CSV)
    st.dataframe(df_hist.tail(10), use_container_width=True)
    st.download_button("Baixar Relatório em Excel/CSV", df_hist.to_csv(index=False), "historico_ia.csv", "text/csv")

st.divider()

# Interface de Visualização Gráfica
st.subheader("📈 Gráficos de Tendência (Candlestick)")
col_a, col_b = st.columns(2)
for i, acao in enumerate(ACOES):
    with col_a if i % 2 == 0 else col_b:
        df_g = buscar_dados_completos(acao)
        if not df_g.empty:
            fig = go.Figure(data=[go.Candlestick(x=df_g.index[-60:], open=df_g['open'], 
                            high=df_g['high'], low=df_g['low'], close=df_g['close'])])
            fig.update_layout(title=f"Ativo: {acao}", xaxis_rangeslider_visible=False, template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
