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
    msg = "🚀 **VICTOR TRADER IA - SINAIS EM TEMPO REAL**\n"
    logs = []
    
    for ticker in ACOES:
        try:
            # Puxa dados de 1 ano para treino e o preço atual
            df = yf.download(ticker, period="1y", interval="1d", progress=False)
            if df.empty: raise ValueError("Sem dados")
            
            # Preço em tempo real
            p_atual = df['Close'].iloc[-1]
            
            # Preparação da IA
            df_train = df[['Close']].copy()
            df_train['Retorno'] = df_train['Close'].pct_change()
            df_train['Alvo'] = (df_train['Close'].shift(-1) > df_train['Close']).astype(int)
            dados = df_train.dropna()
            
            X = dados[['Close', 'Retorno']]
            y = dados['Alvo']
            modelo = RandomForestClassifier(n_estimators=50).fit(X[:-1], y[:-1])
            previsao = modelo.predict(X.tail(1))[0]
            prob = max(modelo.predict_proba(X.tail(1))[0]) * 100
            
            # Recomendação e Alvos
            acao = "🟢 COMPRAR" if previsao == 1 else "🔴 VENDER"
            alvo = p_atual * 1.03
            stop = p_atual * 0.985
            
            msg += f"\n📊 **{ticker}** | Preço: R$ {p_atual:.2f}\n👉 Ação: **{acao}** ({prob:.1f}%)\n🎯 Alvo: {alvo:.2f} | 🛡️ Stop: {stop:.2f}\n"
            logs.append(f"✅ {ticker}")
        except Exception as e:
            logs.append(f"❌ {ticker}: {str(e)}")

    msg += f"\n📡 **STATUS DO SISTEMA:**\n" + "\n".join(logs)
    requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage", 
                  data={'chat_id': CHAT_ID, 'text': msg, 'parse_mode': 'Markdown'})

def gerar_grafico_historico(ticker):
    try:
        # Puxa histórico detalhado dos últimos 60 dias
        df = yf.download(ticker, period="60d", interval="1d", progress=False)
        if df.empty: return None
        
        fig = go.Figure()
        # Gráfico de Candlestick para exibir valores de abertura, fechamento, etc
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], 
                                     low=df['Low'], close=df['Close'], name='Histórico'))
        
        fig.update_layout(
            title=f"Histórico Detalhado: {ticker}",
            template="plotly_dark",
            xaxis_rangeslider_visible=False,
            height=400,
            yaxis_title="Valor (R$)",
            xaxis_title="Data e Horário"
        )
        return fig
    except: return None