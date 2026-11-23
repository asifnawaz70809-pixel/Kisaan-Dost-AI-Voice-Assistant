import streamlit as st
import hashlib
import os
import io
from openai import OpenAI
from gtts import gTTS
import hashlib
import hashlib

# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(
    page_title="Kisaan Dost — AI Voice Assistant",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === KISAAN DOST DYNAMIC FRESH FASAL & FEATURE-SPECIFIC THEME ENGINE ===
_active_pg = st.session_state.get("page", "?? Home")
_page_palettes = {
    "?? Home": ("#05241b", "#0b3d2e", "#10b981", "#fbbf24", "rgba(16, 185, 129, 0.35)"),
    "?? Voice Chat": ("#06261d", "#0e4434", "#34d399", "#fde047", "rgba(52, 211, 153, 0.40)"),
    "?? Disease Check": ("#04231f", "#0a3f38", "#2dd4bf", "#a3e635", "rgba(45, 212, 191, 0.40)"),
    "?? Mandi Rates": ("#1c1908", "#2e270b", "#f59e0b", "#34d399", "rgba(245, 158, 11, 0.40)"),
    "?? Schemes": ("#072129", "#0d3847", "#38bdf8", "#fbbf24", "rgba(56, 189, 248, 0.40)"),
    "?? Weather": ("#061f2e", "#0c354d", "#0ea5e9", "#fde047", "rgba(14, 165, 233, 0.40)"),
}
_bg1, _bg2, _accent1, _accent2, _border_glow = _page_palettes.get(
    _active_pg, ("#05241b", "#0b3d2e", "#10b981", "#fbbf24", "rgba(16, 185, 129, 0.35)")
)

st.markdown(f"""
<style>


.stApp {{
    background: radial-gradient(circle at top right, {_bg2} 0%, {_bg1} 55%, #031711 100%) !important;
    color: #f0fdf4 !important;
    font-family: 'Plus Jakarta Sans', sans-serif;
}}
[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #041d16 0%, #083326 60%, #052219 100%) !important;
    border-right: 1px solid rgba(52, 211, 153, 0.25) !important;
}}
[data-testid="stSidebar"] * {{
    color: #ecfdf5 !important;
}}
[data-testid="stMain"] h1, [data-testid="stMain"] h2, [data-testid="stMain"] h3 {{
    background: linear-gradient(90deg, #ffffff 0%, {_accent1} 55%, {_accent2} 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 800 !important;
}}
[data-testid="stMain"] p, [data-testid="stMain"] label, [data-testid="stMain"] span {{
    color: #ecfdf5 !important;
}}
[data-testid="stMain"] div.stButton > button {{
    background: linear-gradient(135deg, {_accent1} 0%, #059669 100%) !important;
    color: #ffffff !important;
    border: 1px solid {_border_glow} !important;
    border-radius: 14px !important;
    font-weight: 700 !important;
    padding: 10px 18px !important;
    box-shadow: 0 6px 20px rgba(4, 24, 18, 0.45) !important;
    transition: all 0.22s ease !important;
}}
[data-testid="stMain"] div.stButton > button:hover {{
    transform: translateY(-2px) !important;
    border-color: {_accent2} !important;
    box-shadow: 0 10px 26px {_border_glow} !important;
}}
[data-testid="stMetric"] {{
    background: linear-gradient(135deg, rgba(10, 56, 42, 0.72), rgba(5, 32, 24, 0.85)) !important;
    border: 1px solid {_border_glow} !important;
    border-radius: 16px !important;
    padding: 14px 18px !important;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3) !important;
}}
</style>
""", unsafe_allow_html=True)



# Groq Client Setup
api_key = (st.secrets.get("GROQ_API_KEY") if "GROQ_API_KEY" in st.secrets else os.getenv("GROQ_API_KEY")) or "gsk_placeholder"
client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=api_key)

# URL Params se Page Check karo (Clickable Cards ke liye)
query_params = st.query_params
if "page" in query_params:
    st.session_state.page = query_params["page"]
elif "page" not in st.session_state:
    st.session_state.page = "🏠 Home"

# Sidebar Navigation
nav_options = ["🏠 Home", "🎤 Voice Chat", "🔬 Disease Check", "📊 Mandi Rates", "📋 Schemes", "📴 Offline Mode", "🌤 Weather"]
try:
    default_index = nav_options.index(st.session_state.page)
except ValueError:
    default_index = 0

# ============================================
# COLOURFUL CUSTOM CSS
# ============================================
st.markdown("""
<style>
    
    
    .stApp { background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #07291f 100%); color: white; }
    [data-testid="stSidebar"] { background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(10px); border-right: 1px solid rgba(255, 255, 255, 0.1); }
    [data-testid="stSidebar"] * { color: white !important; }
    h1, h2, h3 { color: #FDE047; font-weight: 700; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
    
    .hero-section {
        background: linear-gradient(135deg, #ec4899 0%, #059669 50%, #3b82f6 100%);
        padding: 4rem 2rem; border-radius: 24px; text-align: center;
        box-shadow: 0 0 40px rgba(236, 72, 153, 0.4); margin-bottom: 2rem;
        border: 1px solid rgba(255,255,255,0.2);
    }
    .hero-section h1 { color: white; font-size: 4rem; margin-bottom: 0.5rem; text-shadow: 0 0 20px rgba(255,255,255,0.5); }
    .hero-section p { color: #FDF2F8; font-size: 1.5rem; }
    
    /* Action Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%);
        color: white; border: none; border-radius: 12px;
        padding: 0.8rem 2rem; font-weight: 700; font-size: 1.1rem;
        box-shadow: 0 0 20px rgba(245, 158, 11, 0.5);
    }
    .stButton > button:hover { box-shadow: 0 0 30px rgba(245, 158, 11, 0.8); transform: translateY(-2px); }
    
    /* Urdu Text */
    .urdu-text {
        direction: rtl; text-align: right; font-family: 'Noto Nastaliq Urdu', sans-serif; 
        font-size: 1.2rem; line-height: 2.2; background: rgba(255, 255, 255, 0.1); 
        padding: 25px; border-radius: 16px; border-right: 6px solid #FDE047;
        color: #FDF2F8; margin-top: 15px; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3); backdrop-filter: blur(10px);
    }

    /* Home Cards (HTML Links) */
    .home-card {
        display: block; background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 20px;
        padding: 2rem; text-align: center; text-decoration: none !important;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        transition: all 0.4s ease; height: 100%; margin-bottom: 1rem;
    }
    .home-card:hover {
        transform: translateY(-10px) scale(1.02); box-shadow: 0 0 30px rgba(236, 72, 153, 0.6);
        border-color: #ec4899; background: rgba(255, 255, 255, 0.15);
    }
    .home-card-icon { font-size: 4rem; display: block; margin-bottom: 15px; }
    .home-card-title { font-size: 1.3rem; font-weight: 600; color: #FDE047; display: block; margin-bottom: 5px; }
    .home-card-desc { font-size: 0.9rem; color: #E0E7FF; display: block; }

    .footer { text-align: center; color: #6ee7b7; padding: 2rem; margin-top: 3rem; border-top: 1px solid rgba(255,255,255,0.1); }
</style>
""", unsafe_allow_html=True)

# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    st.markdown('<h1 style="text-align: center; font-size: 4rem; margin-bottom: 0; text-shadow: 0 0 20px #FDE047;">🌾</h1>', unsafe_allow_html=True)
    st.markdown('<h3 style="text-align: center; color: white; margin-top: 0;">Kisaan Dost</h3>', unsafe_allow_html=True)
    
    selected_page = st.radio("Navigation", nav_options, index=default_index, label_visibility="collapsed")
    
    # Agar sidebar se change kiya toh URL param update karo
    if selected_page != st.session_state.page:
        st.session_state.page = selected_page
        st.query_params["page"] = selected_page
    
    st.markdown("---")
    st.markdown('<p style="font-size: 0.9rem; text-align: center; color: #6ee7b7;">👨‍💻 Developer: Asif Nawaz<br>🎓 FYP 2026</p>', unsafe_allow_html=True)

# ============================================
# PAGE: HOME
# ============================================
if st.session_state.page == "🏠 Home":
    st.markdown("""
    <div class="hero-section">
        <h1>Kisaan Dost</h1>
        <p>AI Voice Assistant For Farmers</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<h2 style='text-align: center; margin-bottom: 2rem; color: white;'>Explore Features</h2>", unsafe_allow_html=True)
    
    # HTML Links (In par click karne se page turant change hoga)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <a href="?page=🎤+Voice+Chat" target="_self" class="home-card">
            <span class="home-card-icon">🎤</span>
            <span class="home-card-title">Voice Assistant</span>
            <span class="home-card-desc">Talk in Urdu</span>
        </a>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <a href="?page=🔬+Disease+Check" target="_self" class="home-card">
            <span class="home-card-icon">🔬</span>
            <span class="home-card-title">Disease Check</span>
            <span class="home-card-desc">Upload crop photo</span>
        </a>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <a href="?page=📊+Mandi+Rates" target="_self" class="home-card">
            <span class="home-card-icon">📊</span>
            <span class="home-card-title">Mandi Rates</span>
            <span class="home-card-desc">Check live prices</span>
        </a>
        """, unsafe_allow_html=True)
            
    st.write("")
    col4, col5, col6 = st.columns(3)
    with col4:
        st.markdown("""
        <a href="?page=📋+Schemes" target="_self" class="home-card">
            <span class="home-card-icon">📋</span>
            <span class="home-card-title">Govt Schemes</span>
            <span class="home-card-desc">Find subsidies</span>
        </a>
        """, unsafe_allow_html=True)
    with col5:
        st.markdown("""
        <a href="?page=🌤+Weather" target="_self" class="home-card">
            <span class="home-card-icon">🌤</span>
            <span class="home-card-title">Weather Alerts</span>
            <span class="home-card-desc">Plan your farming</span>
        </a>
        """, unsafe_allow_html=True)
    with col6:
        st.markdown("""
        <a href="?page=Offline" target="_self" class="home-card">
            <span class="home-card-icon">📱</span>
            <span class="home-card-title">Offline Mode</span>
            <span class="home-card-desc">Open Offline Toolkit</span>
        </a>
        """, unsafe_allow_html=True)

