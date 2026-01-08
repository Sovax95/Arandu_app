import streamlit as st
import requests
import pandas as pd
from textblob import TextBlob
import yfinance as yf
from datetime import datetime
import pytz
import plotly.graph_objects as go
import plotly.express as px
import feedparser

# --- 1. CONFIGURAÇÃO DA PÁGINA & CSS HACKING ---
st.set_page_config(
    page_title="Arandu | Market Intelligence",
    page_icon="🦉💹",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .stApp {
        background-color: #0E1117;
        font-family: 'Inter', sans-serif;
    }
   
    div[data-testid="metric-container"] {
        background-color: #161B22;
        border: 1px solid #30363D;
        padding: 15px;
        border-radius: 10px;
        color: #C9D1D9;
        transition: transform 0.2s;
    }
    div[data-testid="metric-container"]:hover {
        border-color: #58A6FF;
        transform: scale(1.02);
    }
   
    .gradient-text {
        background: -webkit-linear-gradient(45deg, #00C9FF, #92FE9D);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 3em;
    }
   
    section[data-testid="stSidebar"] {
        background-color: #0d1117;
    }
   
    .stTextInput input {
        background-color: #0d1117;
        color: #c9d1d9;
        border: 1px solid #30363D;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. FUNÇÕES DE INTELIGÊNCIA ---
@st.cache_data(ttl=3600)
def get_news(api_key):
    if not api_key:
        return []
    url = f"https://newsapi.org/v2/top-headlines?category=business&language=en&apiKey={api_key}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if data.get("status") == "ok":
            return data["articles"][:8]
    except:
        return []
    return []

@st.cache_data(ttl=600)
def get_rss_economia_popular():
    feeds = [
        "https://www.infomoney.com.br/feed/",
        "https://economia.uol.com.br/ultnot/index.rss",
        "https://agenciabrasil.ebc.com.br/economia/rss"
    ]
    entries = []
    for feed_url in feeds:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:5]:
                entries.append({
                    'title': entry.title,
                    'summary': entry.get('summary', 'Sem descrição'),
                    'link': entry.link,
                    'source': feed.feed.get('title', 'Fonte RSS')
                })
        except:
            continue
    seen = set()
    unique_entries = []
    for e in entries:
        if e['title'] not in seen:
            unique_entries.append(e)
            seen.add(e['title'])
        if len(unique_entries) >= 8:
            break
    return unique_entries

@st.cache_data(ttl=300)
def get_market_data():
    tickers = {"S&P 500": "^GSPC", "Bitcoin": "BTC-USD", "Ouro": "GC=F", "Ibovespa": "^BVSP"}
    metrics = {}
    history_df = pd.DataFrame()
   
    try:
        btc = yf.Ticker("BTC-USD")
        history_df = btc.history(period="1mo", interval="1d")
        if history_df.empty:
            st.warning("No Bitcoin chart data available at the moment.")
    except Exception:
        st.error("Error fetching Bitcoin chart data.")
        history_df = pd.DataFrame()

    try:
        for name, ticker in tickers.items():
            stock = yf.Ticker(ticker)
            hist = stock.history(period="5d")
            if len(hist) >= 2:
                current = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2]
                delta = ((current - prev) / prev) * 100
                metrics[name] = (round(current, 2), round(delta, 2))
            else:
                metrics[name] = ("N/A", 0.0)
    except Exception:
        st.error("Error fetching market metrics.")
    
    return metrics, history_df

def analyze_sentiment_nlp(text):
    if not text:
        return 0
    return TextBlob(text).sentiment.polarity

def get_solar_session():
    now = datetime.now(pytz.timezone('America/Sao_Paulo'))
    hour = now.hour
    if 5 <= hour < 12:
        return "ASIA SESSION", "Consolidation", "🌏"
    elif 12 <= hour < 19:
        return "LONDON + NY OVERLAP", "High Volatility", "🏰🗽"
    elif 19 <= hour < 22:
        return "NY SESSION", "Closing Moves", "🗽"
    else:
        return "AFTER HOURS", "Low Liquidity", "🌑"

# --- 3. COMPONENTES VISUAIS ---
def render_chart(df):
    if df.empty:
        return
   
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['Close'],
        mode='lines',
        name='Bitcoin',
        line=dict(color='#00C9FF', width=2),
        fill='tozeroy',
        fillcolor='rgba(0, 201, 255, 0.1)'
    ))
   
    fig.update_layout(
        title="BTC-USD | Trend (30D)",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#C9D1D9'),
        margin=dict(l=0, r=0, t=30, b=0),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='#30363D')
    )
    st.plotly_chart(fig, use_container_width=True)

