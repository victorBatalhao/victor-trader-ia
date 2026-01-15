import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import requests
import datetime
import os
from sklearn.ensemble import RandomForestClassifier

# --- CONFIGURAÇÕES DO PROJETO ---
TOKEN_TELEGRAM = "8238619023:AAEcPr19DnbSpb3Ufoo6sL6ylzTRzdItp80"
CHAT_ID = "5584195780"
ACOES = ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "KLBN11.SA", "BBAS3.SA", "TAEE11.SA"]
ARQ_CSV = "historico_victor_ia.csv"

# --- FUNÇÃO DE DADOS (GRÁFICOS OK) ---
@st.cache_data(ttl=600)
def buscar_dados(ticker):
    try:
        df = yf.download(ticker, period="1y", interval="1d", progress=False, auto_adjust=True)
        if df.empty: return pd.DataFrame()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except:
        return pd.DataFrame()

# --- INTELIGÊNCIA ARTIFICIAL ---
def motor_ia(df):
    try:
        df = df.copy()
        df['Retorno'] = df['Close'].pct_change()
        df['Volatilidade'] = df['Retorno'].rolling(20).std()
        df['Alvo'] = (df['Close'].shift(-1) > df['Close']).astype(int)
        
        dados = df.dropna()
        X = dados[['Close', 'Retorno', 'Volatilidade']]
        y = dados['Alvo']
        
        modelo = RandomForestClassifier(n_estimators=100, random_state=42)
        modelo.fit(X[:-1], y[:-1])
        
        pred = modelo.predict(X.tail(1))[0]
        prob = modelo.predict_proba(X.tail(1))[0]
        
        vol = df['Volatilidade'].iloc[-1]
        perfil = "💰 DIVIDENDOS" if vol < 0.017 else "⚔️ TRADE"
        tendencia = "🚀 ALTA (Valorização)" if pred == 1 else "📉 QUEDA (Depreciação)"
        
        return "COMPRA" if pred == 1 else "VENDA", max(prob)*100, perfil, tendencia
    except:
        return "ERRO", 0, "N/A", "N/A"

# --- INTERFACE ---
st.set_page_config(page_title="Victor Trader IA v6.5", layout="wide")
st.title("🤖 Victor Trader IA – Inteligência de Mercado")

st.sidebar.title("📡 Conexão B3")
for acao in ACOES:
    if not buscar_dados(acao).empty:
        st.sidebar.success(f"{acao}: Online")
    else:
        st.sidebar.error(f"{acao}: Offline")

# --- BOTÃO DE ENVIO (CORRIGIDO PARA TELEGRAM) ---
if st.button("📡 EXECUTAR ANÁLISE COMPLETA E ENVIAR TELEGRAM", use_container_width=True):
    msg = f"🤖 **RELATÓRIO VICTOR TRADER IA**\n📅 {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
    sucesso_envio = False
    
    for acao in ACOES:
        df = buscar_dados(acao)
        if not df.empty:
            sucesso_envio = True
            sinal, conf, perfil, tend = motor_ia(df)
            
            # CORREÇÃO CRÍTICA: Convertendo para float puro para o Telegram aceitar
            preco_raw = df['Close'].iloc[-1]
            preco_final = float(preco_raw.item()) if hasattr(preco_raw, 'item') else float(preco_raw)
            
            msg += f"\n📊 **{acao.replace('.SA', '')}** | R$ {preco_final:.2f}"
            msg += f"\n👉 SINAL: {sinal} ({conf:.1f}%)"
            msg += f"\n🎯 MODO: {perfil} | {tend}\n"
            
            # Salva histórico CSV
            pd.DataFrame([[datetime.datetime.now(), acao, preco_final, sinal, perfil]], 
                         columns=["Data","Ativo","Preco","Sinal","Perfil"]).to_csv(ARQ_CSV, mode='a', header=not os.path.exists(ARQ_CSV), index=False)
    
    if sucesso_envio:
        try:
            url_telegram = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
            response = requests.post(url_telegram, data={'chat_id': CHAT_ID, 'text': msg, 'parse_mode': 'Markdown'})
            
            if response.status_code == 200:
                st.success("✅ Relatório enviado com sucesso ao Telegram!")
            else:
                st.error(f"❌ Erro no Telegram: {response.text}")
        except Exception as e:
            st.error(f"❌ Erro de conexão: {e}")
    else:
        st.error("❌ Não foi possível coletar dados para o relatório.")

# --- GRÁFICOS (QUE JÁ ESTÃO FUNCIONANDO) ---
st.divider()
st.subheader("📈 Visualização Gráfica (Candlestick)")
cols = st.columns(2)
for i, acao in enumerate(ACOES):
    with cols[i % 2]:
        df_g = buscar_dados(acao)
        if not df_g.empty:
            fig = go.Figure(data=[go.Candlestick(
                x=df_g.index[-60:], open=df_g['Open'], high=df_g['High'], 
                low=df_g['Low'], close=df_g['Close']
            )])
            fig.update_layout(title=f"Ativo: {acao}", xaxis_rangeslider_visible=False, template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

if os.path.exists(ARQ_CSV):
    st.divider()
    df_h = pd.read_csv(ARQ_CSV)
    st.download_button("📥 Baixar Histórico de Análises (CSV)", df_h.to_csv(index=False), "historico_ia.csv", "text/csv")