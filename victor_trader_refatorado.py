import os
import pandas as pd
import requests
import datetime
import numpy as np
import streamlit as st
import plotly.graph_objects as go
from sklearn.ensemble import RandomForestClassifier

# ==========================
# CONFIGURAÇÕES TÉCNICAS (DIRETAS)
# ==========================
TOKEN_TELEGRAM = "8238619023:AAEcPr19DnbSpb3Ufoo6sL6ylzTRzdItp80"
CHAT_ID = "5584195780"
TOKEN_BRAPI = "ngaj1shkPqZhAYL6Hcq5wB"

ACOES = ["PETR4", "VALE3", "ITUB4", "KLBN11", "BBAS3", "TAEE11"]
ARQ_CSV = "historico_victor_ia.csv"

# ==========================
# MOTOR DE DADOS & IA
# ==========================
@st.cache_data(ttl=900)
def buscar_dados(ticker, dias="1y"):
    try:
        url = f"https://brapi.dev/api/quote/{ticker}?range={dias}&interval=1d&token={TOKEN_BRAPI}"
        r = requests.get(url, timeout=15).json()
        if 'results' not in r: return pd.DataFrame()
        df = pd.DataFrame(r['results'][0]['historicalData'])
        df['date'] = pd.to_datetime(df['date'], unit='s')
        df.set_index('date', inplace=True)
        return df[['open','high','low','close','volume']]
    except:
        return pd.DataFrame()

def inteligencia_artificial(df):
    try:
        df = df.copy()
        # Indicadores para Trade e Dividendos
        df['retorno'] = df['close'].pct_change()
        df['volatilidade'] = df['retorno'].rolling(20).std()
        df['mm7'] = df['close'].rolling(7).mean()
        df['mm21'] = df['close'].rolling(21).mean()
        df['alvo'] = (df['close'].shift(-1) > df['close']).astype(int)
        
        dados = df.dropna()
        X = dados[['close', 'retorno', 'volatilidade', 'mm7', 'mm21']]
        y = dados['alvo']
        
        modelo = RandomForestClassifier(n_estimators=200, random_state=42)
        modelo.fit(X[:-1], y[:-1])
        
        prob = modelo.predict_proba(X.tail(1))[0]
        pred = modelo.predict(X.tail(1))[0]
        vol_atual = df['volatilidade'].iloc[-1]
        
        # Lógica de Classificação: Trade vs Dividendos
        perfil = "💰 DIVIDENDOS (Baixa Vol)" if vol_atual < 0.02 else "⚔️ TRADE (Alta Vol)"
        return pred, max(prob)*100, perfil
    except:
        return 0, 50.0, "Indefinido"

# ==========================
# RELATÓRIO E TELEGRAM
# ==========================
def gerar_relatorio(tipo_envio="MANUAL"):
    msg = f"🚀 **VICTOR TRADER IA v5.1 ({tipo_envio})**\n"
    msg += f"📅 {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
    tem_sucesso = False

    for acao in ACOES:
        df = buscar_dados(acao)
        if not df.empty and len(df) > 30:
            tem_sucesso = True
            pred, conf, perfil = inteligencia_artificial(df)
            preco = df['close'].iloc[-1]
            sinal = "🟢 COMPRA" if pred == 1 else "🔴 VENDA"
            depreciacao = "⚠️ Risco de Queda" if sinal == "🔴 VENDA" else "🚀 Tendência Alta"

            msg += f"\n📊 **{acao}** | R$ {preco:.2f}\n"
            msg += f"👉 **{sinal}** ({conf:.1f}%)\n"
            msg += f"🎯 Perfil: {perfil}\n"
            msg += f"📉 Status: {depreciacao}\n"

            # Salva no histórico CSV
            novo_dado = pd.DataFrame([[datetime.datetime.now(), acao, preco, sinal, perfil]], 
                                     columns=["Data", "Ticker", "Preco", "Sinal", "Perfil"])
            novo_dado.to_csv(ARQ_CSV, mode='a', header=not os.path.exists(ARQ_CSV), index=False)

    if tem_sucesso:
        requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage", 
                      data={'chat_id': CHAT_ID, 'text': msg, 'parse_mode': 'Markdown'})
        return True
    return False

# ==========================
# INTERFACE GRÁFICA (STREAMLIT)
# ==========================
st.set_page_config(page_title="Victor Trader IA", layout="wide", page_icon="🤖")

st.sidebar.title("📡 Conexão B3")
for acao in ACOES:
    d = buscar_dados(acao, "1d")
    if not d.empty:
        st.sidebar.success(f"{acao}: Online")
    else:
        st.sidebar.error(f"{acao}: Offline")

st.title("🤖 Victor Trader IA – Inteligência de Mercado")
st.markdown("---")

if st.button("🚀 EXECUTAR ANÁLISE AGORA E ENVIAR RELATÓRIO", use_container_width=True):
    with st.spinner("IA analisando preços, tendências e volatilidade..."):
        if gerar_relatorio("MANUAL"):
            st.success("Relatório enviado com sucesso ao Telegram!")
        else:
            st.error("Erro ao coletar dados. Verifique o token Brapi.")

st.divider()

# Download de CSV
if os.path.exists(ARQ_CSV):
    df_csv = pd.read_csv(ARQ_CSV)
    st.subheader("📥 Exportar Dados de Operação")
    st.download_button("Clique aqui para baixar o CSV Histórico", df_csv.to_csv(index=False), "relatorio_victor.csv", "text/csv")

st.divider()

# Gráficos de Visualização
st.subheader("📈 Interface de Visualização Gráfica")
cols = st.columns(2)
for i, acao in enumerate(ACOES):
    with cols[i % 2]:
        df_g = buscar_dados(acao, "60d")
        if not df_g.empty:
            fig = go.Figure(data=[go.Candlestick(x=df_g.index, open=df_g['open'], high=df_g['high'], low=df_g['low'], close=df_g['close'])])
            fig.update_layout(title=f"Tendência: {acao}", xaxis_rangeslider_visible=False, template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
