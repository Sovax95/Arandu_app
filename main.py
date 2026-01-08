import streamlit as st
import requests
import pandas as pd
from textblob import TextBlob
import yfinance as yf
from datetime import datetime
import pytz
import plotly.graph_objects as go
import plotly.express as px

# --- 1. CONFIGURAÇÃO DA PÁGINA & CSS HACKING ---
st.set_page_config(
    page_title="Arandu | Market Intelligence",
    page_icon="🦉",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS Customizado para o "Look" Startup Dark Mode
st.markdown("""
<style>
    /* Fundo geral e fontes */
    .stApp {
        background-color: #0E1117;
        font-family: 'Inter', sans-serif;
    }
    
    /* Cards de Métricas */
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
    
    /* Títulos com Gradiente (Efeito Cyberpunk) */
    .gradient-text {
        background: -webkit-linear-gradient(45deg, #00C9FF, #92FE9D);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 3em;
    }
    
    /* Barra lateral */
    section[data-testid="stSidebar"] {
        background-color: #0d1117;
    }
    
    /* Botões e Inputs */
    .stTextInput input {
        background-color: #0d1117;
        color: #c9d1d9;
        border: 1px solid #30363D;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. FUNÇÕES DE INTELIGÊNCIA (BACKEND MANTIDO) ---

@st.cache_data(ttl=3600)
def get_news(api_key):
    if not api_key: return []
    url = f"https://newsapi.org/v2/top-headlines?category=business&language=en&apiKey={api_key}"
    try:
        response = requests.get(url)
        data = response.json()
        if data.get("status") == "ok": return data["articles"][:8]
    except: return []
    return []

@st.cache_data(ttl=300)
def get_market_data():
    # Agora retorna também o histórico para o gráfico
    tickers = {"S&P 500": "^GSPC", "Bitcoin": "BTC-USD", "Ouro": "GC=F", "Ibovespa": "^BVSP"}
    metrics = {}
    history_df = pd.DataFrame()
    
    try:
        # Pegar dados de histórico do Bitcoin para o gráfico principal
        btc = yf.Ticker("BTC-USD")
        history_df = btc.history(period="1mo") # Último mês
        
        # Pegar métricas pontuais
        for name, ticker in tickers.items():
            stock = yf.Ticker(ticker)
            hist = stock.history(period="2d")
            if len(hist) >= 1:
                current = hist['Close'].iloc[-1]
                prev = hist['Open'].iloc[-1]
                delta = ((current - prev) / prev) * 100
                metrics[name] = (current, delta)
    except: pass
    
    return metrics, history_df

def analyze_sentiment_nlp(text):
    if not text: return 0
    return TextBlob(text).sentiment.polarity

def get_solar_session():
    now = datetime.now(pytz.timezone('UTC'))
    hour = now.hour
    if 0 <= hour < 7: return "ASIA SESSION", "Stabilization", "🌏"
    elif 7 <= hour < 14: return "LONDON SESSION", "Volatility", "🏰"
    elif 14 <= hour < 21: return "NY SESSION", "High Volume", "🗽"
    else: return "AFTER MARKET", "Low Liquidity", "🌑"

# --- 3. COMPONENTES VISUAIS (FRONTEND PRO) ---

def render_chart(df):
    """Cria um gráfico de linha estilo Financeiro com Plotly"""
    if df.empty: return
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index, y=df['Close'],
        mode='lines',
        name='Bitcoin',
        line=dict(color='#00C9FF', width=2),
        fill='tozeroy', # Preenchimento gradiente abaixo da linha
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
    # Sidebar Minimalista
    with st.sidebar:
        st.caption("SYSTEM CONFIG")
        api_key = st.text_input("NewsAPI Key", type="password")
        st.divider()
        st.markdown("Developed by **Arandu Labs**")

    # Header Section
    col_logo, col_status = st.columns([2, 1])
    with col_logo:
        st.markdown('<h1 class="gradient-text">ARANDU OS</h1>', unsafe_allow_html=True)
        st.caption("AI-DRIVEN MARKET SENTIMENT ANALYZER")
        
    session_name, session_desc, session_icon = get_solar_session()
    with col_status:
        st.info(f"**{session_icon} {session_name}**\n\nMode: {session_desc}")

    st.markdown("---")

    # 1. KPI ROW (Métricas em Cards)
    metrics, history_df = get_market_data()
    
    if metrics:
        c1, c2, c3, c4 = st.columns(4)
        cols = [c1, c2, c3, c4]
        for idx, (name, (price, delta)) in enumerate(metrics.items()):
            with cols[idx]:
                st.metric(name, f"{price:,.0f}", f"{delta:.2f}%")
    else:
        st.warning("Connecting to Market Data Feeds...")

    # 2. MAIN GRID (Gráfico + Oráculo)
    st.markdown("<br>", unsafe_allow_html=True) # Espaçamento
    
    col_chart, col_oracle = st.columns([2, 1])
    
    with col_chart:
        st.subheader("Market Trend")
        if not history_df.empty:
            render_chart(history_df)
        else:
            st.write("Loading Chart Data...")

    with col_oracle:
        st.subheader("Arandu Verdict")
        # Lógica do Oráculo visual
        sentiment_display = 0
        if api_key:
            news = get_news(api_key)
            if news:
                sentiment_display = sum([analyze_sentiment_nlp(n['title']) for n in news]) / len(news)
        
        # Display do "Velocímetro" de Sentimento
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = sentiment_display,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Global Sentiment (NLP)"},
            gauge = {
                'axis': {'range': [-1, 1], 'tickcolor': "white"},
                'bar': {'color': "#00C9FF"},
                'steps': [
                    {'range': [-1, -0.1], 'color': "#ff2b2b"},
                    {'range': [-0.1, 0.1], 'color': "#30363D"},
                    {'range': [0.1, 1], 'color': "#00ff7f"}],
            }
        ))
        fig_gauge.update_layout(height=250, margin=dict(l=10, r=10, t=50, b=10), paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"})
        st.plotly_chart(fig_gauge, use_container_width=True)
        
        # Texto de decisão
        if sentiment_display > 0.1:
            st.success("RECOMMENDATION: **AGGRESSIVE GROWTH**")
        elif sentiment_display < -0.1:
            st.error("RECOMMENDATION: **CAPITAL PRESERVATION**")
        else:
            st.warning("RECOMMENDATION: **WAIT & OBSERVE**")

    # 3. NEWS FEED (Cards Estilizados)
    st.markdown("---")
    st.subheader("Intelligence Feed")
    
    if api_key and news:
        for i in range(0, len(news), 2): # Loop para criar linhas de 2 em 2
            row_c1, row_c2 = st.columns(2)
            
            # Artigo 1
            if i < len(news):
                with row_c1:
                    sent = analyze_sentiment_nlp(news[i]['title'])
                    emoji = "🟢" if sent > 0 else "🔴" if sent < 0 else "⚪"
                    with st.expander(f"{emoji} {news[i]['title']}", expanded=False):
                        st.caption(news[i]['source']['name'])
                        st.write(news[i]['description'])
            
            # Artigo 2
            if i + 1 < len(news):
                with row_c2:
                    sent = analyze_sentiment_nlp(news[i+1]['title'])
                    emoji = "🟢" if sent > 0 else "🔴" if sent < 0 else "⚪"
                    with st.expander(f"{emoji} {news[i+1]['title']}", expanded=False):
                        st.caption(news[i+1]['source']['name'])
                        st.write(news[i+1]['description'])
    elif not api_key:
        st.info("🔒 Enter API Key to unlock News Intelligence")

if __name__ == "__main__":
    main()