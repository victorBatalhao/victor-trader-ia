# =============================
# VICTOR TRADER IA v7.0 PRO
# Arquitetura Quant Profissional
# =============================

import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import requests
import datetime
import os
import numpy as np
from sklearn.ensemble import RandomForestClassifier

# =============================
# CONFIGURAÇÕES
# =============================
TOKEN_TELEGRAM = "SEU_TOKEN"
CHAT_ID = "SEU_CHAT_ID"
ACOES = ["PETR4.SA","VALE3.SA","ITUB4.SA","KLBN11.SA","BBAS3.SA","TAEE11.SA"]
ARQ_CSV = "historico_victor_ia.csv"
CAPITAL_INICIAL = 10000

# =============================
# DADOS
# =============================
@st.cache_data(ttl=600)
def buscar_dados(ticker):
    df = yf.download(ticker, period="2y", interval="1d", progress=False, auto_adjust=True)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.dropna()

# =============================
# FEATURES + IA
# =============================
def motor_ia(df):
    df = df.copy()
    df['Retorno'] = df['Close'].pct_change()
    df['Vol'] = df['Retorno'].rolling(20).std()
    df['MM9'] = df['Close'].rolling(9).mean()
    df['MM21'] = df['Close'].rolling(21).mean()
    df['RSI'] = 100 - (100/(1+(df['Close'].diff().clip(lower=0).rolling(14).mean() / abs(df['Close'].diff().clip(upper=0).rolling(14).mean()))))
    df['Alvo'] = (df['Close'].shift(-1) > df['Close']).astype(int)
    dados = df.dropna()

    X = dados[['Close','Retorno','Vol','MM9','MM21','RSI']]
    y = dados['Alvo']

    modelo = RandomForestClassifier(n_estimators=200, random_state=42)
    modelo.fit(X[:-1], y[:-1])

    pred = modelo.predict(X.tail(1))[0]
    prob = modelo.predict_proba(X.tail(1))[0]

    return pred, max(prob)*100, df

# =============================
# REGRAS TÉCNICAS
# =============================
def regra_tecnica(df):
    if df['MM9'].iloc[-1] > df['MM21'].iloc[-1] and df['RSI'].iloc[-1] < 70:
        return 1
    else:
        return 0

# =============================
# ESTRATÉGIA HÍBRIDA
# =============================
def estrategia_hibrida(df):
    pred, prob, df = motor_ia(df)
    regra = regra_tecnica(df)

    final = 1 if pred == 1 and regra == 1 else 0

    return final, prob, df

# =============================
# BACKTEST
# =============================
def backtest(df):
    capital = CAPITAL_INICIAL
    pico = capital
    drawdowns = []

    for i in range(50, len(df)-1):
        sub = df.iloc[:i]
        sinal, prob, _ = estrategia_hibrida(sub)
        retorno = (df['Close'].iloc[i+1] - df['Close'].iloc[i]) / df['Close'].iloc[i]

        if sinal == 1:
            capital *= (1 + retorno)
        pico = max(pico, capital)
        drawdowns.append((capital - pico) / pico)

    return capital, min(drawdowns)

# =============================
# SIMULADOR DE CARTEIRA
# =============================
def simular_carteira():
    capital = CAPITAL_INICIAL
    resultados = []
    for acao in ACOES:
        df = buscar_dados(acao)
        cap, dd = backtest(df)
        resultados.append([acao, round(cap,2), round(dd*100,2)])
    return pd.DataFrame(resultados, columns=["Ativo","Capital_Final","Drawdown_%"])

# =============================
# RELATÓRIO PREMIUM
# =============================
def gerar_relatorio():
    texto = "📊 RELATÓRIO VICTOR TRADER PRO\n"
    texto += f"📅 {datetime.datetime.now().strftime('%d/%m/%Y')}\n"

    for acao in ACOES:
        df = buscar_dados(acao)
        sinal, prob, _ = estrategia_hibrida(df)
        preco = df['Close'].iloc[-1]
        texto += f"\n{acao.replace('.SA','')} | R$ {preco:.2f}"
        texto += f"\nSINAL: {'COMPRA' if sinal==1 else 'NEUTRO'} ({prob:.1f}%)\n"

    return texto

# =============================
# TELEGRAM
# =============================
def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
    requests.post(url, data={'chat_id': CHAT_ID, 'text': msg})

# =============================
# STREAMLIT
# =============================
st.set_page_config("Victor Trader IA v7.0 PRO", layout="wide")

st.title("🚀 Victor Trader IA v7.0 PRO")

if st.button("📡 GERAR RELATÓRIO PREMIUM E ENVIAR"):
    rel = gerar_relatorio()
    enviar_telegram(rel)
    st.success("Relatório enviado com sucesso.")

st.divider()

st.subheader("📈 Backtest & Carteira")

carteira = simular_carteira()
st.dataframe(carteira, use_container_width=True)

st.divider()

st.subheader("📉 Gráficos")
cols = st.columns(2)
for i, acao in enumerate(ACOES):
    with cols[i % 2]:
        df = buscar_dados(acao)
        fig = go.Figure(data=[go.Candlestick(x=df.index[-60:], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
        fig.update_layout(title=acao, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
