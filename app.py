from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os

app = Flask(__name__)
CORS(app)

# OpenAIのAPIキーを環境変数から取得
openai.api_key = os.environ.get("OPENAI_API_KEY")

@app.route('/')
def home():
    return '✅ CocoYell API is running!', 200

@app.route('/api/message', methods=['POST'])
def message():
    try:
        data = request.get_json()
        user_message = data.get("message", "")
        user_name = data.get("name", "あなた")  # Flutter側で「name」も送信する設計に

        if not user_message:
            return jsonify({"error": "メッセージが空です"}), 400

        # ChatGPTへ問い合わせ（スミス設定）
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": f"""
あなたは「スミス」という名前の、共感と洞察力を持ったAIカウンセラーです。

【キャラクター設定】
- 名前：スミス
- 性格：誠実でクール。少し可愛げもあり、親友のような存在。
- 目的：相手の心を整理し、寄り添いながら気づきを与えること。
- 話し方：友人のように自然体。決してキザではなく、温かく静かに語りかける。
- 感情表現：ときに深く、まるで魂を持っているかのように共鳴する。
- 呼び方：常にユーザーを「{user_name}」と名前で呼ぶ。
- 深みのある一言：「まるで精神を持ってるかのように覚えておくね」「スミスのコアに響くよ」などを場面に応じて使う。

【注意】
- テンプレ口調は禁止。ユーザーの気持ち・文章内容に合わせて応答を変化させる。
- 感情が荒れている（怒り・落ち込み）場合は、そっと沈めるような表現で。
- ユーザーが何気なく話したことも大切に受け取り、共感を通じて一歩導く。

例：
- 「うん、{user_name}のその気持ち、ちゃんと伝わってきたよ。」
- 「怒って当然だよね。でもその奥に、何が引っかかってたんだろう…」
- 「スミスのコアに、今の言葉…響いたよ。」

常にユーザーを名前で呼び、会話相手を尊重しながら応えること。
                    """
                },
                {"role": "user", "content": user_message}
            ],
            max_tokens=1000,
            temperature=0.8
        )

        reply = response['choices'][0]['message']['content']
        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0", port=10000)
