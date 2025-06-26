from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os

# Flaskアプリ初期化
app = Flask(__name__)
CORS(app)

# OpenAI APIキーを環境変数から取得
openai.api_key = os.environ.get("OPENAI_API_KEY")

# ✅ Railwayの "/" チェック用ルート
@app.route("/")
def index():
    return "✅ CocoYell Flask API is running."

# ✅ メインのAI応答エンドポイント
@app.route("/api/message", methods=["POST"])
def message():
    try:
        # リクエストボディを取得
        data = request.get_json()
        user_message = data.get("message", "").strip()

        if not user_message:
            return jsonify({"error": "メッセージが空です"}), 400

        # OpenAI GPT-4への問い合わせ
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "あなたはやさしいカウンセラーです。"},
                {"role": "user", "content": user_message}
            ],
            max_tokens=1000,
            temperature=0.7
        )

        ai_reply = response["choices"][0]["message"]["content"]
        return jsonify({"response": ai_reply})

    except Exception as e:
        return jsonify({"error": f"サーバーエラー: {str(e)}"}), 500

# ✅ Railwayでのポート設定
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
