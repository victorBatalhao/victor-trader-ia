import pandas as pd
import yfinance as yf
import requests
import datetime
import os
import streamlit as st
import plotly.graph_objects as go
from sklearn.ensemble import RandomForestClassifier

# ==========================
# 1. CONFIGURAÇÕES (TELEGRAM)
# ==========================
TOKEN_TELEGRAM = "8238619023:AAEcPr19DnbSpb3Ufoo6sL6ylzTRzdItp80"
CHAT_ID = "5584195780"
# Yahoo Finance não precisa de Token!

# Lista formatada para o Yahoo (.SA para ações brasileiras)
ACOES = ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "KLBN11.SA", "BBAS3.SA", "TAEE11.SA"]
ARQ_CSV = "historico_ia_victor.csv"

# ==========================
# 2. BUSCA DE DADOS (YAHOO FINANCE)
# ==========================
@st.cache_data(ttl=600)
def buscar_dados_yahoo(ticker):
    try:
        # Busca 1 ano de dados com intervalos diários
        data = yf.download(ticker, period="1y", interval="1d", progress=False)
        if data.empty:
            return pd.DataFrame()
        return data
    except Exception:
        return pd.DataFrame()

# ==========================
# 3. INTELIGÊNCIA ARTIFICIAL
# ==========================
def analisar_ia_victor(df):
    try:
        df = df.copy()
        # Cálculo de indicadores para Trade e Dividendos
        df['Retorno'] = df['Close'].pct_change()
        df['Volatilidade'] = df['Retorno'].rolling(20).std()
        df['Alvo'] = (df['Close'].shift(-1) > df['Close']).astype(int)
        
        d = df.dropna()
        X = d[['Close', 'Retorno', 'Volatilidade']]
        y = d['Alvo']
        
        modelo = RandomForestClassifier(n_estimators=100, random_state=42)
        modelo.fit(X[:-1], y[:-1])
        
        pred = modelo.predict(X.tail(1))[0]
        prob = modelo.predict_proba(X.tail(1))[0]
        
        # Lógica de Perfil baseada em oscilação
        vol_atual = df['Volatilidade'].iloc[-1]
        perfil = "💰 DIVIDENDOS" if vol_atual < 0.018 else "⚔️ TRADE"
        status = "🚀 VALORIZAÇÃO" if pred == 1 else "📉 DEPRECIAÇÃO"
        
        return "COMPRA" if pred == 1 else "VENDA", max(prob)*100, perfil, status
    except:
        return "ERRO", 0, "N/A", "N/A"

# ==========================
# 4. INTERFACE E RELATÓRIOS
# ==========================
st.set_page_config(page_title="Victor Trader Pro IA", layout="wide")
st.title("🚀 Victor Trader IA v6.0 (Yahoo Finance)")

# Barra Lateral de Status Real-Time
st.sidebar.title("📡 Status Yahoo/B3")
for acao in ACOES:
    df_check = buscar_dados_yahoo(acao)
    if not df_check.empty:
        st.sidebar.success(f"{acao}: Conectado")
    else:
        st.sidebar.error(f"{acao}: Erro de Busca")

# Botão de Comando Mestre
if st.button("📡 ANALISAR TUDO E ENVIAR TELEGRAM", use_container_width=True):
    relatorio = f"🤖 **VICTOR TRADER IA - MODO YAHOO**\n📅 {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
    tem_dados = False
    
    for acao in ACOES:
        df = buscar_dados_yahoo(acao)
        if not df.empty and len(df) > 20:
            tem_dados = True
            sinal, conf, perfil, tend = analisar_ia_victor(df)
            preco_atual = float(df['Close'].iloc[-1])
            
            relatorio += f"\n📊 **{acao.replace('.SA', '')}** | R$ {preco_atual:.2f}"
            relatorio += f"\n👉 SINAL: {sinal} ({conf:.1f}%)"
            relatorio += f"\n🎯 PERFIL: {perfil} | {tend}\n"
            
            # Salva no CSV histórico
            pd.DataFrame([[datetime.datetime.now(), acao, preco_atual, sinal, perfil]], 
                         columns=["Data", "Ativo", "Preco", "Sinal", "Perfil"]).to_csv(ARQ_CSV, mode='a', header=not os.path.exists(ARQ_CSV), index=False)
    
    if tem_dados:
        # Envio via Telegram com formatação Markdown
        url_tel = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
        requests.post(url_tel, data={'chat_id': CHAT_ID, 'text': relatorio, 'parse_mode': 'Markdown'})
        st.success("✅ Relatório enviado com sucesso via Yahoo Finance!")
    else:
        st.error("❌ Falha crítica: O Yahoo Finance não retornou dados das ações.")

# Seção de Gráficos
st.divider()
st.subheader("📈 Gráficos de Candlestick (Visualização Técnica)")
col1, col2 = st.columns(2)
for i, acao in enumerate(ACOES):
    with col1 if i % 2 == 0 else col2:
        df_g = buscar_dados_yahoo(acao)
        if not df_g.empty:
            # Gráfico dos últimos 60 dias
            df_g = df_g.tail(60)
            fig = go.Figure(data=[go.Candlestick(x=df_g.index, open=df_g['Open'], high=df_g['High'], low=df_g['Low'], close=df_g['Close'])])
            fig.update_layout(title=f"Tendência: {acao}", xaxis_rangeslider_visible=False, template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

# Download CSV
if os.path.exists(ARQ_CSV):
    st.divider()
    df_csv = pd.read_csv(ARQ_CSV)
    st.download_button("📥 Baixar Histórico de Trades (CSV)", df_csv.to_csv(index=False), "victor_ia_history.csv", "text/csv")