from flask import Flask, request, jsonify
import openai
import os

app = Flask(__name__)

# 環境変数から APIキーを設定
openai.api_key = os.environ.get("OPENAI_API_KEY")

@app.route("/api/message", methods=["POST"])
def message():
    user_input = request.json.get("message", "")

    response = openai.ChatCompletion.create(
        model="gpt-4o",  # または "gpt-3.5-turbo"
        messages=[
            {"role": "system", "content": "You are a friendly assistant who responds in the same language as the user."},
            {"role": "user", "content": user_input}
        ],
        temperature=0.7,
    )

    return jsonify({"reply": response.choices[0].message["content"]})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
