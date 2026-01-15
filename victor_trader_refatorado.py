import os
import pandas as pd
import requests
import datetime
import numpy as np
import streamlit as st
import plotly.graph_objects as go
from sklearn.ensemble import RandomForestClassifier

# ==========================
# CONFIGURAÇÕES TÉCNICAS (DIRETAS)
# ==========================
# Substituímos o os.getenv para evitar o ImportError
TOKEN_TELEGRAM = "8238619023:AAEcPr19DnbSpb3Ufoo6sL6ylzTRzdItp80"
CHAT_ID = "5584195780"
TOKEN_BRAPI = "ngaj1shkPqZhAYL6Hcq5wB"

ACOES = ["PETR4", "VALE3", "ITUB4", "KLBN11", "BBAS3", "TAEE11"]
ARQ_CSV = "historico_operacoes.csv"

# ==========================
# MOTOR DE DADOS (BRAPI API)
# ==========================
@st.cache_data(ttl=900) # Cache de 15 min para não estourar o limite do Token
def buscar_dados(ticker, range_days="1y"):
    try:
        url = f"https://brapi.dev/api/quote/{ticker}?range={range_days}&interval=1d&token={TOKEN_BRAPI}"
        r = requests.get(url, timeout=15).json()
        if 'results' not in r or not r['results']:
            return pd.DataFrame()
        
        hist = r['results'][0]['historicalData']
        df = pd.DataFrame(hist)
        df['date'] = pd.to_datetime(df['date'], unit='s')
        df.set_index('date', inplace=True)
        return df[['open','high','low','close','volume']]
    except Exception as e:
        return pd.DataFrame()

# ==========================
# INTELIGÊNCIA ARTIFICIAL
# ==========================
def prever_movimento(df):
    try:
        # Criando indicadores para a IA (Médias Móveis e Retorno)
        df = df.copy()
        df['retorno'] = df['close'].pct_change()
        df['mm7'] = df['close'].rolling(7).mean()
        df['mm21'] = df['close'].rolling(21).mean()
        df['volatilidade'] = df['close'].rolling(10).std()
        df['alvo'] = (df['close'].shift(-1) > df['close']).astype(int)
        dados = df.dropna()
        
        X = dados[['close', 'retorno', 'mm7', 'mm21', 'volatilidade']]
        y = dados['alvo']
        
        modelo = RandomForestClassifier(n_estimators=100, random_state=42)
        modelo.fit(X[:-1], y[:-1]) # Treina com tudo menos o último dia
        
        prob = modelo.predict_proba(X.tail(1))[0]
        pred = modelo.predict(X.tail(1))[0]
        
        return pred, max(prob) * 100
    except:
        return 0, 50.0

# ==========================
# RELATÓRIO E TELEGRAM
# ==========================
def executar_analise_completa():
    texto = f"🚀 **VICTOR TRADER IA v5.1**\n"
    texto += f"📅 {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
    enviou_algo = False

    for acao in ACOES:
        df = buscar_dados(acao)
        if df.empty:
            texto += f"\n❌ **{acao}**: Erro na API (Token?)"
            continue
        
        enviou_algo = True
        pred, prob = prever_movimento(df)
        preco = df['close'].iloc[-1]
        sinal = "🟢 COMPRAR" if pred == 1 else "🔴 VENDER"
        
        texto += f"\n📊 **{acao}** | R$ {preco:.2f}"
        texto += f"\n👉 SINAL: {sinal} ({prob:.1f}%)"
        texto += f"\n🎯 Alvo: {preco*1.03:.2f} | Stop: {preco*0.98:.2f}\n"
        
        # Salva no CSV histórico
        df_hist = pd.DataFrame([[datetime.datetime.now().strftime("%d/%m/%Y %H:%M"), acao, preco, sinal, f"{prob:.1f}%"]],
                                columns=["Data", "Ticker", "Preço", "Sinal", "Confiança"])
        df_hist.to_csv(ARQ_CSV, mode='a', header=not os.path.exists(ARQ_CSV), index=False)

    # Envia para o Telegram com formatação Markdown
    if enviou_algo:
        requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage",
                      data={'chat_id': CHAT_ID, 'text': texto, 'parse_mode': 'Markdown'})
        return True
    return False

# ==========================
# INTERFACE STREAMLIT
# ==========================
st.set_page_config(page_title="Victor Trader Pro", layout="wide", page_icon="📈")

# Barra Lateral de Status
st.sidebar.title("📡 Conexão B3")
for acao in ACOES:
    d_status = buscar_dados(acao, "1d")
    if not d_status.empty:
        st.sidebar.success(f"{acao}: Online (R$ {d_status['close'].iloc[-1]:.2f})")
    else:
        st.sidebar.error(f"{acao}: Offline/Token Limite")

st.title("🚀 Victor Trader IA v5.1")

if st.button("📊 EXECUTAR ANÁLISE E NOTIFICAR TELEGRAM", use_container_width=True):
    with st.spinner("IA processando dados da Brapi..."):
        if executar_analise_completa():
            st.success("Análise enviada para o Telegram!")
        else:
            st.error("Falha ao processar análise. Verifique o Status na barra lateral.")

st.divider()

# Seção de Gráficos
st.subheader("📈 Gráficos Técnicos (Candlestick)")
col1, col2 = st.columns(2)
for i, acao in enumerate(ACOES):
    with col1 if i % 2 == 0 else col2:
        df_g = buscar_dados(acao, "60d")
        if not df_g.empty:
            fig = go.Figure(data=[go.Candlestick(x=df_g.index, open=df_g['open'], high=df_g['high'], low=df_g['low'], close=df_g['close'])])
            fig.update_layout(title=f"Histórico: {acao}", xaxis_rangeslider_visible=False, template="plotly_dark", height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"⚠️ {acao}: Sem dados para exibir gráfico.")

# Seção de Download CSV
if os.path.exists(ARQ_CSV):
    st.divider()
    st.subheader("📁 Histórico de Operações")
    df_csv = pd.read_csv(ARQ_CSV)
    st.dataframe(df_csv.tail(10), use_container_width=True)
    st.download_button("📥 Baixar Planilha Completa (CSV)", df_csv.to_csv(index=False), "historico_victor.csv", "text/csv")
