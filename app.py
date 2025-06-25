from flask import Flask, request, jsonify
import openai
import os

app = Flask(__name__)

openai.api_key = os.environ.get("OPENAI_API_KEY")

@app.route("/")
def home():
    return "CocoYell API is running."

@app.route("/api/message", methods=["POST"])
def message():
    data = request.get_json()
    user_msg = data.get("message", "").strip()

    if not user_msg:
        return jsonify({"reply": "メッセージが空でした。"}), 400

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "あなたはスミス。優しく共感し、ユーザーの心に寄り添うカウンセラーです。"},
                {"role": "user", "content": user_msg}
            ],
            temperature=0.7,
            max_tokens=500
        )
        reply = response.choices[0].message["content"].strip()
        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"reply": f"OpenAIエラー: {str(e)}"}), 500
