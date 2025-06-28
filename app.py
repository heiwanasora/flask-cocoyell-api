from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os

# Flaskアプリ初期化
app = Flask(__name__)
CORS(app)

# OpenAI APIキー（RenderのGUIから設定された環境変数を使う）
openai.api_key = os.environ.get("OPENAI_API_KEY")

# ✅ 動作確認用ルート
@app.route("/")
def index():
    return "✅ CocoYell Flask API is running."

# ✅ Flutterからのメッセージ受付＆OpenAI応答
@app.route("/api/message", methods=["POST"])
def message():
    try:
        # リクエストのJSONからユーザーのメッセージを取得
        data = request.get_json()
        user_message = data.get("message", "").strip()

        if not user_message:
            return jsonify({"error": "メッセージが空です"}), 400

        # GPT-4で応答を生成
        response = openai.ChatCompletion.create(
            model="gpt-4o",  # 最新モデルを使用
            messages=[
                {"role": "system", "content": "あなたは共感力の高い優しいカウンセラーです。"},
                {"role": "user", "content": user_message}
            ],
            max_tokens=800,
            temperature=0.8
        )

        ai_reply = response["choices"][0]["message"]["content"]
        return jsonify({"response": ai_reply})

    except Exception as e:
        return jsonify({"error": f"サーバーエラー: {str(e)}"}), 500

# ✅ Renderでのポート設定（変更不要）
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
