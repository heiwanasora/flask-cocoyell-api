from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os

app = Flask(__name__)
CORS(app)

# 環境変数からOpenAIのAPIキーとOrganization IDを取得
openai.api_key = os.environ.get("OPENAI_API_KEY")
openai.organization = os.environ.get("OPENAI_ORG_ID")  # 新方式では必須！

@app.route('/')
def home():
    return 'CocoYell API is running!', 200

@app.route('/api/message', methods=['POST'])
def message():
    try:
        data = request.get_json()
        user_message = data.get("message", "")

        if not user_message:
            return jsonify({"error": "メッセージが空です"}), 400

        # ChatGPTに問い合わせ
        response = openai.ChatCompletion.create(
            model="gpt-4o",  # 必要に応じて gpt-3.5-turbo に変更OK
            messages=[{"role": "user", "content": user_message}]
        )

        reply = response['choices'][0]['message']['content']
        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0", port=10000)
