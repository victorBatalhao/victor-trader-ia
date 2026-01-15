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

def executar_analise_total(tipo_alerta="MANUAL"):
    """
    Realiza a análise quantitativa e envia para o Telegram.
    tipo_alerta: 'MANUAL' ou 'FECHAMENTO AUTOMÁTICO'.
    """
    msg = f"🚀 **VICTOR TRADER IA - {tipo_alerta}**\n"
    msg += f"📅 Data: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
    logs_status = []
    
    for ticker in ACOES:
        try:
            # Puxa histórico de 1 ano para garantir que a IA tenha amostras suficientes
            df = yf.download(ticker, period="1y", interval="1d", progress=False)
            if df.empty or len(df) < 50: 
                logs_status.append(f"⚠️ {ticker}: Dados insuficientes")
                continue
            
            p_atual = df['Close'].iloc[-1]
            
            # IA: Preparação de dados com foco em dias anteriores
            df['Retorno'] = df['Close'].pct_change()
            df['Alvo_IA'] = (df['Close'].shift(-1) > df['Close']).astype(int)
            dados = df.dropna()
            
            X, y = dados[['Close', 'Retorno']], dados['Alvo_IA']
            modelo = RandomForestClassifier(n_estimators=100, random_state=42).fit(X[:-1], y[:-1])
            previsao = modelo.predict(X.tail(1))[0]
            prob = max(modelo.predict_proba(X.tail(1))[0]) * 100
            
            # Regras de Alvo (3%) e Stop (1,5%) solicitadas
            ordem = "🟢 COMPRA" if previsao == 1 else "🔴 VENDA"
            alvo = p_atual * 1.03
            stop = p_atual * 0.985
            
            msg += f"\n📊 **{ticker}**: R$ {p_atual:.2f}\n👉 **ORDEM: {ordem}** ({prob:.1f}%)\n🎯 Alvo: {alvo:.2f} | 🛡️ Stop: {stop:.2f}\n"
            logs_status.append(f"✅ {ticker}: OK")
        except:
            logs_status.append(f"❌ {ticker}: Erro na API")

    msg += f"\n📡 **LOG DE INTEGRIDADE:**\n" + "\n".join(logs_status)
    requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage", 
                  data={'chat_id': CHAT_ID, 'text': msg, 'parse_mode': 'Markdown'})

def gerar_grafico_historico(ticker):
    """Gera gráficos de dias anteriores com Candlestick, datas e valores"""
    try:
        # Puxa 60 dias para garantir dados de mercado fechado
        df = yf.download(ticker, period="60d", interval="1d", progress=False)
        if df.empty: return None
        
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'], 
            low=df['Low'], close=df['Close'], name='Histórico de Preços'
        ))
        
        fig.update_layout(
            title=f"Histórico Detalhado: {ticker} (Datas e Valores)",
            template="plotly_dark",
            xaxis_rangeslider_visible=False,
            yaxis_title="Preço (R$)",
            xaxis_title="Data da Negociação",
            height=450
        )
        return fig
    except: return None