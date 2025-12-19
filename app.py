import streamlit as st
import os
import google.generativeai as genai
from dotenv import load_dotenv
import time

# ==========================================
# 1. ページ設定 & 初期化
# ==========================================
st.set_page_config(
    page_title="Lexify | Enterprise AI Search",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# セッション変数の初期化
if "chat_session" not in st.session_state:
    st.session_state.chat_session = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# ==========================================
# 2. デザイン (Final Ship - Royal Purple Title)
# ==========================================
st.markdown("""
<style>
    /* 日本語フォント設定 */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', "Hiragino Kaku Gothic ProN", "Hiragino Sans", Meiryo, sans-serif;
        color: #E2E8F0 !important;
    }

    /* --- 背景: 上品な暗めのプラチナグラデーション --- */
    .stApp {
        background-color: #0F172A;
        background-image: radial-gradient(circle at 50% 0%, #1E293B 0%, #0F172A 60%);
        background-attachment: fixed;
    }

    /* ヘッダー調整 */
    .block-container {
        padding-top: 5rem !important;
        padding-bottom: 6rem !important;
    }

    /* --- サイドバー --- */
    [data-testid="stSidebar"] {
        background-color: #111827 !important;
        border-right: 1px solid #1F2937;
        box-shadow: 5px 0 15px rgba(0,0,0,0.2);
    }
    [data-testid="stSidebar"] * {
        color: #CBD5E1 !important;
    }
    [data-testid="stSidebar"] strong {
        color: #A78BFA !important;
    }
    /* ファイルアップローダー */
    [data-testid="stFileUploader"] {
        background-color: #1F2937;
        border-radius: 10px;
        padding: 10px;
        border: 1px dashed #374151;
    }
    [data-testid="stFileUploader"] small {
        display: none;
    }

    /* --- ボタン (Royal Purple Gradient) --- */
    .stButton button {
        background: linear-gradient(135deg, #7C3AED 0%, #5B21B6 100%);
        color: white !important;
        border: 1px solid #6D28D9;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.6rem 1.2rem;
        transition: all 0.2s ease;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px -3px rgba(124, 58, 237, 0.4);
        border-color: #A78BFA;
    }

    /* --- 入力フォーム --- */
    .stTextInput input, .stPasswordInput input {
        background-color: #1F2937 !important;
        color: #F8FAFC !important;
        border: 1px solid #374151;
        border-radius: 8px;
    }
    .stTextInput input:focus, .stPasswordInput input:focus {
        border-color: #A78BFA;
        box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.2);
    }
    label {
        color: #CBD5E1 !important;
    }
    .stChatInput {
        background-color: #1F2937 !important;
        border-radius: 12px;
        border: 1px solid #374151;
    }

    /* --- タイトル修正 (ここを変更しました！) --- */
    .main-title {
        font-size: 3.5rem; 
        font-weight: 800;
        letter-spacing: -0.03em;
        /* 修正: ロゴに合わせた鮮やかで深い紫のグラデーション */
        background: -webkit-linear-gradient(0deg, #C084FC, #7C3AED);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
        margin-top: 0 !important;
        line-height: 1.4 !important; 
        padding-top: 10px !important;
        padding-bottom: 20px !important;
        /* 修正: 光彩も強く鮮やかに */
        text-shadow: 0 0 40px rgba(124, 58, 237, 0.5);
    }
    .sub-title {
        font-size: 1.1rem;
        color: #94A3B8;
        margin-bottom: 3rem;
        margin-top: -10px;
        font-weight: 500;
    }

    /* --- ヒーローセクション --- */
    .hero-container {
        text-align: center;
        padding: 4rem 2rem;
        background: rgba(30, 41, 59, 0.5);
        backdrop-filter: blur(10px);
        border-radius: 24px;
        border: 1px solid rgba(148, 163, 184, 0.1);
        box-shadow: 0 20px 40px -10px rgba(0, 0, 0, 0.3);
        margin-bottom: 2rem;
        margin-top: 1rem;
    }
    .hero-icon {
        font-size: 5rem;
        margin-bottom: 1rem;
        display: inline-block;
        filter: drop-shadow(0 10px 20px rgba(124, 58, 237, 0.4));
    }

    /* --- ログインカード --- */
    .login-container {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(12px);
        padding: 3rem;
        border-radius: 24px;
        border: 1px solid rgba(139, 92, 246, 0.3);
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.4);
        text-align: center;
    }
    
    /* チャットメッセージ */
    [data-testid="stChatMessage"] {
        background-color: transparent;
        border-bottom: 1px solid #1F2937;
        padding: 1.5rem 0;
    }
    [data-testid="stChatMessageAvatarBackground"] {
        background-color: #6D28D9 !important;
    }
</style>
""", unsafe_allow_html=True)

load_dotenv()

# ==========================================
# 3. APIキー読み込み
# ==========================================
api_key = None
try:
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
except: pass

if not api_key and os.path.exists("api_key.txt"):
    try:
        with open("api_key.txt", "r", encoding="utf-8") as f:
            raw = f.read()
            api_key = raw.replace("GOOGLE_API_KEY", "").replace("=", "").replace('"', "").replace("'", "").strip()
    except: pass

if not api_key and os.getenv("GOOGLE_API_KEY"):
    api_key = os.getenv("GOOGLE_API_KEY")

# ==========================================
# 4. ログイン認証
# ==========================================
SYSTEM_PASSWORD = "lexify-demo" 

if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="height: 100px;"></div>
        <div class="login-container">
            <h1 style="color:#F8FAFC; font-size: 3.5rem; margin:0; font-weight:800; letter-spacing:-0.03em; text-shadow: 0 0 30px rgba(124, 58, 237, 0.6);">🔮 Lexify</h1>
            <p style="color:#94A3B8; margin-top:10px; font-size:1.1rem; font-weight:500;">専門商社向け AIカタログ検索プラットフォーム</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        password = st.text_input("パスワード", type="password", label_visibility="collapsed", placeholder="パスワードを入力してください...")
        
        if st.button("システムにログイン", use_container_width=True):
            if password == SYSTEM_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("パスワードが間違っています")
    st.stop()

# ==========================================
# 5. サイドバー (管理メニュー)
# ==========================================
with st.sidebar:
    st.markdown("### 🏢 管理メニュー")
    
    if not api_key:
        st.warning("⚠️ APIキー未設定")
        api_key = st.text_input("API Key", type="password")

    st.markdown("---")
    st.markdown("#### 📂 1. カタログ読込")
    uploaded_files = st.file_uploader("ここにPDFをドラッグ", type=["pdf"], accept_multiple_files=True, label_visibility="collapsed")
    
    st.markdown("#### ⚙️ 2. システム状態")
    if st.session_state.chat_session:
        # ここも色を合わせて鮮やかに
        st.markdown('🟣 <span style="color:#C084FC"><b>AIエンジン: 稼働中</b></span>', unsafe_allow_html=True)
    elif api_key:
        st.markdown('🟡 <span style="color:#FBBF24"><b>準備完了</b></span>', unsafe_allow_html=True)
    else:
        st.error("🔴 設定エラー")
        
    st.markdown("---")
    if st.button("🗑️ 会話をリセット", use_container_width=True):
        st.session_state.messages = []
        st.session_state.chat_session = None
        st.rerun()

if not api_key:
    st.stop()

try:
    genai.configure(api_key=api_key)
except Exception as e:
    st.error(f"Config Error: {e}")
    st.stop()

# ==========================================
# 6. メインロジック
# ==========================================

# タイトル
st.markdown('<div class="main-title">Lexify AI Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Powered by <b>Gemini 3.0 Vision</b> | 専門商社・技術営業のためのAIパートナー</div>', unsafe_allow_html=True)

# ファイル処理
@st.cache_resource(show_spinner=False)
def process_uploaded_files(files):
    file_handles = []
    progress_text = "カタログを解析中..."
    my_bar = st.progress(0, text=progress_text)
    
    for i, file in enumerate(files):
        save_path = os.path.join("data", file.name)
        os.makedirs("data", exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(file.getbuffer())
        try:
            uploaded_ref = genai.upload_file(path=save_path, mime_type="application/pdf")
            while uploaded_ref.state.name == "PROCESSING":
                time.sleep(1)
                uploaded_ref = genai.get_file(uploaded_ref.name)
            file_handles.append(uploaded_ref)
        except Exception as e:
            st.error(f"Error: {e}")
        my_bar.progress((i + 1) / len(files), text=f"スキャン中: {file.name}")
    
    time.sleep(0.5)
    my_bar.empty()
    return file_handles

# レスポンス生成
def generate_response(prompt):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑‍💼"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🔮"):
        message_placeholder = st.empty()
        full_response = ""
        try:
            responses = st.session_state.chat_session.send_message(prompt, stream=True)
            for chunk in responses:
                full_response += chunk.text
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        except Exception as e:
            st.error(f"API Error: {e}")

# --- ヒーローセクション ---
if not st.session_state.messages and not uploaded_files:
    st.markdown("""
    <div class="hero-container">
        <div class="hero-icon">🔮</div>
        <h2 style="color:#F8FAFC; margin-bottom:1rem; font-weight:800;">Lexifyへようこそ</h2>
        <p style="color:#CBD5E1; font-size:1.1rem; line-height:1.6;">
            サイドバーからPDFカタログをアップロードして、<br>
            「AIエンジンを起動」ボタンを押してください。<br>
            <strong>Gemini 3.0 Vision</strong> が、図面やスペック表を正確に読み取ります。
        </p>
    </div>
    """, unsafe_allow_html=True)

# 起動ボタン
if uploaded_files and st.session_state.chat_session is None:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.info("👆 PDFの準備ができました。解析を開始します。")
    with col2:
        if st.button("🚀 AIエンジンを起動", type="primary", use_container_width=True):
            with st.spinner("図面とスペック表を解析中..."):
                try:
                    files = process_uploaded_files(uploaded_files)
                    system_instruction = """
                    あなたは日本の専門商社のアシスタント「Lexify」です。
                    ユーザーから提供された複数のカタログPDFを視覚的に理解し、日本語で回答します。
                    【必須ルール】
                    1. 数値、型番は絶対に正確に答えること。
                    2. 回答の根拠となる「ページ数」や「カタログ名」を必ず明記すること。
                    3. 表組や図面の内容も読み取って回答すること。
                    """
                    model = genai.GenerativeModel(
                        model_name="models/gemini-3-flash-preview",
                        system_instruction=system_instruction
                    )
                    st.session_state.chat_session = model.start_chat(
                        history=[
                            {"role": "user", "parts": files + ["資料を記憶してください。"]},
                            {"role": "model", "parts": ["解析完了。"]}
                        ]
                    )
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": "準備完了です。カタログの比較、スペック検索などをご指示ください。"
                    })
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

