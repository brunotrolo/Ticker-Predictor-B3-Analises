
import streamlit as st
import pandas as pd, numpy as np
from datetime import date, timedelta
import yfinance as yf
import plotly.graph_objects as go
from b3_utils import load_b3_tickers, ensure_sa_suffix, is_known_b3_ticker, search_b3

st.set_page_config(page_title="Análise B3 Didática", page_icon="📊", layout="wide")

@st.cache_data(ttl=3600)
def fetch_data(ticker, start, end):
    df = yf.download(ensure_sa_suffix(ticker), start=start, end=end, auto_adjust=True, progress=False)
    if df.empty: return df
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    for c in ["Open","High","Low","Close","Volume"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["Close"]).reset_index()
    return df

def sma(s, w): return s.rolling(window=w, min_periods=w).mean()
def rsi(s, w=14):
    delta = s.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    ma_up = up.rolling(w).mean()
    ma_down = down.rolling(w).mean()
    rs = ma_up / ma_down.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def add_indicators(df):
    if df.empty: return df
    df = df.copy()
    df["SMA20"]=sma(df["Close"],20)
    df["RSI14"]=rsi(df["Close"])
    return df

def plot_price(df, t):
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df["Date"], open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"], name="Preço"))
    fig.add_trace(go.Scatter(x=df["Date"], y=df["SMA20"], name="SMA20"))
    fig.update_layout(title=f"{t} - Preço e SMA20", xaxis_title="Data", yaxis_title="Preço (R$)")
    st.plotly_chart(fig, use_container_width=True)

def plot_rsi(df, t):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Date"], y=df["RSI14"], name="RSI(14)"))
    fig.add_hline(y=70, line_dash="dash")
    fig.add_hline(y=30, line_dash="dash")
    fig.update_layout(title=f"{t} - RSI(14)", xaxis_title="Data", yaxis_title="RSI")
    st.plotly_chart(fig, use_container_width=True)

b3 = load_b3_tickers()
st.sidebar.header("⚙️ Configurações")
q = st.sidebar.text_input("Buscar empresa ou ticker", "")
res = search_b3(q) if q else b3
ticker = st.sidebar.selectbox("Selecione o ticker", res["ticker"])
start = st.sidebar.date_input("Início", date.today()-timedelta(days=365))
end = st.sidebar.date_input("Fim", date.today())

st.title("📊 Análise Didática de Ações da B3")
st.caption("Somente tickers da B3 (.SA) — dados do Yahoo Finance")

if not is_known_b3_ticker(ticker):
    st.error("Ticker fora da lista da B3.")
    st.stop()

with st.spinner("Baixando dados..."):
    df = fetch_data(ticker, start, end)
if df.empty:
    st.warning("Sem dados disponíveis.")
    st.stop()

df = add_indicators(df)
price = float(df["Close"].iloc[-1])
sma20 = float(df["SMA20"].iloc[-1])
rsi_val = float(df["RSI14"].iloc[-1])
delta20 = (price/sma20-1)*100 if sma20 else np.nan

c1,c2,c3 = st.columns(3)
c1.metric("Ticker", ticker)
c2.metric("Fechamento", f"R$ {price:,.2f}".replace(",", "X").replace(".", ",").replace("X","."))
c3.metric("Δ vs SMA20", f"{delta20:+.2f}%")

plot_price(df, ticker)
plot_rsi(df, ticker)

st.info("Dica: você pode colar PETR4, VALE3, ITUB4, etc. Se digitar sem .SA, a aplicação adiciona automaticamente.")

st.markdown("---")
st.subheader("🧠 Explicação simples dos resultados")

st.markdown(f"""
🪜 **1. Entendendo a SMA20 — “a linha da média”**

A **SMA20** é como a média dos últimos **20 preços de fechamento**.

Ela mostra **a direção geral do preço**:
- Se o preço está **acima da SMA20**, ele vem **subindo** — está mais forte.
- Se o preço está **abaixo da SMA20**, ele vem **caindo** — está mais fraco.

👉 No caso de **{ticker}**, o preço atual é **R$ {price:,.2f}**, cerca de **{delta20:+.2f}%** em relação à média dos últimos 20 dias.
""")

if delta20 < -5:
    st.markdown("🔴 **A ação vem caindo há várias semanas e o mercado está pessimista no curto prazo.**")
elif -5 <= delta20 <= 5:
    st.markdown("🟡 **O preço está próximo da média — o mercado está em equilíbrio.**")
else:
    st.markdown("🟢 **O preço está acima da média — o papel mostra força no curto prazo.**")

st.markdown("""
📉 É como se o preço estivesse “afastado demais da linha média”, o que pode indicar **exagero na queda** — uma corda muito esticada pra baixo.

---

⚖️ **2. Entendendo o RSI(14) — “o termômetro da força”**

O **RSI** vai de 0 a 100 e mostra **quem está dominando**: compradores ou vendedores.

| Faixa | Situação | O que significa |
|--------|-----------|----------------|
| 70 a 100 | Sobrecompra | Subiu rápido demais — pode corrigir pra baixo. |
| 50 | Neutro | Equilíbrio entre compra e venda. |
| 0 a 30 | Sobrevenda | Caiu rápido demais — pode reagir pra cima. |
""")

st.markdown(f"No caso de **{ticker}**, o RSI(14) está em **{rsi_val:.1f}**.")

if rsi_val < 30:
    st.markdown("🟢 **Está na zona de sobrevenda — o papel caiu muito e pode reagir em breve.**")
elif 30 <= rsi_val <= 70:
    st.markdown("🟡 **Está em zona neutra — o mercado está equilibrado.**")
else:
    st.markdown("🔴 **Está na zona de sobrecompra — o preço subiu demais e pode corrigir.**")

st.markdown("""
---

🧩 **3. Juntando as duas informações**

Quando o **preço está bem abaixo da SMA20** e o **RSI está perto de 30**, o mercado parece dizer:

> “Essa ação caiu bastante, está cansada de cair e pode dar um respiro em breve.”

Mas isso **não garante** que vai subir agora — é apenas um **sinal de enfraquecimento da queda**.

---

🔍 **4. Pensando em comportamento de mercado**

Imagine o gráfico assim:

```
Preço ↓↓↓↓↓
SMA20 → uma linha que ficou lá em cima
RSI ↓ até 30
```

Isso significa:
- A **queda foi rápida**
- O **preço ficou longe da média**
- E o **RSI mostra que os vendedores estão perdendo força**

💡 É o que muitos chamam de **“ponto de atenção”**:
se aparecer volume de compra nos próximos dias e o preço começar a subir,
→ pode ser **um repique** (subida temporária após muita queda).

---

💬 **Em resumo:**

| Indicador | O que está dizendo | Significado prático |
|------------|--------------------|---------------------|
| **SMA20** | O preço está bem abaixo da média dos últimos 20 dias | A ação caiu rápido; está “pressionada”. |
| **RSI(14)** | Está quase “no limite da queda” | O mercado pode começar a enxergar oportunidade. |
| **Conclusão geral** | A ação está fraca, mas pode estar perto de uma pausa ou leve recuperação | — |
""")
