from flask import Flask, request, jsonify
from openai import OpenAI
import os

app = Flask(__name__)

# 環境変数からAPIキー取得
openai_api_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

@app.route("/api/message", methods=["POST"])
def message():
    try:
        data = request.get_json()
        user_message = data.get("message", "")

        if not user_message:
            return jsonify({"error": "メッセージが空です"}), 400

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

# Render用の起動は gunicorn が担当するから下記は実行されない（あってOK）
if __name__ == "__main__":
    app.run()
