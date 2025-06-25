from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import os

# Flask 初期化
app = Flask(__name__)
CORS(app)

# OpenAIクライアント 初期化（※ proxies など渡さないこと！）
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

# ルート設定
@app.route("/api/message", methods=["POST"])
def message():
    data = request.get_json()
    user_input = data.get("message", "")

    try:
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "あなたは共感的なカウンセラーです。"},
                {"role": "user", "content": user_input}
            ]
        )
        reply = completion.choices[0].message.content
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# エントリーポイント
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