# ============================================
# PAGE: VOICE CHAT
# ============================================
elif st.session_state.page == "🎤 Voice Chat":
    from utils.voice_utils import process_voice_pipeline, get_urdu_ai_response, synthesize_urdu_speech
    # =========================================================================
    # KISAAN DOST — AURORA AGRI-TECH GLASSMORPHISM VOICE STUDIO UI
    # Scoped to [data-testid="stMain"] so sidebar styling stays 100% intact
    # =========================================================================
    st.markdown(
        """
        <style>
        

        /* Hero Studio Banner with Vibrant Aurora Border */
        .kd-studio-hero {
            position: relative;
            background: linear-gradient(135deg, rgba(8, 48, 36, 0.85) 0%, rgba(19, 46, 68, 0.82) 55%, rgba(28, 16, 62, 0.90) 100%);
            backdrop-filter: blur(18px);
            -webkit-backdrop-filter: blur(18px);
            border: 1.5px solid rgba(52, 211, 153, 0.42);
            border-radius: 22px;
            padding: 24px 28px;
            margin-bottom: 20px;
            box-shadow: 0 12px 40px rgba(8, 4, 24, 0.55), inset 0 1px 0 rgba(255, 255, 255, 0.15);
            overflow: hidden;
        }
        .kd-studio-hero::before {
            content: "";
            position: absolute;
            top: -50%;
            right: -15%;
            width: 320px;
            height: 320px;
            background: radial-gradient(circle, rgba(16, 185, 129, 0.24) 0%, transparent 70%);
            pointer-events: none;
        }
        .kd-studio-hero::after {
            content: "";
            position: absolute;
            bottom: -55%;
            left: -10%;
            width: 300px;
            height: 300px;
            background: radial-gradient(circle, rgba(236, 72, 153, 0.22) 0%, transparent 70%);
            pointer-events: none;
        }
        .kd-hero-title {
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-size: 1.75rem;
            font-weight: 800;
            background: linear-gradient(90deg, #ffffff 0%, #6ee7b7 50%, #fde047 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 0;
            line-height: 1.3;
        }
        .kd-hero-sub {
            color: #e2d9f3;
            font-size: 0.95rem;
            margin: 6px 0 0 0;
        }

        /* Animated Equalizer Soundwave Bars */
        .kd-wave-box {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            height: 26px;
            padding: 6px 12px;
            background: rgba(16, 185, 129, 0.16);
            border: 1px solid rgba(52, 211, 153, 0.45);
            border-radius: 999px;
        }
        .kd-wave-bar {
            width: 3.5px;
            height: 10px;
            border-radius: 4px;
            background: linear-gradient(180deg, #34d399, #fbbf24);
            animation: kdPulseWave 1.15s ease-in-out infinite;
        }
        .kd-wave-bar:nth-child(2) { animation-delay: 0.15s; height: 16px; }
        .kd-wave-bar:nth-child(3) { animation-delay: 0.30s; height: 20px; }
        .kd-wave-bar:nth-child(4) { animation-delay: 0.45s; height: 14px; }
        .kd-wave-bar:nth-child(5) { animation-delay: 0.60s; height: 18px; }
        @keyframes kdPulseWave {
            0%, 100% { transform: scaleY(0.45); opacity: 0.7; }
            50% { transform: scaleY(1.15); opacity: 1; }
        }

        /* Tech Stack Glowing Pills */
        .kd-pill-row {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 14px;
        }
        .kd-pill-emerald {
            background: rgba(16, 185, 129, 0.18);
            border: 1px solid rgba(52, 211, 153, 0.45);
            color: #a7f3d0;
            padding: 4px 12px;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 600;
        }
        .kd-pill-amber {
            background: rgba(245, 158, 11, 0.18);
            border: 1px solid rgba(251, 191, 36, 0.45);
            color: #fde68a;
            padding: 4px 12px;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 600;
        }
        .kd-pill-pink {
            background: rgba(236, 72, 153, 0.18);
            border: 1px solid rgba(244, 114, 182, 0.45);
            color: #fbcfe8;
            padding: 4px 12px;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 600;
        }

        /* Fix All Main Area Widget Labels to Crisp White */
        [data-testid="stMain"] div[data-testid="stWidgetLabel"] p,
        [data-testid="stMain"] div[data-testid="stWidgetLabel"] label,
        [data-testid="stMain"] div[data-testid="stRadio"] label,
        [data-testid="stMain"] div[data-testid="stRadio"] p,
        [data-testid="stMain"] div[data-testid="stAudioInput"] label,
        [data-testid="stMain"] div[data-testid="stAudioInput"] p {
            color: #ffffff !important;
            font-weight: 600 !important;
        }

        /* Sleek Glass Radio Bar */
        [data-testid="stMain"] div[data-testid="stRadio"] > div {
            background: linear-gradient(90deg, rgba(13, 66, 50, 0.65), rgba(30, 58, 95, 0.55));
            border: 1px solid rgba(52, 211, 153, 0.35);
            border-radius: 14px;
            padding: 10px 16px;
        }

        /* Transform Default White st.audio_input into Neon Dark-Glass Recorder */
        [data-testid="stMain"] div[data-testid="stAudioInput"] > div {
            background: linear-gradient(135deg, rgba(8, 46, 35, 0.92), rgba(18, 42, 66, 0.92)) !important;
            border: 1.5px solid rgba(56, 189, 248, 0.55) !important;
            border-radius: 16px !important;
            padding: 10px 16px !important;
            box-shadow: 0 6px 24px rgba(14, 165, 233, 0.22) !important;
        }
        [data-testid="stMain"] div[data-testid="stAudioInput"] button {
            background: linear-gradient(135deg, #ec4899, #059669) !important;
            color: #ffffff !important;
            border-radius: 50% !important;
            border: none !important;
            box-shadow: 0 0 14px rgba(236, 72, 153, 0.55) !important;
        }
        [data-testid="stMain"] div[data-testid="stAudioInput"] svg {
            fill: #ffffff !important;
            color: #ffffff !important;
        }
        [data-testid="stMain"] div[data-testid="stAudioInput"] span,
        [data-testid="stMain"] div[data-testid="stAudioInput"] div {
            color: #e0f2fe !important;
        }

        /* Colorful Sample Buttons & Clear Button in Main Area */
        [data-testid="stMain"] div.stButton > button {
            background: linear-gradient(135deg, #10b981 0%, #059669 50%, #047857 100%) !important;
            color: #ffffff !important;
            border: 1px solid rgba(167, 243, 208, 0.45) !important;
            border-radius: 14px !important;
            padding: 12px 14px !important;
            font-weight: 700 !important;
            box-shadow: 0 6px 18px rgba(16, 185, 129, 0.28) !important;
            transition: all 0.22s ease !important;
        }
        [data-testid="stMain"] div.stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 10px 24px rgba(16, 185, 129, 0.48) !important;
            border-color: #fde047 !important;
        }

        /* 3-Step Empty State Onboarding Cards */
        .kd-step-card {
            background: linear-gradient(145deg, rgba(9, 54, 41, 0.65), rgba(24, 14, 52, 0.80));
            border: 1px solid rgba(196, 181, 253, 0.28);
            border-radius: 16px;
            padding: 18px 16px;
            text-align: center;
            height: 100%;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.28);
        }
        .kd-step-num {
            display: inline-block;
            width: 32px;
            height: 32px;
            line-height: 32px;
            border-radius: 50%;
            font-weight: 800;
            font-size: 0.9rem;
            color: #ffffff;
            margin-bottom: 8px;
        }

        /* Conversation Bubbles — Farmer (Warm Violet/Gold) & AI (Emerald/Cyan Aurora) */
        .kd-chat-farmer {
            background: linear-gradient(135deg, rgba(6, 78, 59, 0.42), rgba(49, 16, 82, 0.72));
            backdrop-filter: blur(12px);
            border: 1px solid rgba(251, 191, 36, 0.40);
            border-right: 6px solid #fbbf24;
            border-radius: 20px 20px 4px 20px;
            padding: 18px 22px;
            margin-bottom: 12px;
            box-shadow: 0 8px 24px rgba(15, 7, 36, 0.38);
        }
        .kd-chat-ai {
            background: linear-gradient(135deg, rgba(6, 78, 59, 0.48), rgba(30, 27, 75, 0.82));
            backdrop-filter: blur(14px);
            border: 1px solid rgba(52, 211, 153, 0.48);
            border-left: 6px solid #34d399;
            border-radius: 20px 20px 20px 4px;
            padding: 20px 24px;
            margin-bottom: 12px;
            box-shadow: 0 10px 30px rgba(6, 78, 59, 0.28);
        }
        .kd-urdu-text {
            font-family: 'Noto Nastaliq Urdu', 'Jameel Noori Nastaleeq', serif;
            direction: rtl;
            text-align: right;
            font-size: 1.28rem;
            line-height: 2.45;
            color: #ffffff;
            margin: 8px 0 0 0;
        }
        .kd-speaker-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 4px;
        }
        .kd-speaker-tag-farmer {
            background: rgba(251, 191, 36, 0.20);
            border: 1px solid rgba(251, 191, 36, 0.45);
            color: #fde68a;
            padding: 3px 12px;
            border-radius: 999px;
            font-size: 0.82rem;
            font-weight: 700;
        }
        .kd-speaker-tag-ai {
            background: rgba(16, 185, 129, 0.22);
            border: 1px solid rgba(52, 211, 153, 0.50);
            color: #6ee7b7;
            padding: 3px 12px;
            border-radius: 999px;
            font-size: 0.82rem;
            font-weight: 700;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Initialize session state variables
    if "voice_history" not in st.session_state:
        st.session_state.voice_history = []
    if "last_processed_audio_hash" not in st.session_state:
        st.session_state.last_processed_audio_hash = None

    # Load Groq API Key securely from st.secrets
    try:
        groq_api_key = st.secrets["GROQ_API_KEY"]
    except Exception:
        groq_api_key = ""

    # 1. Vibrant Aurora Hero Banner
    st.markdown(
        """
        <div class="kd-studio-hero">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 14px;">
                <div>
                    <h1 class="kd-hero-title">🎤 Kisaan Dost — Urdu Voice Studio</h1>
                    <p class="kd-hero-sub">
                        Apni awaz mein Urdu ya Punjabi mein sawal poochein — AI foran khalis Urdu Nastaliq mein likhe aur sunaye ga.
                    </p>
                </div>
                <div class="kd-wave-box">
                    <div class="kd-wave-bar"></div>
                    <div class="kd-wave-bar"></div>
                    <div class="kd-wave-bar"></div>
                    <div class="kd-wave-bar"></div>
                    <div class="kd-wave-bar"></div>
                    <span style="color: #a7f3d0; font-size: 0.82rem; font-weight: 700; margin-left: 6px;">LIVE VOICE AI</span>
                </div>
            </div>
            <div class="kd-pill-row">
                <span class="kd-pill-emerald">🎙️ Local Whisper Urdu STT</span>
                <span class="kd-pill-amber">🧠 Groq LLaMA Urdu Nastaliq Brain</span>
                <span class="kd-pill-pink">🔊 Natural Urdu Voice Output</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 2. Control Bar: Whisper Accuracy/Speed Mode + Clear Chat
    ctrl_col1, ctrl_col2 = st.columns([3.2, 1])
    with ctrl_col1:
        whisper_choice = st.radio(
            "🎚️ Voice Recognition Engine Mode:",
            options=["groq_turbo", "base"],
            format_func=lambda x: (
                "🚀 Instant Mode (0.5s — Best Urdu & Punjabi, No Download)"
                if x == "base"
                else "💻 Offline Local Whisper (Base — Works Without Internet)"
            ),
            horizontal=True,
        )
    with ctrl_col2:
        st.markdown("<div style='height: 26px;'></div>", unsafe_allow_html=True)
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.voice_history = []
            st.session_state.last_processed_audio_hash = None
            st.rerun()

    # 3. Dark-Glass Microphone Studio Recorder
    recorded_audio = st.audio_input("🎙️ Neeche Mic Icon Dabakar Urdu ya Punjabi Mein Bolein:")

    # 4. Colorful Quick-Test Agricultural Prompts
    st.markdown(
        "<div style='color: #fde68a; font-weight: 700; font-size: 0.95rem; margin: 12px 0 8px 0;'>"
        "✨ Ya Ek Click Mein Kisi Zarai Sawal Ka Live Demo Dekhein:"
        "</div>",
        unsafe_allow_html=True,
    )
    q_col1, q_col2, q_col3 = st.columns(3)
    sample_prompt = None
    with q_col1:
        if st.button("🌾 گندم کے پیلے زنگ کا علاج", use_container_width=True):
            sample_prompt = "گندم کے پتوں پر پیلا زنگ لگ گیا ہے، اس کا فوری علاج بتائیں۔"
    with q_col2:
        if st.button("🌧️ بارش میں سپرے کا مشورہ", use_container_width=True):
            sample_prompt = "آج موسم ابر آلود ہے اور بارش کا امکان ہے، کیا فصل پر سپرے کرنا ٹھیک ہے؟"
    with q_col3:
        if st.button("🥔 آلو کی فصل میں کھاد", use_container_width=True):
            sample_prompt = "آلو کی بہتر پیداوار کے لیے یوریا اور پوٹاش کھاد کب اور کیسے ڈالنی چاہیے؟"

    # Process Recorded Voice Input
    if recorded_audio is not None:
        raw_bytes = recorded_audio.getvalue()
        audio_hash = hashlib.md5(raw_bytes).hexdigest()

        if audio_hash != st.session_state.last_processed_audio_hash:
            st.session_state.last_processed_audio_hash = audio_hash
            with st.spinner("🎧 آپ کی آواز سمجھی جا رہی ہے اور خالص اردو جواب تیار ہو رہا ہے..."):
                result = process_voice_pipeline(
                    audio_bytes=raw_bytes,
                    groq_api_key=groq_api_key,
                    whisper_size=whisper_choice,
                    chat_history=st.session_state.voice_history,
                )

            st.session_state.last_processed_audio_hash = audio_hash

            if not result["success"]:
                st.error(f"⚠️ {result['error']}")
            else:
                st.session_state.voice_history.append(
                    {
                        "user": result["transcript"],
                        "assistant": result["reply"],
                        "audio": result["audio_bytes"],
                        "warning": result.get("tts_warning"),
                    }
                )

    # Process Quick Sample Prompt Click
    if sample_prompt is not None:
        with st.spinner("🤖 کسان دوست خالص اردو میں مشورہ تیار کر رہا ہے..."):
            llm_out = get_urdu_ai_response(
                sample_prompt,
                groq_api_key,
                chat_history=st.session_state.voice_history,
            )
            if not llm_out["success"]:
                st.error(f"⚠️ {llm_out['error']}")
            else:
                tts_out = synthesize_urdu_speech(llm_out["reply"])
                st.session_state.voice_history.append(
                    {
                        "user": sample_prompt,
                        "assistant": llm_out["reply"],
                        "audio": tts_out.get("audio_bytes") if tts_out["success"] else None,
                        "warning": None if tts_out["success"] else tts_out["error"],
                    }
                )

    # 5. Conversation Feed OR 3-Step Colorful Onboarding Cards
    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    if not st.session_state.voice_history:
        s1, s2, s3 = st.columns(3)
        with s1:
            st.markdown(
                """
                <div class="kd-step-card">
                    <span class="kd-step-num" style="background: linear-gradient(135deg, #ec4899, #059669);">1</span>
                    <div style="font-weight: 700; color: #ffffff; font-size: 1rem;">Mic Icon Dabayein</div>
                    <div style="color: #6ee7b7; font-size: 0.85rem; margin-top: 4px;">
                        Upar diye gaye glowing mic button par click karke recording shuru karein.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with s2:
            st.markdown(
                """
                <div class="kd-step-card">
                    <span class="kd-step-num" style="background: linear-gradient(135deg, #f59e0b, #ea580c);">2</span>
                    <div style="font-weight: 700; color: #ffffff; font-size: 1rem;">Urdu / Punjabi Bolein</div>
                    <div style="color: #fde68a; font-size: 0.85rem; margin-top: 4px;">
                        Apni fasal, khad, spray ya bimari ke baray mein apni zuban mein sawal poochein.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with s3:
            st.markdown(
                """
                <div class="kd-step-card">
                    <span class="kd-step-num" style="background: linear-gradient(135deg, #10b981, #0284c7);">3</span>
                    <div style="font-weight: 700; color: #ffffff; font-size: 1rem;">Urdu Jawab Sunein</div>
                    <div style="color: #a7f3d0; font-size: 0.85rem; margin-top: 4px;">
                        Kisaan Dost khalis Urdu Nastaliq mein mashwara likhe ga aur awaz mein sunaye ga.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        for idx, turn in enumerate(reversed(st.session_state.voice_history)):
            is_latest = idx == 0

            st.markdown(
                f"""
                <div class="kd-chat-farmer">
                    <div class="kd-speaker-header">
                        <span style="color: #fde68a; font-size: 0.78rem;">Transcribed Speech</span>
                        <span class="kd-speaker-tag-farmer">👨‍🌾 کسان بھائی کا سوال</span>
                    </div>
                    <p class="kd-urdu-text">{turn['user']}</p>
                </div>
                <div class="kd-chat-ai">
                    <div class="kd-speaker-header">
                        <span style="color: #6ee7b7; font-size: 0.78rem;">AI Agricultural Advisor</span>
                        <span class="kd-speaker-tag-ai">🌾 کسان دوست کا مشورہ</span>
                    </div>
                    <p class="kd-urdu-text">{turn['assistant']}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if turn.get("audio"):
                st.audio(turn["audio"], format="audio/mp3", autoplay=is_latest)
            elif turn.get("warning"):
                st.warning(f"⚠️ {turn['warning']}")

            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
# ============================================
# PAGE: MANDI RATES
# ============================================
# PAGE: MANDI RATES (5 Provinces & 50+ Crops)
# ============================================
elif st.session_state.page == "📊 Mandi Rates":
    import pandas as pd
    from tools.mandi_scraper import get_mandi_rates
    from tools.mandi_scraper import get_mandi_rates, ALL_CROPS_50
    
    st.markdown("## 📊 Pakistan Live Mandi Rates (5 Provinces)")
    st.write("Pakistan ke tamam 5 subhon (Punjab, Sindh, KPK, Balochistan, Gilgit-Baltistan) aur unki major mandiyon ke taza tareen rates dekhein.")
    
    # 50+ Crops Dropdown
    selected_crop = st.selectbox("Select Crop / Commodity (50+ Available):", ALL_CROPS_50)
    
    if st.button("Check Provincial Rates", type="primary"):
        with st.spinner("Tamam subhon se live rates fetch ho rahe hain..."):
            # Clean commodity name for fetching
            clean_name = selected_crop.split("(")[0].strip()
            rates = get_mandi_rates(commodity_name=clean_name)
            
            if rates:
                df = pd.DataFrame(rates)
                highest = df.loc[df['max_price'].idxmax()]
                lowest = df.loc[df['min_price'].idxmin()]
                
                st.success(f"✅ Latest Provincial Rates for: {selected_crop}")
                
                # Highest and Lowest Highlight Cards
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"""
                    <div style="background: rgba(16, 185, 129, 0.2); padding: 20px; border-radius: 12px; border-left: 5px solid #10B981; backdrop-filter: blur(10px);">
                        <h4 style="margin:0; color:#6EE7B7;">🟢 Highest Price Market</h4>
                        <p style="margin:5px 0 0 0; font-size: 1.2rem; color: white;"><b>{highest['mandi']} ({highest['province']})</b></p>
                        <p style="margin:0; color:#34D399; font-weight: 600; font-size: 1.1rem;">Rs. {highest['max_price']} / 40kg</p>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""
                    <div style="background: rgba(239, 68, 68, 0.2); padding: 20px; border-radius: 12px; border-left: 5px solid #EF4444; backdrop-filter: blur(10px);">
                        <h4 style="margin:0; color:#FCA5A5;">🔴 Lowest Price Market</h4>
                        <p style="margin:5px 0 0 0; font-size: 1.2rem; color: white;"><b>{lowest['mandi']} ({lowest['province']})</b></p>
                        <p style="margin:0; color:#F87171; font-weight: 600; font-size: 1.1rem;">Rs. {lowest['min_price']} / 40kg</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.write("")
                # Detailed Province & City Table
                df_display = df[['province', 'mandi', 'min_price', 'max_price']]
                df_display.columns = ["Province", "City / Mandi", "Min Price (Rs)", "Max Price (Rs)"]
                st.dataframe(df_display, use_container_width=True, hide_index=True)
# ============================================
# PAGE: SCHEMES
# ============================================

elif "Offline" in str(st.session_state.page):
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, rgba(6, 78, 59, 0.90), rgba(13, 59, 46, 0.92));
                    border: 1.5px solid rgba(52, 211, 153, 0.50); border-radius: 20px; padding: 20px 24px; margin-bottom: 16px;">
            <span style="background: #fbbf24; color: #05241b; font-weight: 800; padding: 3px 10px; border-radius: 999px; font-size: 0.78rem;">
                NO INTERNET REQUIRED
            </span>
            <h2 style="margin: 8px 0 4px 0; color: #ffffff;">Offline Kisaan Toolkit (Bina Internet Ke Sahulat)</h2>
            <p style="margin: 0; color: #d1fae5; font-size: 0.95rem;">
                Gaon ya khet mein internet band hone ki soorat mein bhi neeche di gayi tamam sahuliyat 100% offline kaam karti hain.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_calc, tab_guide, tab_scan = st.tabs([
        "Khaad & Spray Calculator (Offline)",
        "Offline Zarai Guide (Urdu/Roman)",
        "Offline Leaf Disease Scanner"
    ])

    with tab_calc:
        st.subheader("Per-Acre Khaad (Fertilizer) & Spray Pani Calculator")
        col1, col2 = st.columns(2)
        with col1:
            crop_choice = st.selectbox(
                "Apni Fasal Muntakhib Karein:",
                ["Gandum (Wheat)", "Chawal (Rice)", "Kapas (Cotton)", "Makai (Maize)", "Aalu / Sabziyat"]
            )
        with col2:
            acres = st.number_input("Zameen Ka Raqba (Acres mein):", min_value=0.5, max_value=500.0, value=1.0, step=0.5)

        fertilizer_rates = {
            "Gandum (Wheat)": {"DAP": 1.5, "Urea": 2.0, "Potash": 0.5, "Water_L": 110, "Tanks": 5.5},
            "Chawal (Rice)": {"DAP": 1.0, "Urea": 2.5, "Potash": 0.5, "Water_L": 120, "Tanks": 6.0},
            "Kapas (Cotton)": {"DAP": 1.5, "Urea": 2.5, "Potash": 1.0, "Water_L": 120, "Tanks": 6.0},
            "Makai (Maize)": {"DAP": 1.5, "Urea": 2.5, "Potash": 0.5, "Water_L": 110, "Tanks": 5.5},
            "Aalu / Sabziyat": {"DAP": 2.0, "Urea": 2.0, "Potash": 1.0, "Water_L": 120, "Tanks": 6.0},
        }
        r = fertilizer_rates[crop_choice]
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("DAP Boriyan", f"{r['DAP'] * acres:.1f} Bags")
        m2.metric("Urea Boriyan", f"{r['Urea'] * acres:.1f} Bags")
        m3.metric("Potash (SOP/MOP)", f"{r['Potash'] * acres:.1f} Bags")
        m4.metric("Spray Pani (20L Tank)", f"{int(r['Water_L'] * acres)} L ({r['Tanks'] * acres:.1f} Tanks)")

        st.info(
            f"Mashwara ({crop_choice} - {acres} Acre): DAP aur Potash bijai ke waqt zameen mein dalein, "
            "jabke Urea ko 2 se 3 qiston mein aabpashi ke sath istemal karein. Spray hamesha subah sawere ya shaam ko karein."
        )

    with tab_guide:
        st.subheader("Offline Zarai Bimariyan Aur Fori Ilaj (Built-in Database)")
        offline_db = {
            "Gandum ? Peela Zung (Wheat Yellow Rust)": "Pattay par peele rang ki dhariyan banti hain. Fori tor par Propiconazole ya Tebuconazole fungicide ko 100?120 liter pani mein mila kar fi acre spray karein.",
            "Chawal ? Patte Ka Jhulsao (Rice Leaf Blast)": "Pattay par ankh numa dhabbay bante hain. Tricyclazole ya Azoxystrobin fi acre spray karein aur khet mein khara pani kuch din ke liye nikal dein.",
            "Kapas ? Patta Maror Virus & Whitefly": "Sufaid makkhi (Whitefly) ke control ke liye Pyriproxyfen ya Acetamiprid subah sawere fi acre spray karein aur narm patton ko bachayein.",
            "Aalu / Tamatar ? Late Blight (Pichheta Jhulsao)": "Pattay kinaron se siyah ho kar galne lagte hain. Mancozeb + Metalaxyl fi acre 7 se 10 din ke waqfe se spray karein.",
        }
        selected_issue = st.selectbox("Bimari / Fasal Chunein:", list(offline_db.keys()))
        st.success(f"**Offline Ilaj & Spray Guide:** {offline_db[selected_issue]}")

    with tab_scan:
        st.subheader("Local Offline Deep Learning Leaf Scanner")
        st.write("Aapka trained AI model local disk par mojood hai ? internet band hone par bhi neeche button daba kar leaf photo scan karein:")
        if st.button("?? Open Offline Disease Detector", use_container_width=True):
            for candidate in ["?? Disease Check", "Disease Check"]:
                st.session_state.page = candidate
                break
            st.rerun()
elif st.session_state.page == "📋 Schemes":
    import hashlib
    from tools.schemes_advisor import transcribe_scheme_voice, ask_schemes_with_voice_and_text

    st.markdown(
        """
        <div style="background: linear-gradient(135deg, rgba(7, 45, 62, 0.88), rgba(6, 62, 48, 0.88));
                    border: 1.5px solid rgba(56, 189, 248, 0.45); border-radius: 20px; padding: 20px 24px; margin-bottom: 16px;">
            <h2 style="margin: 0; color: #ffffff;">📋 Sarkari Zarai Schemes ? Bol Kar Ya Likh Kar Poochein</h2>
            <p style="margin: 6px 0 0 0; color: #bae6fd; font-size: 0.95rem;">
                Kisi bhi sarkari scheme ke baray mein bolein ya likhein ? jawab asaan Roman Urdu, clickable official links, aur Voice Note mein milega.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    try:
        groq_api_key = st.secrets["GROQ_API_KEY"]
    except Exception:
        groq_api_key = ""

    if "schemes_history" not in st.session_state:
        st.session_state.schemes_history = []
    if "last_scheme_audio_hash" not in st.session_state:
        st.session_state.last_scheme_audio_hash = None

    scheme_audio = st.audio_input("🎙️ Bol kar scheme ka sawal poochein (Kissan Card, Green Tractor, Solar Tube Well, Qarza):")

    st.markdown("**⚡ Ya ek click mein kisi scheme ki poori tafseel aur official link dekhein:**")
    c1, c2, c3 = st.columns(3)
    quick_q = None
    with c1:
        if st.button("💳 CM Punjab Kissan Card", use_container_width=True):
            quick_q = "CM Punjab Kissan Card kya hai? Is ki raqam, eligibility, official website link aur apply karne ka mukammal tariqa Roman Urdu mein batayein."
    with c2:
        if st.button("🚜 Green Tractor & Solar Scheme", use_container_width=True):
            quick_q = "CM Green Tractor Scheme aur Solar Tube Well subsidy ki mukammal tafseel, official website link aur apply tariqa Roman Urdu mein batayein."
    with c3:
        if st.button("🏦 PM Agri Loan & ZTBL Qarza", use_container_width=True):
            quick_q = "Prime Minister Youth Business & Agriculture Loan Scheme (10 lakh loan) aur ZTBL zarai qarza ki mukammal tafseel aur clickable link Roman Urdu mein dein."

    typed_q = st.text_input(
        "⌨️ Apna sawal likhein (Roman Urdu ya English mein):",
        placeholder="Maslan: Mujhy 10 lakh loan chahiye, is ki eligibility aur apply link batayein?",
    )
    col_b1, col_b2 = st.columns([3, 1])
    with col_b1:
        typed_btn = st.button("📩 Mukammal Jawab & Link Hasil Karein", use_container_width=True)
    with col_b2:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.schemes_history = []
            st.session_state.last_scheme_audio_hash = None
            st.rerun()

    final_scheme_query = None
    if scheme_audio is not None:
        raw_bytes = scheme_audio.getvalue()
        a_hash = hashlib.md5(raw_bytes).hexdigest()
        if a_hash != st.session_state.last_scheme_audio_hash:
            st.session_state.last_scheme_audio_hash = a_hash
            with st.spinner("🎧 Aap ki awaz samjhi ja rahi hai..."):
                stt_out = transcribe_scheme_voice(raw_bytes, groq_api_key)
            if not stt_out["success"]:
                st.error(f"⚠️ {stt_out['error']}")
            else:
                final_scheme_query = stt_out["text"]

    if quick_q:
        final_scheme_query = quick_q
    elif typed_btn and typed_q.strip():
        final_scheme_query = typed_q.strip()

    if final_scheme_query:
        with st.spinner("📋 Sarkari scheme ki maloomat, official link aur voice note tayyar ho raha hai..."):
            ans = ask_schemes_with_voice_and_text(
                final_scheme_query,
                groq_api_key,
                chat_history=st.session_state.schemes_history,
            )
        if not ans["success"]:
            st.error(f"⚠️ {ans['error']}")
        else:
            st.session_state.schemes_history.append(
                {
                    "user": final_scheme_query,
                    "assistant": ans["reply"],
                    "assistant_raw": ans.get("raw_reply", ""),
                    "audio": ans.get("audio_bytes"),
                }
            )

    for idx, turn in enumerate(reversed(st.session_state.schemes_history)):
        is_latest = idx == 0
        st.markdown(
            f"""
            <div dir="ltr" style="background: rgba(245, 158, 11, 0.16); border-left: 5px solid #fbbf24;
                        border-radius: 16px; padding: 14px 18px; margin-top: 14px; text-align: left;">
                <div style="color: #fde68a; font-size: 0.85rem; font-weight: 700;">👨‍🌾 Kisaan Ka Sawal</div>
                <div style="color: #ffffff; font-size: 1.05rem; margin-top: 4px; line-height: 1.6;">
                    {turn['user']}
                </div>
            </div>
            <div dir="ltr" style="background: linear-gradient(135deg, rgba(6, 78, 59, 0.55), rgba(7, 45, 62, 0.78));
                        border: 1px solid rgba(52, 211, 153, 0.45); border-left: 5px solid #34d399;
                        border-radius: 16px; padding: 18px 22px; margin-top: 8px; text-align: left;">
                <div style="color: #6ee7b7; font-size: 0.88rem; font-weight: 700; margin-bottom: 6px;">
                    📋 Sarkari Scheme Ki Mukammal Tafseel & Official Portal Link
                </div>
                <div style="color: #ffffff; font-size: 1.02rem; line-height: 1.75;">
                    {turn['assistant']}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if turn.get("audio"):
            st.audio(turn["audio"], format="audio/mp3", autoplay=is_latest)
elif st.session_state.page == "🔬 Disease Check":
    from tools.disease_detector import predict_crop_disease_100
    
    st.markdown("## 🔬 100-Crop Disease Detection & AI Treatment")
    st.write("Fasal ke patte ki tasweer upload karein aur 100 mukhtalif bimariyon mein se shanakht karein.")
    
    uploaded_leaf = st.file_uploader("Fasal ke patte ki tasweer upload karein (JPG/PNG)", type=["jpg", "jpeg", "png"])
    
    if uploaded_leaf is not None:
        st.image(uploaded_leaf, caption="Uploaded Crop Leaf", use_container_width=True)
        
        if st.button("🔍 Scan 100+ Diseases", type="primary"):
            with st.spinner("AI 100+ disease patterns match kar raha hai..."):
                disease, conf, treatment = predict_crop_disease_100(uploaded_leaf)
                
                if disease == "Error" or disease == "Model File Missing":
                    st.error(f"⚠️ {treatment}")
                else:
                    st.success(f"✅ Shanakht Shuda Bimari: **{disease}** (Confidence: {conf:.2f}%)")
                    
                    st.markdown(f"""
                    <div style="background: rgba(16, 185, 129, 0.2); padding: 20px; border-radius: 12px; margin-top: 15px; border-left: 5px solid #10B981;">
                        <h4 style="color: #6EE7B7; margin-top: 0;">💊 Urdu Ilaj aur Tajweez:</h4>
                        <p style="color: white; font-size: 1.1rem;">{treatment}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
            st.markdown("""
            <div style="background: rgba(239, 68, 68, 0.2); padding: 15px; border-radius: 12px; margin-top: 15px; border-left: 5px solid #EF4444;">
                <p style="color: #FCA5A5; margin: 0;"><b>📞 Helpline:</b> Mazeed rehnumai ke liye <b>0800-17000</b> par rabta karein.</p>
            </div>
            """, unsafe_allow_html=True)
# ============================================
# PAGE: WEATHER
# ============================================
elif st.session_state.page == "🌤 Weather":
    from tools.weather_api import fetch_weather_bundle
    # Glassmorphism Dark Purple Theme Styling for Weather Module
    st.markdown(
        """
        <style>
        .kd-glass-card {
            background: linear-gradient(135deg, rgba(9, 54, 41, 0.65), rgba(22, 12, 48, 0.78));
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            border: 1px solid rgba(52, 211, 153, 0.28);
            border-radius: 18px;
            padding: 22px;
            margin-bottom: 18px;
            box-shadow: 0 8px 32px rgba(10, 5, 25, 0.45);
            color: #f3e8ff;
        }
        .kd-metric-box {
            background: rgba(139, 92, 246, 0.14);
            border: 1px solid rgba(196, 181, 253, 0.22);
            border-radius: 14px;
            padding: 14px 10px;
            text-align: center;
        }
        .kd-metric-label {
            font-size: 0.82rem;
            color: #6ee7b7;
            margin-bottom: 4px;
        }
        .kd-metric-value {
            font-size: 1.35rem;
            font-weight: 700;
            color: #ffffff;
        }
        .kd-advice-danger {
            background: linear-gradient(135deg, rgba(127, 29, 29, 0.55), rgba(59, 18, 54, 0.75));
            border-left: 5px solid #f87171;
        }
        .kd-advice-warning {
            background: linear-gradient(135deg, rgba(120, 53, 15, 0.55), rgba(49, 24, 78, 0.75));
            border-left: 5px solid #fbbf24;
        }
        .kd-advice-success {
            background: linear-gradient(135deg, rgba(20, 83, 45, 0.52), rgba(43, 22, 74, 0.75));
            border-left: 5px solid #34d399;
        }
        .kd-forecast-card {
            background: rgba(39, 21, 77, 0.58);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(52, 211, 153, 0.25);
            border-radius: 16px;
            padding: 16px 12px;
            text-align: center;
            min-height: 255px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
        }
        .kd-tag-pill {
            display: inline-block;
            background: rgba(139, 92, 246, 0.28);
            border: 1px solid rgba(196, 181, 253, 0.35);
            border-radius: 999px;
            padding: 4px 10px;
            font-size: 0.76rem;
            color: #ede9fe;
            margin-top: 8px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("## 🌤️ Kisaan Mausam aur Zarai Alerts")
    st.caption("Apne shehar ka live mausam, 5-din ki peshgoi aur faslon ke liye Urdu hidayat dekhein.")

    # Cache weather requests for 10 minutes (600s) to protect free API quota
    @st.cache_data(ttl=600, show_spinner=False)
    def _fetch_success_only(city_name: str, key: str):
        res = fetch_weather_bundle(city_name, key)
        if not res["success"]:
            raise RuntimeError(res["error"])
        return res

    def get_cached_weather(city_name: str, key: str):
        try:
            return _fetch_success_only(city_name, key.strip())
        except RuntimeError as err:
            return {"success": False, "error": str(err)}

    # City Selection Controls
    pakistani_cities = [
        "Lahore",
        "Multan",
        "Faisalabad",
        "Karak",
        "Peshawar",
        "Islamabad",
        "Rawalpindi",
        "Karachi",
        "Bahawalpur",
        "Sargodha",
        "Sukkur",
        "Quetta",
        "Custom City (Khud Likhein)",
    ]

    col_sel, col_custom, col_btn = st.columns([2, 2, 1])
    with col_sel:
        selected_option = st.selectbox("📍 Apna Shehar Chunein:", pakistani_cities, index=0)

    with col_custom:
        if selected_option == "Custom City (Khud Likhein)":
            target_city = st.text_input("✍️ Shehar ka naam likhein:", value="Sahiwal", placeholder="e.g. Gujranwala")
        else:
            target_city = st.text_input("🔍 Ya koi aur shehar search karein:", value=selected_option)

    with col_btn:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        refresh_clicked = st.button("🔄 Refresh", use_container_width=True)
        if refresh_clicked:
            st.cache_data.clear()

    # Load API Key safely from st.secrets
    try:
        owm_api_key = st.secrets["OPENWEATHER_API_KEY"]
    except Exception:
        owm_api_key = ""

    with st.spinner(f"⏳ {target_city} ka live mausam aur 5-din ki report hasil ki ja rahi hai..."):
        weather_result = get_cached_weather(target_city, owm_api_key)

    if not weather_result["success"]:
        st.error(f"⚠️ {weather_result['error']}")
    else:
        curr = weather_result["current"]
        advice = weather_result["advice"]
        forecast = weather_result["forecast"]

        # 1. Current Weather Hero Card
        st.markdown(
            f"""
            <div class="kd-glass-card">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
                    <div>
                        <div style="font-size: 0.9rem; color: #6ee7b7; letter-spacing: 0.5px;">LIVE MAUSAM REPORT</div>
                        <h2 style="margin: 2px 0 6px 0; color: #ffffff;">📍 {weather_result['city']}, {weather_result['country']}</h2>
                        <div style="font-size: 1.1rem; color: #e9d5ff;">
                            {curr['emoji']} <b>{curr['urdu_condition']}</b> ({curr['condition']})
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 3.1rem; font-weight: 800; line-height: 1; color: #ffffff;">
                            {curr['temp']}°C
                        </div>
                        <div style="font-size: 0.9rem; color: #6ee7b7; margin-top: 4px;">
                            Mehsoos: {curr['feels_like']}°C
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 4 Key Metric Cards
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(
                f"""<div class="kd-metric-box">
                    <div class="kd-metric-label">🌡️ Darja-e-Hararat</div>
                    <div class="kd-metric-value">{curr['temp']}°C</div>
                </div>""",
                unsafe_allow_html=True,
            )
        with m2:
            st.markdown(
                f"""<div class="kd-metric-box">
                    <div class="kd-metric-label">💧 Hawa Mein Nami</div>
                    <div class="kd-metric-value">{curr['humidity']}%</div>
                </div>""",
                unsafe_allow_html=True,
            )
        with m3:
            st.markdown(
                f"""<div class="kd-metric-box">
                    <div class="kd-metric-label">💨 Hawa Ki Raftaar</div>
                    <div class="kd-metric-value">{curr['wind_kmh']} km/h</div>
                </div>""",
                unsafe_allow_html=True,
            )
        with m4:
            st.markdown(
                f"""<div class="kd-metric-box">
                    <div class="kd-metric-label">🌧️ Barish Ka Imkaan</div>
                    <div class="kd-metric-value">{curr['rain_prob']}%</div>
                </div>""",
                unsafe_allow_html=True,
            )

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

        # 2. Urdu Agricultural Advisory Card
        advice_class = f"kd-advice-{advice['level']}"
        tips_html = "".join(f"<li style='margin-bottom: 6px;'>{tip}</li>" for tip in advice["tips"])

        st.markdown(
            f"""
            <div class="kd-glass-card {advice_class}">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="font-weight: 700; font-size: 1.05rem; color: #ffffff;">🌾 Kisaan Zarai Mashwara (Urdu Advisory)</span>
                    <span class="kd-tag-pill">{advice['badge']}</span>
                </div>
                <p style="font-size: 1.05rem; font-weight: 600; color: #fef08a; margin-bottom: 10px;">
                    {advice['headline']}
                </p>
                <ul style="margin: 0; padding-left: 20px; color: #f3e8ff; font-size: 0.95rem;">
                    {tips_html}
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 3. 5-Day Forecast Section
        st.markdown("### 📅 Agle 5 Din Ki Zarai Peshgoi (5-Day Forecast)")
        forecast_cols = st.columns(len(forecast))

        for idx, day in enumerate(forecast):
            with forecast_cols[idx]:
                st.markdown(
                    f"""
                    <div class="kd-forecast-card">
                        <div>
                            <div style="font-weight: 700; color: #ffffff; font-size: 1rem;">{day['day_name']}</div>
                            <div style="font-size: 0.82rem; color: #6ee7b7;">{day['date']}</div>
                            <div style="font-size: 2.2rem; margin: 10px 0;">{day['emoji']}</div>
                            <div style="font-size: 0.88rem; font-weight: 600; color: #e9d5ff; min-height: 38px;">
                                {day['urdu_condition']}
                            </div>
                        </div>
                        <div>
                            <div style="font-size: 1.05rem; font-weight: 700; color: #ffffff; margin: 6px 0;">
                                {day['max_temp']}° / <span style="color: #6ee7b7; font-weight: 400;">{day['min_temp']}°</span>
                            </div>
                            <div style="font-size: 0.78rem; color: #6ee7b7;">
                                🌧️ {day['rain_prob']}% &nbsp;|&nbsp; 💨 {day['wind_kmh']} km/h
                            </div>
                            <div class="kd-tag-pill">{day['action_tag']}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

# ============================================
# FOOTER
# ============================================
st.markdown("""
<div class="footer">
    <p>🌾 <strong>Kisaan Dost</strong> — Made with ❤️ for Pakistani Farmers</p>
</div>
""", unsafe_allow_html=True)


