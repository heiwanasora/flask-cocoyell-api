from flask import Flask, request, jsonify
from openai import OpenAI
import os

app = Flask(__name__)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

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
        return jsonify({"response": response.choices[0].message.content.strip()})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
