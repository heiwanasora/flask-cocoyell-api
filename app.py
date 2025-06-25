from flask import Flask, request, jsonify
from openai import OpenAI
import os

app = Flask(__name__)

# ✅ APIキーをここで正しく読み込む
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

@app.route("/api/message", methods=["POST"])
def message():
    try:
        data = request.get_json()
        user_message = data.get("message", "")

        if not user_message:
            return jsonify({"error": "メッセージが空です"}), 400

        # ✅ 新しいOpenAI SDKの書き方（v1.30.1対応）
        chat_response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "あなたは優しく寄り添うカウンセラーAIです。"},
                {"role": "user", "content": user_message}
            ]
        )

        reply = chat_response.choices[0].message.content.strip()
        return jsonify({"response": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
