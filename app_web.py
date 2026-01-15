# Victor Trader IA v5.0 – Arquitetura Unificada e Refatorada
# Autor: Victor
# Objetivo: Sistema automático de análise de ações + relatórios + gráficos + CSV + Telegram

import os
import pandas as pd
import requests
import datetime
import numpy as np
import streamlit as st
import plotly.graph_objects as go
from sklearn.ensemble import RandomForestClassifier

# ==========================
# CONFIGURAÇÕES (USE ENV VARS)
# ==========================
TOKEN_TELEGRAM = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TOKEN_BRAPI = os.getenv("BRAPI_TOKEN")

ACOES = ["PETR4", "VALE3", "ITUB4", "KLBN11", "BBAS3", "TAEE11"]
ARQ_CSV = "historico_operacoes.csv"

# ==========================
# DADOS DE MERCADO
# ==========================
@st.cache_data(ttl=300)
def buscar_dados(ticker, range_days="1y"):
    try:
        url = f"https://brapi.dev/api/quote/{ticker}?range={range_days}&interval=1d&token={TOKEN_BRAPI}"
        r = requests.get(url, timeout=10).json()
        hist = r['results'][0]['historicalData']
        df = pd.DataFrame(hist)
        df['date'] = pd.to_datetime(df['date'], unit='s')
        df.set_index('date', inplace=True)
        return df[['open','high','low','close','volume']]
    except:
        return pd.DataFrame()

# ==========================
# FEATURE ENGINEERING
# ==========================
def preparar_features(df):
    df = df.copy()
    df['retorno'] = df['close'].pct_change()
    df['mm7'] = df['close'].rolling(7).mean()
    df['mm21'] = df['close'].rolling(21).mean()
    df['vol'] = df['volume'].pct_change()
    df['alvo'] = (df['close'].shift(-1) > df['close']).astype(int)
    return df.dropna()

# ==========================
# MODELO
# ==========================
def prever_movimento(df):
    dados = preparar_features(df)
    if len(dados) < 10:  # Verificação mínima de dados
        return 0, 0.0
    X = dados[['close','retorno','mm7','mm21','vol']]
    y = dados['alvo']

    modelo = RandomForestClassifier(n_estimators=200, random_state=42)
    modelo.fit(X[:-1], y[:-1])

    prob = modelo.predict_proba(X.tail(1))[0]
    pred = modelo.predict(X.tail(1))[0]

    return pred, max(prob)*100

# ==========================
# CLASSIFICAÇÃO DE PERFIL
# ==========================
def classificar_acao(df):
    if len(df) < 30:  # Verificação mínima de dados
        return "DESCONHECIDO"
    vol = df['close'].pct_change().std()
    if vol < 0.015:
        return "DIVIDENDO"
    else:
        return "TRADE"

# ==========================
# RELATÓRIO COMPLETO
# ==========================
def executar_analise(tipo="AUTOMATICO"):
    texto = f"🚀 Victor Trader IA v5.0 ({tipo})\n"
    texto += f"📅 {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n"

    for acao in ACOES:
        df = buscar_dados(acao)
        if df.empty:
            texto += f"\n❌ {acao}: Sem dados."
            continue

        pred, prob = prever_movimento(df)
        perfil = classificar_acao(df)
        preco = df['close'].iloc[-1]

        # Integração do perfil na decisão do sinal
        if perfil == "DIVIDENDO":
            sinal = "HOLD"  # Para ações de dividendos, sugerir HOLD
        else:
            sinal = "COMPRA" if pred == 1 else "VENDA"

        texto += f"\n📊 {acao} | R$ {preco:.2f}"
        texto += f"\n👉 SINAL: {sinal}"
        if perfil == "TRADE":
            texto += f" ({prob:.1f}%)"
        texto += f"\n🎯 PERFIL: {perfil}\n"

        salvar_csv(acao, preco, sinal, perfil, prob if perfil == "TRADE" else 0.0)

    enviar_telegram(texto)

# ==========================
# CSV
# ==========================
def salvar_csv(ticker, preco, sinal, perfil, prob):
    df = pd.DataFrame([[datetime.datetime.now(), ticker, preco, sinal, perfil, prob]],
        columns=["Data","Ticker","Preco","Sinal","Perfil","Confianca"])

    df.to_csv(ARQ_CSV, mode='a', header=not os.path.exists(ARQ_CSV), index=False)

# ==========================
# TELEGRAM
# ==========================
def enviar_telegram(msg):
    if not TOKEN_TELEGRAM:
        return
    requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage",
        data={'chat_id': CHAT_ID, 'text': msg})

# ==========================
# GRÁFICO
# ==========================
def grafico(ticker):
    df = buscar_dados(ticker, "60d")
    if df.empty: return None

    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['open'], high=df['high'], low=df['low'], close=df['close'])])
    fig.update_layout(title=ticker, xaxis_rangeslider_visible=False)
    return fig

# ==========================
# STREAMLIT APP
# ==========================
st.set_page_config("Victor Trader IA", layout="wide")

st.title("🚀 Victor Trader IA v5.0")

if st.button("📡 ANALISAR MERCADO E ENVIAR TELEGRAM"):
    executar_analise("MANUAL")
    st.success("Relatório enviado.")

st.divider()

if os.path.exists(ARQ_CSV):
    df = pd.read_csv(ARQ_CSV)
    st.download_button("📥 Baixar CSV", df.to_csv(index=False), "historico.csv")

st.divider()

for acao in ACOES:
    fig = grafico(acao)
    if fig:
        st.plotly_chart(fig, use_container_width=True)