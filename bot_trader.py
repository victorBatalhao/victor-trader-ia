import yfinance as yf
import pandas as pd
import requests
from sklearn.ensemble import RandomForestClassifier
import datetime
import os
import plotly.graph_objects as go

# --- CONFIGURAÇÕES ---
TOKEN_TELEGRAM = "8238619023:AAEcPr19DnbSpb3Ufoo6sL6ylzTRzdItp80"
CHAT_ID = "5584195780"
ACOES = ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "KLBN11.SA", "BBAS3.SA", "TAEE11.SA"]
NOME_ARQUIVO = "database_performance.csv"

def executar_analise_total():
    msg = "🚀 **VICTOR TRADER IA - RECOMENDAÇÕES**\n"
    logs = []
    
    for ticker in ACOES:
        try:
            # Puxa 1 ano de dados para garantir que a IA tenha amostras
            df = yf.download(ticker, period="1y", interval="1d", progress=False)
            if df.empty or len(df) < 50: 
                raise ValueError("Dados insuficientes na API")
            
            p_atual = df['Close'].iloc[-1]
            
            # Treinamento da IA
            df['Retorno'] = df['Close'].pct_change()
            df['Alvo'] = (df['Close'].shift(-1) > df['Close']).astype(int)
            dados = df.dropna()
            
            X = dados[['Close', 'Retorno']]
            y = dados['Alvo']
            modelo = RandomForestClassifier(n_estimators=100).fit(X[:-1], y[:-1])
            previsao = modelo.predict(X.tail(1))[0]
            prob = max(modelo.predict_proba(X.tail(1))[0]) * 100
            
            # Recomendação direta
            ordem = "🟢 COMPRA" if previsao == 1 else "🔴 VENDA"
            alvo, stop = p_atual * 1.03, p_atual * 0.985
            
            msg += f"\n📊 **{ticker}** | Agora: R$ {p_atual:.2f}\n👉 **AÇÃO: {ordem}** ({prob:.1f}%)\n🎯 Alvo: {alvo:.2f} | 🛡️ Stop: {stop:.2f}\n"
            logs.append(f"✅ {ticker}: OK")
            
        except Exception as e:
            logs.append(f"❌ {ticker}: {str(e)}")

    msg += f"\n📡 **SITUAÇÃO DO MERCADO:**\n" + "\n".join(logs)
    requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage", 
                  data={'chat_id': CHAT_ID, 'text': msg, 'parse_mode': 'Markdown'})

def gerar_grafico_historico(ticker):
    try:
        # Puxa dados detalhados para o gráfico web
        df = yf.download(ticker, period="60d", interval="1d", progress=False)
        if df.empty: return None
        
        fig = go.Figure()
        # Gráfico de Candlestick (Velas) com Datas e Valores
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], 
                                     low=df['Low'], close=df['Close'], name='Preço'))
        
        fig.update_layout(
            title=f"Histórico de Preços: {ticker}",
            template="plotly_dark",
            xaxis_rangeslider_visible=False,
            yaxis_title="Valor (R$)",
            xaxis_title="Data da Negociação"
        )
        return fig
    except: return None