def main():
    with st.sidebar:
        st.caption("SYSTEM CONFIG")
        api_key = st.text_input("NewsAPI Key", type="password")
        st.divider()
        st.markdown("Developed by **Arandu Labs**")

    col_logo, col_status = st.columns([2, 1])
    with col_logo:
        st.markdown('<h1 class="gradient-text">ARANDU OS</h1>', unsafe_allow_html=True)
        st.caption("AI-DRIVEN MARKET SENTIMENT ANALYZER")
       
    session_name, session_desc, session_icon = get_solar_session()
    now_br = datetime.now(pytz.timezone('America/Sao_Paulo'))
    with col_status:
        st.info(f"**{session_icon} {session_name}**\n\nMode: {session_desc}")
        st.caption(f"Last update: {now_br.strftime('%H:%M:%S %Z')}")

    st.markdown("---")

    metrics, history_df = get_market_data()
   
    if metrics:
        c1, c2, c3, c4 = st.columns(4)
        cols = [c1, c2, c3, c4]
        for idx, (name, (price, delta)) in enumerate(metrics.items()):
            with cols[idx]:
                if price == "N/A":
                    st.metric(name, "N/A", "0%")
                else:
                    value_str = f"${price:,.2f}" if name in ["Bitcoin", "Ouro"] else f"{price:,.0f}"
                    st.metric(
                        label=name,
                        value=value_str,
                        delta=f"{delta:+.2f}%",
                        delta_color="normal"
                    )
    else:
        st.warning("Connecting to Market Data Feeds...")

    st.markdown("<br>", unsafe_allow_html=True)
   
    col_chart, col_oracle = st.columns([2, 1])
   
    with col_chart:
        st.subheader("Market Trend")
        if not history_df.empty:
            render_chart(history_df)
        else:
            st.write("Loading Chart Data...")

    with col_oracle:
        st.subheader("Arandu Verdict")
        sentiment_display = 0
        news = []
        
        if api_key:
            news = get_news(api_key)
            if news:
                sentiment_display = sum(analyze_sentiment_nlp(n['title']) for n in news) / len(news)
       
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=sentiment_display,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "News-Based Sentiment Score"},
            gauge={
                'axis': {'range': [-1, 1], 'tickcolor': "white"},
                'bar': {'color': "#00C9FF"},
                'steps': [
                    {'range': [-1, -0.1], 'color': "#ff2b2b"},
                    {'range': [-0.1, 0.1], 'color': "#30363D"},
                    {'range': [0.1, 1], 'color': "#00ff7f"}
                ],
            }
        ))
        fig_gauge.update_layout(
            height=250,
            margin=dict(l=10, r=10, t=50, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
            font={'color': "white"}
        )
        st.plotly_chart(fig_gauge, use_container_width=True)
       
        # <<< ALTERADO PARA EVITAR TOM DE RECOMENDAÇÃO >>>
        if sentiment_display > 0.1:
            st.success("MARKET SENTIMENT SIGNAL: **BULLISH**")
        elif sentiment_display < -0.1:
            st.error("MARKET SENTIMENT SIGNAL: **BEARISH**")
        else:
            st.warning("MARKET SENTIMENT SIGNAL: **NEUTRAL**")

    st.markdown("---")
    st.subheader("Intelligence Feed")
   
    if api_key and news:
        for i in range(0, len(news), 2):
            row_c1, row_c2 = st.columns(2)
           
            if i < len(news):
                with row_c1:
                    sent = analyze_sentiment_nlp(news[i]['title'])
                    emoji = "🟢" if sent > 0 else "🔴" if sent < 0 else "⚪"
                    with st.expander(f"{emoji} {news[i]['title']}", expanded=False):
                        st.caption(news[i]['source']['name'])
                        st.write(news[i]['description'] or "No description available.")
           
            if i + 1 < len(news):
                with row_c2:
                    sent = analyze_sentiment_nlp(news[i+1]['title'])
                    emoji = "🟢" if sent > 0 else "🔴" if sent < 0 else "⚪"
                    with st.expander(f"{emoji} {news[i+1]['title']}", expanded=False):
                        st.caption(news[i+1]['source']['name'])
                        st.write(news[i+1]['description'] or "No description available.")
    else:
        st.info("🔑 Insira sua chave da NewsAPI.org para ativar o Intelligence Feed")
        st.markdown("""
        Cadastre-se gratuitamente em [newsapi.org](https://newsapi.org/register)  
        (plano free permite 100 requests/dia)
        """)

    st.markdown("---")
    st.subheader("💰 Dicas de Economia Popular & Finanças Pessoais")

    rss_news = get_rss_economia_popular()
    
    if rss_news:
        for i in range(0, len(rss_news), 2):
            row_c1, row_c2 = st.columns(2)
            
            if i < len(rss_news):
                with row_c1:
                    item = rss_news[i]
                    sent = analyze_sentiment_nlp(item['title'])
                    emoji = "🟢" if sent > 0 else "🔴" if sent < 0 else "⚪"
                    with st.expander(f"{emoji} {item['title']}", expanded=False):
                        st.caption(item['source'])
                        st.write(item['summary'][:500] + "..." if len(item['summary']) > 500 else item['summary'])
                        st.markdown(f"[Ler mais]({item['link']})")
            
            if i + 1 < len(rss_news):
                with row_c2:
                    item = rss_news[i+1]
                    sent = analyze_sentiment_nlp(item['title'])
                    emoji = "🟢" if sent > 0 else "🔴" if sent < 0 else "⚪"
                    with st.expander(f"{emoji} {item['title']}", expanded=False):
                        st.caption(item['source'])
                        st.write(item['summary'][:500] + "..." if len(item['summary']) > 500 else item['summary'])
                        st.markdown(f"[Ler mais]({item['link']})")
    else:
        st.info("Carregando dicas de economia popular... (RSS gratuito)")

if __name__ == "__main__":
    main()
