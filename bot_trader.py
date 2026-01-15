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
    """Gera gráfico garantindo preenchimento de dados para evitar NaN"""
    try:
        df = yf.download(ticker, period="1y", interval="1d", progress=False)
        if df.empty: return None
        
        # Consolida os dados para garantir que MA10 não falhe
        df = df['Close'].to_frame()
        df.columns = ['Close']
        df['MA10'] = df['Close'].rolling(window=10).mean()
        df = df.ffill().tail(100) # Últimos 100 pregões
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name='Preço', line=dict(color='#00ff00')))
        fig.add_trace(go.Scatter(x=df.index, y=df['MA10'], name='Média 10d', line=dict(color='#ff9900', dash='dot')))
        
        fig.update_layout(
            title=f"Tendência de Preço: {ticker}",
            template="plotly_dark",
            xaxis_rangeslider_visible=False,
            height=400,
            margin=dict(l=10, r=10, t=40, b=10)
        )
        return fig
    except:
        return None

def salvar_historico(ticker, sinal, lucro):
    data_hoje = datetime.date.today().strftime("%Y-%m-%d")
    novo_dado = pd.DataFrame([[data_hoje, ticker, sinal, lucro]], columns=['Data', 'Ticker', 'Sinal', 'Lucro'])
    if not os.path.isfile(NOME_ARQUIVO):
        novo_dado.to_csv(NOME_ARQUIVO, index=False)
    else:
        novo_dado.to_csv(NOME_ARQUIVO, mode='a', header=False, index=False)

def calcular_lucro_mensal():
    if not os.path.isfile(NOME_ARQUIVO): return 0.0
    try:
        df = pd.read_csv(NOME_ARQUIVO)
        df['Data'] = pd.to_datetime(df['Data'])
        mes, ano = datetime.date.today().month, datetime.date.today().year
        return df[(df['Data'].dt.month == mes) & (df['Data'].dt.year == ano)]['Lucro'].sum()
    except: return 0.0

def executar_analise_total():
    msg_final = "🧠 **SISTEMA QUANTITATIVO V3.2**\n"
    logs_integridade = []
    total_dia = 0
    
    # 1. TENTA DADOS MACRO (Dólar e Ibov)
    try:
        macro = yf.download(['USDBRL=X', '^BVSP'], period="1y", progress=False)['Close'].ffill()
        if macro.empty: raise Exception
        logs_integridade.append("✅ Dados Macro: OK")
    except:
        macro = None
        logs_integridade.append("⚠️ Dados Macro: Indisponíveis (IA operando em modo técnico)")

    # 2. ANALISA CADA AÇÃO INDIVIDUALMENTE
    for ticker in ACOES:
        try:
            df = yf.download(ticker, period="1y", progress=False)['Close'].to_frame()
            if df.empty:
                logs_integridade.append(f"❌ {ticker}: Falha na conexão")
                continue
            
            df.columns = ['Close']
            df = df.ffill()
            
            # Indicadores fundamentais
            df['MA10'] = df['Close'].rolling(10).mean()
            df['Retorno'] = df['Close'].pct_change()
            df['Volatilidade'] = df['Retorno'].rolling(5).std()
            
            # IA Dinâmica: se tiver macro usa, se não, usa só o técnico
            cols_treino = ['Close', 'MA10', 'Volatilidade']
            if macro is not None:
                df = df.join(macro).ffill()
                cols_treino += ['USDBRL=X', '^BVSP']
            
            df['Alvo'] = (df['Close'].shift(-1) > df['Close']).astype(int)
            dados_ia = df.dropna()
            
            if len(dados_ia) < 30:
                logs_integridade.append(f"⚠️ {ticker}: Histórico insuficiente")
                continue

            X = dados_ia[cols_treino]
            y = dados_ia['Alvo']
            
            modelo = RandomForestClassifier(n_estimators=100, random_state=42).fit(X[:-1], y[:-1])
            previsao = modelo.predict(X.tail(1))[0]
            prob = max(modelo.predict_proba(X.tail(1))[0]) * 100
            
            # Gerenciamento de Risco
            preco_atual = df['Close'].iloc[-1]
            stop, alvo = preco_atual * 0.985, preco_atual * 1.03
            
            # Financeiro
            variacao = df['Retorno'].iloc[-1] * 100
            lucro_hoje = 10000 * (variacao / 100) if previsao == 1 else 0
            total_dia += lucro_hoje
            salvar_historico(ticker, "COMPRA" if previsao == 1 else "VENDA", lucro_hoje)

            sinal_txt = "🟢 COMPRA" if previsao == 1 else "🔴 VENDA"
            msg_final += f"\n📍 **{ticker}** | {sinal_txt} ({prob:.1f}%)\n"
            if previsao == 1:
                msg_final += f"   🎯 Alvo: R$ {alvo:.2f} | 🛡️ Stop: R$ {stop:.2f}\n"
            msg_final += f"   💰 Resultado: R$ {lucro_hoje:.2f}\n"

        except Exception as e:
            logs_integridade.append(f"⚠️ Erro em {ticker}")

    # Finalização da Mensagem
    msg_final += f"\n💰 **TOTAL DIA: R$ {total_dia:.2f}**"
    msg_final += f"\n📊 **BALANÇO MÊS: R$ {calcular_lucro_mensal():.2f}**"
    msg_final += "\n\n📡 **LOG DE INTEGRIDADE:**\n" + "\n".join(logs_integridade)
    
    requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage", 
                  data={'chat_id': CHAT_ID, 'text': msg_final, 'parse_mode': 'Markdown'})