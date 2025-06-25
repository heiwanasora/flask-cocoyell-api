from flask import Flask, request, jsonify
import openai
import os

app = Flask(__name__)

# OpenAI APIキーの設定（最新版SDKではこう書く）
openai.api_key = os.environ.get("OPENAI_API_KEY")

@app.route("/api/message", methods=["POST"])
def message():
    user_input = request.json.get("message", "")

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # 必要なら "gpt-4o" に変更
        messages=[
            {"role": "system", "content": "You are a kind assistant who replies in the user's language."},
            {"role": "user", "content": user_input}
        ],
        temperature=0.7,
    )

    return jsonify({"reply": response.choices[0].message["content"]})

if __name__ == "__main__":
    app.run(debug=True)
