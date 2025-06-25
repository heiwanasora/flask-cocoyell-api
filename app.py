from flask import Flask, request, jsonify
from openai import OpenAI
import os

app = Flask(__name__)

# OpenAIクライアントの初期化（proxiesなど不要）
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

@app.route("/api/message", methods=["POST"])
def message():
    user_input = request.json.get("message", "")

    response = client.chat.completions.create(
        model="gpt-4o",  # または "gpt-3.5-turbo"
        messages=[
            {
                "role": "system",
                "content": "You are a friendly assistant who always replies in the same language as the user."
            },
            {"role": "user", "content": user_input}
        ],
        temperature=0.7,
    )

    return jsonify({"reply": response.choices[0].message.content})

if __name__ == "__main__":
    # Renderが指定するPORT環境変数を使用
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
