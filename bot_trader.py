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

def gerar_grafico_interativo(ticker):
    try:
        # Aumentamos o período para garantir que sempre haja dados para o gráfico
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)
        if df.empty: return None
        df = df['Close'].to_frame()
        df.columns = ['Close']
        df['MA10'] = df['Close'].rolling(window=10).mean()
        df = df.ffill().tail(40)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name='Preço', line=dict(color='#00ff00', width=3)))
        fig.add_trace(go.Scatter(x=df.index, y=df['MA10'], name='Tendência (MA10)', line=dict(color='#ff9900', dash='dot')))
        fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=350, margin=dict(l=5, r=5, t=5, b=5))
        return fig
    except: return None

def salvar_historico(ticker, sinal, lucro, prob):
    data_hoje = datetime.date.today().strftime("%Y-%m-%d")
    novo_dado = pd.DataFrame([[data_hoje, ticker, sinal, round(lucro, 2), f"{prob:.1f}%"]], 
                             columns=['Data', 'Ticker', 'Sinal', 'Lucro', 'Confiança'])
    if not os.path.isfile(NOME_ARQUIVO):
        novo_dado.to_csv(NOME_ARQUIVO, index=False)
    else:
        novo_dado.to_csv(NOME_ARQUIVO, mode='a', header=False, index=False)

def executar_analise_total():
    msg_final = "🧠 **SISTEMA QUANTITATIVO V3.2 PRO**\n"
    logs_integridade = []
    total_dia = 0
    
    try:
        macro = yf.download(['USDBRL=X', '^BVSP'], period="1y", progress=False)['Close'].ffill()
        logs_integridade.append("✅ Sensores Macro: OK")
    except:
        macro = None
        logs_integridade.append("⚠️ Modo Técnico: Macro Offline")

    for ticker in ACOES:
        try:
            # Baixa um histórico maior para garantir que a IA tenha 'massa' para treinar
            df = yf.download(ticker, period="2y", progress=False)['Close'].to_frame()
            df.columns = ['Close']
            df = df.ffill()
            
            # Indicadores Técnicos
            df['MA10'] = df['Close'].rolling(10).mean()
            df['Retorno'] = df['Close'].pct_change()
            df['Volat'] = df['Retorno'].rolling(5).std()
            
            X_cols = ['Close', 'MA10', 'Volat']
            if macro is not None:
                df = df.join(macro, how='left').ffill()
                X_cols += ['USDBRL=X', '^BVSP']
            
            df['Alvo_IA'] = (df['Close'].shift(-1) > df['Close']).astype(int)
            dados_ia = df.dropna()
            
            # Treinamento
            X, y = dados_ia[X_cols], dados_ia['Alvo_IA']
            modelo = RandomForestClassifier(n_estimators=150, random_state=42).fit(X[:-1], y[:-1])
            
            # Previsão
            previsao = modelo.predict(X.tail(1))[0]
            prob = max(modelo.predict_proba(X.tail(1))[0]) * 100
            
            preco_atual = df['Close'].iloc[-1]
            # Gerenciamento de Risco: Alvo 3% | Stop 1.5%
            stop, alvo = preco_atual * 0.985, preco_atual * 1.03
            
            lucro_simulado = 10000 * (df['Retorno'].iloc[-1]) if previsao == 1 else 0
            total_dia += lucro_simulado
            
            salvar_historico(ticker, "COMPRA" if previsao == 1 else "VENDA", lucro_simulado, prob)

            sinal_ico = "🟢" if previsao == 1 else "🔴"
            msg_final += f"\n{sinal_ico} **{ticker}** ({prob:.1f}%)\n"
            msg_final += f"   🎯 Alvo: {alvo:.2f} | 🛡️ Stop: {stop:.2f}\n"
        except Exception as e:
            logs_integridade.append(f"❌ {ticker}: {str(e)[:20]}")

    msg_final += f"\n💰 **HOJE: R$ {total_dia:.2f}**\n📡 **LOG:** " + " | ".join(logs_integridade)
    requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage", 
                  data={'chat_id': CHAT_ID, 'text': msg_final, 'parse_mode': 'Markdown'})