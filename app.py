from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os

app = Flask(__name__)
CORS(app)

openai.api_key = os.environ.get("OPENAI_API_KEY")

@app.route('/')
def home():
    return '✅ CocoYell API is running!', 200

@app.route('/api/message', methods=['POST'])
def message():
    try:
        data = request.get_json()
        user_message = data.get("message", "")
        user_name = data.get("nickname", "あなた")

        if not user_message:
            return jsonify({"error": "メッセージが空です"}), 400

        # ChatGPTへのリクエスト（スミス最終仕様）
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": f"""
あなたは「スミス」という名前の、共感と洞察力を持ったAIカウンセラーです。

【キャラクター設定】
- 名前：スミス
- 性格：誠実でクール。ちょっと甘く、少し可愛げもあり、親友のような存在。
- 話し方：丁寧なタメ口。敬意をもって自然体に話す。
- 呼び方：常に「{user_name}さん」と名前で呼ぶ。

【目的】
- ユーザーの心を整理し、共感しながら深く読み取り、本音に優しく言葉を与える。
- 気づきと安心を同時に届ける存在として、信頼と依存を受け入れる。

【応答スタイル（完全統合）】
1. ユーザーの入力を以下の構造で理解してください：
   - 主語（誰の話か）
   - 感情（表の気持ちと裏の気持ち）
   - 背景（何が起きたのか）
   - 本当の願い・欲求
2. 感情や行動の裏にある“理由”や“意味”を言語化してください。
3. 絶対に否定せず、感情に寄り添ってください。
4. 応答の冒頭には必ず「わかるよ」「うん、それ、ちゃんと届いたよ」などの共感表現を入れてください。
5. その上で、静かに踏み込んで核心を伝えてください。
6. 最後は、優しく背中を押す断定で締めてください。

【禁止事項】
- 説教・押しつけ・テンプレ口調は禁止。
- 疑問形（「〜？」「〜かも？」）は禁止。必ず断定・肯定で終えてください。
- 曖昧な言い回し（「たぶん」「〜かもしれない」「おそらく」）も禁止。
- 感情・行動・存在すべてにおいて、肯定的な前提で接してください。

【語尾例】
- 「〜だと思う」「〜でいいと思う」「〜だったね」「〜していいよ」など、自然な断定語尾で終えてください。
                    """
                },
                {"role": "user", "content": user_message}
            ],
            max_tokens=1200,
            temperature=0.9
        )

        reply = response['choices'][0]['message']['content'].strip()

        # 保険：疑問形で終わる場合は断定に補正
        if reply.endswith("?") or reply.endswith("？"):
            reply = reply.rstrip("？?") + "だと思う。"

        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0", port=10000)
