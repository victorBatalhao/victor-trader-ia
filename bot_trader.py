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
    """Gera um gráfico de preços com Médias Móveis para o Streamlit"""
    dados = yf.download(ticker, period="6mo", interval="1d", progress=False)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dados.index, y=dados['Close'], name='Preço', line=dict(color='#00ff00')))
    fig.add_trace(go.Scatter(x=dados.index, y=dados['Close'].rolling(10).mean(), name='Média 10d', line=dict(dash='dot')))
    fig.update_layout(
        title=f"Tendência: {ticker}",
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        height=400,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig

def calcular_gerenciamento_risco(preco_atual, volatilidade):
    """Calcula Alvo e Stop Loss baseados na volatilidade"""
    margem_stop = preco_atual * (volatilidade * 1.5)
    margem_alvo = preco_atual * (volatilidade * 3.0)
    return preco_atual - margem_stop, preco_atual + margem_alvo

def analisar_correlacao(dados):
    correl = dados['USDBRL=X'].pct_change().corr(dados['^BVSP'].pct_change())
    if correl < -0.5:
        return "⚠️ **ALERTA DE MACRO:** Correlação Dólar vs Ibov forte (Fuga de Risco)."
    return "✅ **MACRO:** Correlação estável."

def salvar_historico(ticker, sinal, lucro):
    data_hoje = datetime.date.today().strftime("%Y-%m-%d")
    novo_dado = pd.DataFrame([[data_hoje, ticker, sinal, lucro]], columns=['Data', 'Ticker', 'Sinal', 'Lucro'])
    if not os.path.isfile(NOME_ARQUIVO):
        novo_dado.to_csv(NOME_ARQUIVO, index=False)
    else:
        novo_dado.to_csv(NOME_ARQUIVO, mode='a', header=False, index=False)

def calcular_lucro_mensal():
    if not os.path.isfile(NOME_ARQUIVO): return 0.0
    df = pd.read_csv(NOME_ARQUIVO)
    df['Data'] = pd.to_datetime(df['Data'])
    mes, ano = datetime.date.today().month, datetime.date.today().year
    return df[(df['Data'].dt.month == mes) & (df['Data'].dt.year == ano)]['Lucro'].sum()

def executar_analise_total():
    tickers_macro = ['BZ=F', 'USDBRL=X', '^BVSP']
    dados = yf.download(ACOES + tickers_macro, period="2y", interval="1d", progress=False)['Close']
    alerta_macro = analisar_correlacao(dados)
    msg_final = f"🧠 **SISTEMA QUANTITATIVO V3.1**\n{alerta_macro}\n\n"
    total_dia = 0

    for ticker in ACOES:
        df = pd.DataFrame(dados[ticker]).rename(columns={ticker: 'Close'})
        df['MA10'] = df['Close'].rolling(10).mean()
        df['Volatilidade'] = df['Close'].pct_change().rolling(5).std()
        df['Brent'], df['Dolar'], df['Ibov'] = dados['BZ=F'], dados['USDBRL=X'], dados['^BVSP']
        df['Alvo_IA'] = (df['Close'].shift(-1) > df['Close']).astype(int)
        df = df.dropna()
        
        X = df[['Close', 'MA10', 'Volatilidade', 'Brent', 'Dolar', 'Ibov']]
        y = df['Alvo_IA']
        modelo = RandomForestClassifier(n_estimators=100, random_state=42).fit(X[:-1], y[:-1])
        previsao = modelo.predict(X.tail(1))[0]
        prob = max(modelo.predict_proba(X.tail(1))[0]) * 100
        
        preco_atual = df['Close'].iloc[-1]
        stop, alvo = calcular_gerenciamento_risco(preco_atual, df['Volatilidade'].iloc[-1])
        
        variacao = (df['Close'].iloc[-1] / df['Close'].iloc[-2] - 1) * 100
        lucro_hoje = 10000 * (variacao / 100) if previsao == 1 else 0
        total_dia += lucro_hoje
        salvar_historico(ticker, "COMPRA" if previsao == 1 else "VENDA", lucro_hoje)

        msg_final += f"📍 **{ticker}** | {'🟢' if previsao == 1 else '🔴'} ({prob:.1f}%)\n"
        if previsao == 1:
            msg_final += f"   🎯 Alvo: R$ {alvo:.2f} | 🛡️ Stop: R$ {stop:.2f}\n"
        msg_final += f"   💰 Simulação: R$ {lucro_hoje:.2f}\n\n"

    msg_final += f"📊 **BALANÇO MENSAL: R$ {calcular_lucro_mensal():.2f}**\n💵 **HOJE: R$ {total_dia:.2f}**"
    requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage", data={'chat_id': CHAT_ID, 'text': msg_final, 'parse_mode': 'Markdown'})