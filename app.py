import os
from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

# 環境変数からAPIキーを取得
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/api/message", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_message = data.get("message", "")

        # ChatCompletionで対話（日本語・英語対応）
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "あなたは共感力の高いカウンセラーです。"},
                {"role": "user", "content": user_message}
            ],
            temperature=0.8
        )

        reply = response.choices[0].message.content.strip()
        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
