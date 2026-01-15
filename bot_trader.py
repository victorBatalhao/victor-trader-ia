import pandas as pd
import requests
from sklearn.ensemble import RandomForestClassifier
import datetime
import os
import plotly.graph_objects as go

# --- CONFIGURAÇÕES ---
TOKEN_TELEGRAM = "8238619023:AAEcPr19DnbSpb3Ufoo6sL6ylzTRzdItp80"
CHAT_ID = "5584195780"
TOKEN_BRAPI = "ngaj1shkPqZhAYL6Hcq5wB"
ACOES = ["PETR4", "VALE3", "ITUB4", "KLBN11", "BBAS3", "TAEE11"]
NOME_ARQUIVO = "database_performance.csv"

def buscar_dados_brapi(ticker, range_days="60d"):
    """Busca dados históricos e atuais usando o Token fornecido"""
    try:
        url = f"https://brapi.dev/api/quote/{ticker}?range={range_days}&interval=1d&token={TOKEN_BRAPI}"
        response = requests.get(url).json()
        if 'results' not in response or not response['results']:
            return pd.DataFrame()
        
        results = response['results'][0]['historicalData']
        df = pd.DataFrame(results)
        df['date'] = pd.to_datetime(df['date'], unit='s')
        df.set_index('date', inplace=True)
        return df[['open', 'high', 'low', 'close']]
    except Exception as e:
        print(f"Erro na API Brapi para {ticker}: {e}")
        return pd.DataFrame()

def executar_analise_total(tipo_alerta="MANUAL"):
    msg = f"🚀 **VICTOR TRADER IA v4.0 - {tipo_alerta}**\n"
    msg += f"📅 {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
    
    for ticker in ACOES:
        try:
            # Puxa 1 ano para treino da IA
            df = buscar_dados_brapi(ticker, "1y")
            if df.empty: continue
            
            p_atual = df['close'].iloc[-1]
            df['retorno'] = df['close'].pct_change()
            df['alvo_ia'] = (df['close'].shift(-1) > df['close']).astype(int)
            dados = df.dropna()
            
            X, y = dados[['close', 'retorno']], dados['alvo_ia']
            modelo = RandomForestClassifier(n_estimators=100, random_state=42).fit(X[:-1], y[:-1])
            previsao = modelo.predict(X.tail(1))[0]
            prob = max(modelo.predict_proba(X.tail(1))[0]) * 100
            
            ordem = "🟢 COMPRA" if previsao == 1 else "🔴 VENDA"
            alvo, stop = p_atual * 1.03, p_atual * 0.985
            
            # Atualiza arquivo CSV para download
            df_hist = pd.DataFrame([[datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), ticker, ordem, round(p_atual, 2), f"{prob:.1f}%"]], 
                                    columns=['Data', 'Ticker', 'Sinal', 'Preco', 'Confianca'])
            df_hist.to_csv(NOME_ARQUIVO, mode='a', header=not os.path.exists(NOME_ARQUIVO), index=False)
            
            msg += f"\n📊 **{ticker}**: R$ {p_atual:.2f}\n👉 **AÇÃO: {ordem}** ({prob:.1f}%)\n🎯 Alvo: {alvo:.2f} | 🛡️ Stop: {stop:.2f}\n"
        except:
            msg += f"\n⚠️ **{ticker}**: Erro no processamento."

    # Envio da mensagem completa para o Telegram
    requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage", 
                  data={'chat_id': CHAT_ID, 'text': msg, 'parse_mode': 'Markdown'})

def gerar_grafico_historico(ticker):
    """Gera gráficos de velas detalhados com datas e valores"""
    try:
        df = buscar_dados_brapi(ticker, "60d")
        if df.empty: return None
        
        fig = go.Figure(data=[go.Candlestick(
            x=df.index, open=df['open'], high=df['high'], 
            low=df['low'], close=df['close'], name='Preço B3'
        )])
        fig.update_layout(title=f"Histórico 60 Dias: {ticker}", template="plotly_dark", 
                          xaxis_rangeslider_visible=False, height=450)
        return fig
    except: return None