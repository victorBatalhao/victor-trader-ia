import yfinance as yf
import pandas as pd
import requests
from sklearn.ensemble import RandomForestClassifier
import datetime
import plotly.graph_objects as go

# --- CONFIGURAÇÕES ---
TOKEN_TELEGRAM = "8238619023:AAEcPr19DnbSpb3Ufoo6sL6ylzTRzdItp80"
CHAT_ID = "5584195780"
ACOES = ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "KLBN11.SA", "BBAS3.SA", "TAEE11.SA"]

def executar_analise_total(tipo_alerta="MANUAL"):
    msg = f"🚀 **VICTOR TRADER IA - {tipo_alerta}**\n"
    msg += f"📅 Data: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
    
    for ticker in ACOES:
        try:
            df = yf.download(ticker, period="1y", interval="1d", progress=False)
            if df.empty: continue
            
            p_atual = df['Close'].iloc[-1]
            df['Retorno'] = df['Close'].pct_change()
            df['Alvo_IA'] = (df['Close'].shift(-1) > df['Close']).astype(int)
            dados = df.dropna()
            
            X, y = dados[['Close', 'Retorno']], dados['Alvo_IA']
            modelo = RandomForestClassifier(n_estimators=100, random_state=42).fit(X[:-1], y[:-1])
            previsao = modelo.predict(X.tail(1))[0]
            prob = max(modelo.predict_proba(X.tail(1))[0]) * 100
            
            # Previsões: Alvo 3% e Stop 1,5%
            ordem = "🟢 COMPRA" if previsao == 1 else "🔴 VENDA"
            alvo, stop = p_atual * 1.03, p_atual * 0.985
            
            msg += f"\n📊 **{ticker}**: R$ {p_atual:.2f}\n👉 **ORDEM: {ordem}** ({prob:.1f}%)\n🎯 Alvo: {alvo:.2f} | 🛡️ Stop: {stop:.2f}\n"
        except:
            msg += f"\n⚠️ {ticker}: Erro nos dados."

    requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage", 
                  data={'chat_id': CHAT_ID, 'text': msg, 'parse_mode': 'Markdown'})

def gerar_grafico_historico(ticker):
    try:
        # Gráficos de dias anteriores para evitar tela preta
        df = yf.download(ticker, period="60d", interval="1d", progress=False)
        if df.empty: return None
        
        fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
        fig.update_layout(title=f"Histórico: {ticker}", template="plotly_dark", xaxis_rangeslider_visible=False, height=400)
        return fig
    except: return None