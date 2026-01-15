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

def salvar_historico(ticker, sinal, lucro, prob):
    data_hoje = datetime.date.today().strftime("%Y-%m-%d")
    df_novo = pd.DataFrame([[data_hoje, ticker, sinal, round(lucro, 2), f"{prob:.1f}%"]], 
                             columns=['Data', 'Ticker', 'Sinal', 'Lucro', 'Confiança'])
    if not os.path.isfile(NOME_ARQUIVO):
        df_novo.to_csv(NOME_ARQUIVO, index=False)
    else:
        df_novo.to_csv(NOME_ARQUIVO, mode='a', header=False, index=False)

def executar_analise_total():
    msg = "🧠 **SISTEMA QUANTITATIVO V3.2.5**\n"
    logs = []
    total_dia = 0
    
    try:
        macro = yf.download(['USDBRL=X', '^BVSP'], period="1y", progress=False)['Close'].ffill()
        logs.append("✅ Macro: OK")
    except:
        macro = None
        logs.append("⚠️ Macro: Offline")

    for ticker in ACOES:
        try:
            # Busca 1 ano de dados e garante que não pegue apenas o dia vazio de hoje
            df = yf.download(ticker, period="1y", progress=False)['Close'].to_frame()
            if df.empty or len(df) < 20: continue
            
            df.columns = ['Close']
            df = df.ffill().dropna()
            df['MA10'] = df['Close'].rolling(10).mean()
            df['Retorno'] = df['Close'].pct_change()
            df['Volat'] = df['Retorno'].rolling(5).std()
            
            X_cols = ['Close', 'MA10', 'Volat']
            if macro is not None:
                df = df.join(macro, how='inner').ffill()
                X_cols += ['USDBRL=X', '^BVSP']
            
            df['Alvo_IA'] = (df['Close'].shift(-1) > df['Close']).astype(int)
            dados = df.dropna()
            
            if len(dados) < 5: continue

            X, y = dados[X_cols], dados['Alvo_IA']
            modelo = RandomForestClassifier(n_estimators=100, random_state=42).fit(X[:-1], y[:-1])
            previsao = modelo.predict(X.tail(1))[0]
            prob = max(modelo.predict_proba(X.tail(1))[0]) * 100
            
            p_atual = df['Close'].iloc[-1]
            stop, alvo = p_atual * 0.985, p_atual * 1.03
            
            lucro_sim = 10000 * (df['Retorno'].iloc[-1]) if previsao == 1 else 0
            total_dia += lucro_sim
            
            salvar_historico(ticker, "COMPRA" if previsao == 1 else "VENDA", lucro_sim, prob)
            msg += f"\n{'🟢' if previsao == 1 else '🔴'} **{ticker}** ({prob:.1f}%)\n   🎯 Alvo: {alvo:.2f} | 🛡️ Stop: {stop:.2f}\n"
        except:
            logs.append(f"❌ {ticker}")

    msg += f"\n💰 **TOTAL DIA: R$ {total_dia:.2f}**\n📡 **LOG:** " + " | ".join(logs)
    requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage", data={'chat_id': CHAT_ID, 'text': msg, 'parse_mode': 'Markdown'})

def gerar_grafico_interativo(ticker):
    try:
        # Aumentamos para 6 meses para garantir que o gráfico nunca fique vazio
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)['Close'].to_frame()
        if df.empty: return None
        df.columns = ['Close']
        df['MA10'] = df['Close'].rolling(10).mean()
        df = df.tail(60).ffill()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name='Preço', line=dict(color='#00ff00')))
        fig.add_trace(go.Scatter(x=df.index, y=df['MA10'], name='Média 10d', line=dict(color='#ff9900', dash='dot')))
        fig.update_layout(template="plotly_dark", height=300, margin=dict(l=10, r=10, t=10, b=10))
        return fig
    except: return None