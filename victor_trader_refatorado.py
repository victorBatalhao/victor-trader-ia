import os
import pandas as pd
import requests
import datetime
import streamlit as st
import plotly.graph_objects as go
from sklearn.ensemble import RandomForestClassifier

# --- CONFIGURAÇÃO MESTRE ---
TOKEN_TELEGRAM = "8238619023:AAEcPr19DnbSpb3Ufoo6sL6ylzTRzdItp80"
CHAT_ID = "5584195780"
TOKEN_BRAPI = "ngaj1shkPqZhAYL6Hcq5wB"
ACOES = ["PETR4", "VALE3", "ITUB4", "KLBN11", "BBAS3", "TAEE11"]
ARQ_CSV = "historico_ia_victor.csv"

# --- BUSCA DE DADOS COM TIMEOUT AMPLIADO ---
@st.cache_data(ttl=600)
def buscar_dados(ticker):
    try:
        # Adicionada a URL de verificação de cotação atual + histórico
        url = f"https://brapi.dev/api/quote/{ticker}?range=1y&interval=1d&token={TOKEN_BRAPI}"
        r = requests.get(url, timeout=20).json()
        if 'results' in r and r['results']:
            df = pd.DataFrame(r['results'][0]['historicalData'])
            df['date'] = pd.to_datetime(df['date'], unit='s')
            df.set_index('date', inplace=True)
            return df[['open','high','low','close','volume']]
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

# --- INTELIGÊNCIA ARTIFICIAL: TRADE VS DIVIDENDOS ---
def analisar_ia(df):
    try:
        df = df.copy()
        df['retorno'] = df['close'].pct_change()
        df['volatilidade'] = df['retorno'].rolling(20).std()
        df['alvo'] = (df['close'].shift(-1) > df['close']).astype(int)
        
        d = df.dropna()
        X = d[['close', 'retorno', 'volatilidade']]
        y = d['alvo']
        
        modelo = RandomForestClassifier(n_estimators=100, random_state=42)
        modelo.fit(X[:-1], y[:-1])
        
        pred = modelo.predict(X.tail(1))[0]
        prob = modelo.predict_proba(X.tail(1))[0]
        
        # Lógica de Perfil: Volatilidade baixa = Dividendos | Alta = Trade
        vol = df['volatilidade'].iloc[-1]
        perfil = "💰 DIVIDENDOS" if vol < 0.015 else "⚔️ TRADE"
        tendencia = "🚀 ALTA (Valorização)" if pred == 1 else "📉 QUEDA (Depreciação)"
        
        return "COMPRA" if pred == 1 else "VENDA", max(prob)*100, perfil, tendencia
    except:
        return "ERRO", 0, "N/A", "N/A"

# --- INTERFACE STREAMLIT ---
st.set_page_config(page_title="Victor Trader IA Mestre", layout="wide")
st.title("🚀 Victor Trader IA v5.5")
st.write("Análise Automática: Trade, Dividendos e Relatórios Automáticos.")

# Barra lateral de Conexão
st.sidebar.title("📡 Conexão B3")
for acao in ACOES:
    check = buscar_dados(acao)
    if not check.empty:
        st.sidebar.success(f"{acao}: Online")
    else:
        st.sidebar.error(f"{acao}: Offline/Erro Token")

# Botão de Relatório Manual
if st.button("📡 EXECUTAR ANÁLISE COMPLETA E NOTIFICAR TELEGRAM", use_container_width=True):
    relatorio = f"🤖 **VICTOR TRADER IA - RELATÓRIO MESTRE**\n📅 {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
    sucesso = False
    
    for acao in ACOES:
        df = buscar_dados(acao)
        if not df.empty:
            sucesso = True
            sinal, conf, perfil, tend = analisar_ia(df)
            preco = df['close'].iloc[-1]
            
            relatorio += f"\n📊 **{acao}** | R$ {preco:.2f}"
            relatorio += f"\n👉 SINAL: {sinal} ({conf:.1f}%)"
            relatorio += f"\n🎯 PERFIL: {perfil} | {tend}\n"
            
            # Salva no CSV
            pd.DataFrame([[datetime.datetime.now(), acao, preco, sinal, perfil]], 
                         columns=["Data", "Ativo", "Preco", "Sinal", "Perfil"]).to_csv(ARQ_CSV, mode='a', header=not os.path.exists(ARQ_CSV), index=False)
    
    if sucesso:
        requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage", 
                      data={'chat_id': CHAT_ID, 'text': relatorio, 'parse_mode': 'Markdown'})
        st.success("Relatório enviado ao Telegram!")
    else:
        st.error("Erro ao coletar dados da Brapi. Verifique o limite do token.")

# Gráficos e Download
st.divider()
if os.path.exists(ARQ_CSV):
    df_h = pd.read_csv(ARQ_CSV)
    st.subheader("📥 Histórico de Análises")
    st.dataframe(df_h.tail(5), use_container_width=True)
    st.download_button("Baixar Histórico CSV", df_h.to_csv(index=False), "historico.csv", "text/csv")

st.divider()
st.subheader("📈 Visualização Gráfica")
cols = st.columns(2)
for i, acao in enumerate(ACOES):
    with cols[i % 2]:
        df_g = buscar_dados(acao)
        if not df_g.empty:
            fig = go.Figure(data=[go.Candlestick(x=df_g.index[-60:], open=df_g['open'], high=df_g['high'], low=df_g['low'], close=df_g['close'])])
            fig.update_layout(title=f"Gráfico: {acao}", xaxis_rangeslider_visible=False, template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)