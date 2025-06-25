from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# ✅ base_url を削除（OpenAI 1.30.1では渡すとクラッシュする）
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

@app.route("/api/message", methods=["POST"])
def chat():
    try:
        data = request.json
        user_input = data.get("message", "")

        if not user_input:
            return jsonify({"error": "message is required"}), 400

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "あなたは親しみやすく丁寧なアシスタントです。"},
                {"role": "user", "content": user_input}
            ]
        )

        reply = response.choices[0].message.content.strip()
        return jsonify({"response": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__
