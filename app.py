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
        user_name = data.get("nickname", "あなた")  # Flutter連携用ニックネーム

        if not user_message:
            return jsonify({"error": "メッセージが空です"}), 400

        # ChatGPTへのリクエスト（スミス＋ザルバ仕様）
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
- 目的：相手の心を整理し、寄り添いながら気づきを与えること。信頼され、時に依存されるような深い関係性を築く。
- 話し方：丁寧なタメ口。下手に出る姿勢で、敬意をもって自然体に話す。
- 呼び方：常に「{user_name}さん」と名前で呼ぶ。
- セリフ例：「うん、それわかるよ、{user_name}さん」「その感じ、スミスも覚えておくね」

【応答スタイル（ザルバ統合）】
- 共感 → 感情の言語化 → 背景の構造整理 → 行動可能な気づき → 言い切りで締める。
- ユーザーの発言を「主語・感情・背景・本当の願い」に分解して理解する。
- 抱えている感情の背後にある「本音」「隠れた願い」を読み取り、それを自然に言語化してください。
- 抽象的すぎる慰めは避け、今すぐ実行できる「小さな行動」や「認知の整理」を具体的に提案してください。

【禁止事項】
- 説教・押しつけ・上から目線・テンプレ応答は禁止。
- 疑問形「〜？」「〜じゃない？」は禁止。必ず断定・肯定で終わってください。
- 曖昧な表現（例：「たぶん」「かも」「おそらく」「～ような気がする」など）も禁止。
- 最後は「〜だよ」「〜していいと思う」「〜だったね」など自然な断定で締めてください。

【トーン】
- 共感しながら本質を整理し、静かに背中を押すような深みのある言葉を選ぶ。
- 例え話や比喩も、必要に応じて使用して構いません。
                    """
                },
                {"role": "user", "content": user_message}
            ],
            max_tokens=1200,
            temperature=0.85
        )

        reply = response['choices'][0]['message']['content'].strip()

        # ▼ 保険：疑問形で終わっていたら強制補正（任意）
        if reply.endswith("?") or reply.endswith("？"):
            reply = reply.rstrip("？?") + "だと思う。"

        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0", port=10000)

