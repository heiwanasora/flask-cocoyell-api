from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os

# Flask初期化
app = Flask(__name__)
CORS(app)

# OpenAIのAPIキーを環境変数から取得
openai.api_key = os.environ.get("OPENAI_API_KEY")

@app.route("/api/message", methods=["POST"])
def message():
    try:
        data = request.get_json()
        user_message = data.get("message", "")

        if not user_message:
            return jsonify({"error": "No message provided"}), 400

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "あなたはやさしいカウンセラーです。"},
                {"role": "user", "content": user_message}
            ],
            max_tokens=1000,
            temperature=0.7
        )

        ai_reply = response["choices"][0]["message"]["content"]
        return jsonify({"response": ai_reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Railwayが自動でPORT環境変数を使う
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
