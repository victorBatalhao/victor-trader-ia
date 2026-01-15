import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import requests
import datetime
import os
from sklearn.ensemble import RandomForestClassifier

# ==========================================
# 1. CONFIGURAÇÕES MESTRE (YAHOO FINANCE)
# ==========================================
# Yahoo Finance não exige token, eliminando erros de conexão
TOKEN_TELEGRAM = "8238619023:AAEcPr19DnbSpb3Ufoo6sL6ylzTRzdItp80"
CHAT_ID = "5584195780"

# Lista de ativos com sufixo .SA para a B3
ACOES = ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "KLBN11.SA", "BBAS3.SA", "TAEE11.SA"]
ARQ_CSV = "historico_victor_ia.csv"

# ==========================================
# 2. TRATAMENTO DE DADOS (CORREÇÃO DE GRÁFICOS)
# ==========================================
@st.cache_data(ttl=600)
def buscar_dados_limpos(ticker, periodo="1y"):
    try:
        # auto_adjust=True resolve problemas de escala nos gráficos
        df = yf.download(ticker, period=period, interval="1d", progress=False, auto_adjust=True)
        if df.empty:
            return pd.DataFrame()
        
        # Correção MultiIndex: Garante que as colunas sejam nomes simples strings
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        return df
    except Exception as e:
        return pd.DataFrame()

# ==========================================
# 3. INTELIGÊNCIA ARTIFICIAL
# ==========================================
def processar_ia(df):
    try:
        df = df.copy()
        df['Retorno'] = df['Close'].pct_change()
        df['Volatilidade'] = df['Retorno'].rolling(20).std()
        df['Alvo'] = (df['Close'].shift(-1) > df['Close']).astype(int)
        
        dados = df.dropna()
        X = dados[['Close', 'Retorno', 'Volatilidade']]
        y = dados['Alvo']
        
        # Modelo para prever movimento de mercado
        modelo = RandomForestClassifier(n_estimators=100, random_state=42)
        modelo.fit(X[:-1], y[:-1])
        
        pred = modelo.predict(X.tail(1))[0]
        prob = modelo.predict_proba(X.tail(1))[0]
        
        # Identificação de Perfil (Trade vs Dividendos)
        vol = df['Volatilidade'].iloc[-1]
        perfil = "💰 DIVIDENDOS (Estável)" if vol < 0.016 else "⚔️ TRADE (Oscilação)"
        status = "🚀 VALORIZAÇÃO" if pred == 1 else "📉 DEPRECIAÇÃO"
        
        return "COMPRA" if pred == 1 else "VENDA", max(prob)*100, perfil, status
    except:
        return "ERRO", 0, "N/A", "N/A"

# ==========================================
# 4. INTERFACE E COMANDOS
# ==========================================
st.set_page_config(page_title="Victor Trader IA v6.5", layout="wide", page_icon="🤖")

# Barra Lateral de Status Real-Time
st.sidebar.title("📡 Conexão B3 (Yahoo)")
for acao in ACOES:
    d_check = buscar_dados_limpos(acao, "1d")
    if not d_check.empty:
        st.sidebar.success(f"{acao}: Online")
    else:
        st.sidebar.error(f"{acao}: Falha")

st.title("🚀 Victor Trader IA – Sistema Mestre")
st.markdown("Monitoramento automático para Trade e Dividendos.")

if st.button("📡 EXECUTAR ANÁLISE COMPLETA E NOTIFICAR TELEGRAM", use_container_width=True):
    relatorio = f"🤖 **VICTOR TRADER IA v6.5**\n📅 {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
    tem_sucesso = False
    
    for acao in ACOES:
        df = buscar_dados_limpos(acao)
        if not df.empty:
            tem_sucesso = True
            sinal, conf, perfil, tend = processar_ia(df)
            preco = float(df['Close'].iloc[-1])
            
            # Montagem da mensagem formatada para Telegram
            relatorio += f"\n📊 **{acao}** | R$ {preco:.2f}"
            relatorio += f"\n👉 SINAL: {sinal} ({conf:.1f}%)"
            relatorio += f"\n🎯 MODO: {perfil} | {tend}\n"
            
            # Salva no banco de dados CSV local
            pd.DataFrame([[datetime.datetime.now(), acao, preco, sinal, perfil]], 
                         columns=["Data","Ativo","Preco","Sinal","Perfil"]).to_csv(ARQ_CSV, mode='a', header=not os.path.exists(ARQ_CSV), index=False)
    
    if tem_sucesso:
        # Envio direto via API do Telegram
        requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage", 
                      data={'chat_id': CHAT_ID, 'text': relatorio, 'parse_mode': 'Markdown'})
        st.success("✅ Relatório enviado com sucesso!")
    else:
        st.error("❌ Erro ao coletar dados do Yahoo Finance.")

# ==========================================
# 5. GRÁFICOS E HISTÓRICO (EXIBIÇÃO)
# ==========================================
st.divider()

# Download do Histórico
if os.path.exists(ARQ_CSV):
    df_h = pd.read_csv(ARQ_CSV)
    st.subheader("📥 Exportar Relatórios")
    st.download_button("Baixar Histórico Completo (CSV)", df_h.to_csv(index=False), "historico_ia.csv", "text/csv")

st.divider()

# Grid de Gráficos de Candlestick
st.subheader("📈 Visualização Técnica (Últimos 60 Dias)")
col1, col2 = st.columns(2)
for i, acao in enumerate(ACOES):
    with col1 if i % 2 == 0 else col2:
        df_g = buscar_dados_limpos(acao, "60d")
        if not df_g.empty:
            # Renderização do gráfico Plotly corrigido
            fig = go.Figure(data=[go.Candlestick(
                x=df_g.index,
                open=df_g['Open'],
                high=df_g['High'],
                low=df_g['Low'],
                close=df_g['Close']
            )])
            fig.update_layout(title=f"Tendência: {acao}", xaxis_rangeslider_visible=False, template="plotly_dark", height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"⚠️ {acao}: Sem dados para exibir gráfico.")