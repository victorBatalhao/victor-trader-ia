import pandas as pd
import requests
from sklearn.ensemble import RandomForestClassifier
import datetime
import os
import plotly.graph_objects as go
import streamlit as st

# --- CONFIGURAÇÕES ---
TOKEN_TELEGRAM = "8238619023:AAEcPr19DnbSpb3Ufoo6sL6ylzTRzdItp80"
CHAT_ID = "5584195780"
TOKEN_BRAPI = "ngaj1shkPqZhAYL6Hcq5wB"
ACOES = ["PETR4", "VALE3", "ITUB4", "KLBN11", "BBAS3", "TAEE11"]
NOME_ARQUIVO = "database_performance.csv"

@st.cache_data(ttl=300) # Evita gastar token repetidamente por 5 minutos
def buscar_dados_brapi(ticker, range_days="60d"):
    try:
        url = f"https://brapi.dev/api/quote/{ticker}?range={range_days}&interval=1d&token={TOKEN_BRAPI}"
        response = requests.get(url, timeout=10).json()
        if 'results' in response and response['results']:
            results = response['results'][0].get('historicalData', [])
            if results:
                df = pd.DataFrame(results)
                df['date'] = pd.to_datetime(df['date'], unit='s')
                df.set_index('date', inplace=True)
                return df[['open', 'high', 'low', 'close']]
        return pd.DataFrame()
    except:
        return pd.DataFrame()

def executar_analise_total(tipo_alerta="MANUAL"):
    msg = f"🚀 **VICTOR TRADER IA v4.1 - {tipo_alerta}**\n"
    msg += f"📅 {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
    corpo_msg = ""
    
    for ticker in ACOES:
        try:
            df = buscar_dados_brapi(ticker, "1y")
            if df.empty: 
                corpo_msg += f"\n⚠️ **{ticker}**: Dados indisponíveis na API."
                continue
            
            p_atual = df['close'].iloc[-1]
            df['retorno'] = df['close'].pct_change()
            df['alvo_ia'] = (df['close'].shift(-1) > df['close']).astype(int)
            dados = df.dropna()
            
            X, y = dados[['close', 'retorno']], dados['alvo_ia']
            modelo = RandomForestClassifier(n_estimators=100, random_state=42).fit(X[:-1], y[:-1])
            previsao = modelo.predict(X.tail(1))[0]
            prob = max(modelo.predict_proba(X.tail(1))[0]) * 100
            
            ordem = "🟢 COMPRA" if previsao == 1 else "🔴 VENDA"
            corpo_msg += f"\n📊 **{ticker}**: R$ {p_atual:.2f}\n👉 **AÇÃO: {ordem}** ({prob:.1f}%)\n🎯 Alvo: {p_atual*1.03:.2f} | 🛡️ Stop: {p_atual*0.985:.2f}\n"
            
            # Histórico CSV
            df_hist = pd.DataFrame([[datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), ticker, ordem, round(p_atual, 2)]], 
                                    columns=['Data', 'Ticker', 'Sinal', 'Preco'])
            df_hist.to_csv(NOME_ARQUIVO, mode='a', header=not os.path.exists(NOME_ARQUIVO), index=False)
        except:
            corpo_msg += f"\n❌ **{ticker}**: Erro técnico."

    # Envio garantido do conteúdo acumulado
    final_msg = msg + corpo_msg
    requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage", 
                  data={'chat_id': CHAT_ID, 'text': final_msg, 'parse_mode': 'Markdown'})

def gerar_grafico_historico(ticker):
    try:
        df = buscar_dados_brapi(ticker, "60d")
        if df.empty: return None
        fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['open'], high=df['high'], low=df['low'], close=df['close'])])
        fig.update_layout(title=f"Histórico: {ticker}", template="plotly_dark", xaxis_rangeslider_visible=False, height=400)
        return fig
    except: return None