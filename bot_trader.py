import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
from sklearn.ensemble import RandomForestClassifier

# --- CONFIGURAÇÕES DO VICTOR ---
TOKEN_TELEGRAM = "8238619023:AAEcPr19DnbSpb3Ufoo6sL6ylzTRzdItp80"
CHAT_ID = "5584195780"
ACOES_TRADE = ["PETR4.SA", "VALE3.SA", "ITUB4.SA"]
ACOES_DIVIDENDOS = ["KLBN11.SA", "BBAS3.SA", "TAEE11.SA"]

def obter_investidor10(ticker):
    url = f"https://investidor10.com.br/acoes/{ticker.lower().replace('.sa', '')}/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        indicadores = {}
        cards = soup.find_all('div', class_='_card-body')
        for card in cards[:5]:
            titulo = card.find('span').text.strip()
            valor = card.find('div', class_='_card-value').text.strip()
            indicadores[titulo] = valor
        return indicadores
    except: return None

# --- AQUI ENTRA A SUA NOVA FUNÇÃO ---
def analisar_cenario(ticker, previsao, prob, variação_dia, fundamentos):
    if previsao == 0: 
        if variação_dia > 0:
            motivo = "🚀 *Maximizar Lucros:* A ação subiu hoje, mas a IA detectou perda de força. Venda agora para garantir o lucro no topo."
        else:
            motivo = "📉 *Minimizar Perdas:* A ação já está caindo e a tendência é piorar. Venda para evitar um prejuízo maior."
    else: 
        motivo = "✅ *Oportunidade:* Indicadores sugerem que o preço está atrativo para entrada ou reforço de posição."

    if prob > 85:
        proximos_dias = "🔥 *Forte Tendência:* O movimento deve se intensificar nos próximos 3 a 5 dias."
    elif prob > 60:
        proximos_dias = "⚖️ *Volatilidade:* Mercado indeciso, espere oscilações curtas."
    else:
        proximos_dias = "⚠️ *Atenção:* Mudança de tendência à vista. O cenário pode inverter."

    msg = f"📊 *ANÁLISE: {ticker}*\n"
    msg += f"👉 *RECOMENDAÇÃO:* {'🟢 COMPRA' if previsao == 1 else '🔴 VENDA'}\n"
    msg += f"💡 *PORQUÊ:* {motivo}\n"
    msg += f"🔮 *PRÓXIMOS DIAS:* {proximos_dias}\n"
    if fundamentos:
        msg += f"📋 *P/L:* {fundamentos.get('P/L','-')} | *DY:* {fundamentos.get('DY','-')}\n"
    return msg + "\n"

def executar_analise_total():
    todas = ACOES_TRADE + ACOES_DIVIDENDOS
    dados = yf.download(todas + ['BZ=F', 'USDBRL=X'], period="2y", interval="1d", progress=False)['Close']
    
    relatorio_completo = ""
    melhor_confianca, melhor_acao = 0, ""

    for ticker in todas:
        df = pd.DataFrame()
        df['Retorno'] = dados[ticker].pct_change()
        df['Brent'] = dados['BZ=F'].pct_change()
        df['Dolar'] = dados['USDBRL=X'].pct_change()
        df['Alvo'] = (dados[ticker].shift(-1) > dados[ticker]).astype(int)
        df = df.dropna()

        X, y = df[['Retorno', 'Brent', 'Dolar']], df['Alvo']
        modelo = RandomForestClassifier(n_estimators=100).fit(X, y)
        
        prob = max(modelo.predict_proba(X.tail(1))[0]) * 100
        previsao = modelo.predict(X.tail(1))[0]
        
        # Cálculo da variação do dia para a sua nova lógica
        preco_hoje = dados[ticker].iloc[-1]
        preco_ontem = dados[ticker].iloc[-2]
        variacao = ((preco_hoje - preco_ontem) / preco_ontem) * 100
        
        fundamentos = obter_investidor10(ticker)
        
        # CHAMADA DA SUA NOVA FUNÇÃO AQUI:
        relatorio_completo += analisar_cenario(ticker, previsao, prob, variacao, fundamentos)

        if prob > melhor_confianca:
            melhor_confianca, melhor_acao = prob, ticker

    final_msg = f"🏆 *MELHOR ESCOLHA: {melhor_acao}* ({melhor_confianca:.1f}%)\n\n" + relatorio_completo
    requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage", data={'chat_id': CHAT_ID, 'text': final_msg, 'parse_mode': 'Markdown'})