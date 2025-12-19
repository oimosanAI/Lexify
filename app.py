import streamlit as st
import os
import google.generativeai as genai
from dotenv import load_dotenv
import time

# 1. 環境設定・認証設定
load_dotenv()

# ==========================================
# 👇 ここにAPIキーを貼り付けてください
# ==========================================
GOOGLE_API_KEY = "AIzaSyAf_rdC27RzygHRgefpfNROdQ0my2c20k4"
# ==========================================

# 簡易パスワード (顧客に教える合言葉)
SYSTEM_PASSWORD = "lexify-demo" 

# キーチェック
if "あなたの" in GOOGLE_API_KEY:
    st.error("⚠️ APIキーを書き換えてください！")
    st.stop()

genai.configure(api_key=GOOGLE_API_KEY)

# 2. ページ設定
st.set_page_config(page_title="Lexify PoC (v2.0)", layout="wide")

# --- 🔐 ログイン機能 (Phase 2 Requirement) ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def check_password():
    if st.session_state.password_input == SYSTEM_PASSWORD:
        st.session_state.authenticated = True
        del st.session_state.password_input
    else:
        st.error("パスワードが間違っています")

if not st.session_state.authenticated:
    st.title("🔒 Lexify Login")
    st.text_input("パスワードを入力してください", type="password", key="password_input", on_change=check_password)
    st.stop() # 認証されるまでここで止める

# --- ログイン後のメイン画面 ---
st.title("🧩 Lexify Catalog Search (PoC ver.)")
st.caption("Phase 2: Multi-File Vision Mode | Powered by Gemini 2.0 Flash")

# サイドバー: データ管理
st.sidebar.header("📚 Data Management")
st.sidebar.info("複数のカタログPDFを一括で解析します。")

# 3. ファイル処理ロジック (キャッシュ対応)
@st.cache_resource(show_spinner=False)
def process_uploaded_files(uploaded_files):
    file_handles = []
    progress_bar = st.sidebar.progress(0)
    status_text = st.sidebar.empty()
    
    for i, uploaded_file in enumerate(uploaded_files):
        # 一時保存
        status_text.text(f"Uploading {uploaded_file.name}...")
        save_path = os.path.join("data", uploaded_file.name)
        os.makedirs("data", exist_ok=True)
        
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
            
        # Geminiにアップロード
        try:
            # MIMEタイプを自動判定または指定
            mime_type = "application/pdf"
            uploaded_ref = genai.upload_file(path=save_path, display_name=uploaded_file.name, mime_type=mime_type)
            
            # 処理完了待ち (Activeになるまで待機)
            while uploaded_ref.state.name == "PROCESSING":
                time.sleep(2)
                uploaded_ref = genai.get_file(uploaded_ref.name)
                
            file_handles.append(uploaded_ref)
        except Exception as e:
            st.error(f"Error uploading {uploaded_file.name}: {e}")
            
        # 進捗更新
        progress_bar.progress((i + 1) / len(uploaded_files))
        
    status_text.text("✅ All files ready!")
    time.sleep(1)
    status_text.empty()
    progress_bar.empty()
    
    return file_handles

# 4. UI実装
# 複数ファイルアップロード対応 (accept_multiple_files=True)
uploaded_files = st.sidebar.file_uploader(
    "PDFカタログを選択 (複数可)", 
    type=["pdf"], 
    accept_multiple_files=True
)

# セッション管理
if "chat_session" not in st.session_state:
    st.session_state.chat_session = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# スタートボタン
if uploaded_files and not st.session_state.chat_session:
    if st.sidebar.button("🚀 カタログを読み込んで開始"):
        with st.spinner("エンジンを起動中... (これには数秒かかります)"):
            try:
                # 1. ファイルを処理 (キャッシュされるのでリロードしても高速)
                file_objects = process_uploaded_files(uploaded_files)
                
                # 2. システムプロンプト作成
                system_instruction = """
                あなたは熟練した専門商社の営業アシスタントAIです。
                アップロードされた複数のカタログPDFの内容をすべて視覚的に理解し、ユーザーの質問に答えてください。
                
                【ルール】
                1. 正確性: 型番、スペック、数値は絶対に間違えないこと。表の読み取りに注意する。
                2. 根拠: 回答の際は、必ず「どのファイルの、どのあたり(ページ数など)に書いてあるか」を明記すること。
                3. 不明時: カタログに載っていないことは正直に「記載がありません」と答えること。
                """
                
                # 3. モデル初期化 (Gemini 2.0 Flash)
                model = genai.GenerativeModel(
                model_name="models/gemini-3-flash-preview", 
                system_instruction=system_instruction
                )
                
                # 4. チャット履歴の初期化 (ファイルを渡す)
                # historyの最初の要素としてファイルを渡すのがポイント
                st.session_state.chat_session = model.start_chat(
                    history=[
                        {
                            "role": "user",
                            "parts": file_objects + ["これらのカタログデータを参照して回答してください。"]
                        },
                        {
                            "role": "model",
                            "parts": ["承知いたしました。アップロードされたすべてのカタログを確認しました。型番検索、スペック確認など、なんでもお申し付けください。"]
                        }
                    ]
                )
                
                # 最初の挨拶を履歴に追加
                st.session_state.messages.append({"role": "assistant", "content": "準備完了です。複数のカタログから横断的に検索できます。"})
                st.rerun()
                
            except Exception as e:
                st.error(f"起動エラー: {e}")

# チャット画面
if st.session_state.chat_session:
    # 履歴表示
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    # 入力フォーム
    if prompt := st.chat_input("質問を入力 (例: 耐熱120度のコネクタはどれ？)"):
        # ユーザーの入力を表示
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)

        # AIの回答処理
        with st.chat_message("assistant"):
            resp_placeholder = st.empty()
            resp_placeholder.markdown("Thinking...")
            
            try:
                response = st.session_state.chat_session.send_message(prompt)
                answer_text = response.text
                
                # ログ保存 (Phase 2 Requirement: 改善の宝庫)
                # 簡易的にコンソールに出力（本番ではDBへ）
                print(f"[LOG] User: {prompt} | AI: {answer_text[:50]}...")
                
                resp_placeholder.markdown(answer_text)
                st.session_state.messages.append({"role": "assistant", "content": answer_text})
                
            except Exception as e:
                st.error(f"回答エラー: {e}")

else:
    # 未開始時のガイド
    if not uploaded_files:
        st.info("👈 サイドバーからカタログ(PDF)をアップロードしてください。")
    else:
        st.info("👈 サイドバーの「🚀 カタログを読み込んで開始」ボタンを押してください。")

# 画面下部にリセットボタン
st.sidebar.divider()
if st.sidebar.button("🔄 リセット (新しいカタログを読み込む)"):
    st.session_state.clear()
    st.rerun()