# 履歴表示
for msg in st.session_state.messages:
    if msg["role"] == "assistant":
        with st.chat_message("assistant", avatar="🔮"):
            st.markdown(msg["content"])
    else:
        with st.chat_message("user", avatar="🧑‍💼"):
            st.markdown(msg["content"])

# アクションボタン
if st.session_state.chat_session and len(st.session_state.messages) <= 1:
    st.markdown("#### 💡 おすすめの操作")
    col1, col2 = st.columns(2)
    if col1.button("📊 スペック比較 (JST vs Molex)", use_container_width=True):
        prompt = "Molexの『Micro-Fit 3.0』と、JSTの『XHシリーズ』を比較したいです。それぞれの『ピッチ（mm）』と『定格電流』を教えてください。"
        generate_response(prompt)
        st.rerun()
    if col2.button("🔍 型番検索 (XHP-4)", use_container_width=True):
        prompt = "JSTの型番『XHP-4』の適合電線範囲（AWG）と、極数を教えてください。根拠ページも示して。"
        generate_response(prompt)
        st.rerun()

# 入力欄
if prompt := st.chat_input("カタログについて質問を入力してください..."):
    if st.session_state.chat_session is None:
        st.warning("⚠️ サイドバーからPDFをアップロードし、「AIエンジンを起動」してください。")
    else:
        generate_response(prompt)