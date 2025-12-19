import google.generativeai as genai
import os
from dotenv import load_dotenv

# .env から読み込むか、直接設定
load_dotenv()
GOOGLE_API_KEY = "AIzaSyAf_rdC27RzygHRgefpfNROdQ0my2c20k4" # 👈 ここにキーを貼るか、.envを使用

# APIキーの設定
if "あなたの" in GOOGLE_API_KEY:
    print("❌ エラー: APIキーを書き換えてください。")
    exit()

genai.configure(api_key=GOOGLE_API_KEY)

print("🔍 利用可能なGeminiモデルを検索中...\n")

try:
    # モデル一覧を取得
    models = genai.list_models()
    
    available_models = []
    for m in models:
        # チャット(generateContent)に対応しているモデルのみ抽出
        if 'generateContent' in m.supported_generation_methods:
            available_models.append(m.name)

    # Lexifyで使える主要モデルをピックアップして解説
    print(f"✅ APIキーは有効です。以下のモデルが使用可能です（全{len(available_models)}個）：\n")
    
    # 注目すべきモデルの解説マップ
    recommendations = {
        "models/gemini-2.0-flash-exp": "🚀 [最新/推奨] 爆速かつVision性能が高い。デモに最適。",
        "models/gemini-1.5-pro":       "🧠 [高精度] 読み取りミスが最も少ない。複雑な比較分析向き。",
        "models/gemini-1.5-flash":     "⚡ [高速/安価] 1.5系の軽量版。2.0が出るまでの主力。",
        "models/gemini-1.5-pro-latest": "🆕 [1.5 Pro最新] 常に最新のProモデル。",
        "models/gemini-1.5-flash-8b":   "🏎️ [超軽量] 単純なタスク用。カタログ解析には不向きかも。",
    }

    # 一覧表示
    for model_name in available_models:
        print(f"・ {model_name}")
        if model_name in recommendations:
            print(f"   ↳ {recommendations[model_name]}")
            
    print("\n--------------------------------------------------")
    print("💡 Lexifyへの推奨:")
    if "models/gemini-2.0-flash-exp" in available_models:
        print("まずは 'models/gemini-2.0-flash-exp' を使いましょう。")
        print("もし回答が不安定なら 'models/gemini-1.5-pro' に切り替えるのがベストです。")
    else:
        print("'models/gemini-1.5-pro' を使用してください。")

except Exception as e:
    print(f"❌ エラーが発生しました: {e}")
    print("APIキーが正しいか、通信環境を確認してください。")