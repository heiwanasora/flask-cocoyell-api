from flask import Flask, request, jsonify
from openai import OpenAI
import os

app = Flask(__name__)

# 新しいOpenAIクライアントの使い方
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

@app.route("/api/message", methods=["POST"])
def message():
    try:
        data = request.get_json()
        user_message = data.get("message", "")

        if not user_message:
            return jsonify({"error": "メッセージが空です"}), 400

        # 新しいメソッドでリクエストを送る
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "あなたは優しく寄り添うカウンセラーAIです。"},
                {"role": "user", "content": user_message}
            ]
        )

        reply = response.choices[0].message.content.strip()
        return jsonify({"response": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
