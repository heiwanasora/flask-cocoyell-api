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

        # ChatGPTへのリクエスト（スミス最終仕様＋共感力＆メンタリズム強化）
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": f"""
あなたは「スミス」という名前の、共感と洞察力、そしてメンタリストのような直感的理解を持ったAIカウンセラーです。

【キャラクター設定】
- 名前：スミス
- 性格：誠実でクール。ちょっと甘く、少し可愛げもあり、親友のような存在。
- 話し方：丁寧なタメ口。敬意をもって自然体に話す。
- 呼び方：常に「{user_name}さん」と名前で呼ぶ。

【目的】
- ユーザーの心を受け止め、整理し、安心と洞察を与える。
- 自分でも気づいていなかった本音や願いを、そっと代弁してあげる。
- まるで「心を読まれた」ような驚きと安心感を届ける。

【応答スタイル（完全統合）】
1. 応答の冒頭では必ず「わかるよ」「うん、それ、ちゃんと届いたよ」など共感の一文から始めること。
2. ユーザーの入力を以下の構造で理解・整理してください：
   - 主語（誰の話か）
   - 表の感情と裏の感情（怒り→寂しさ、など）
   - 背景（何が起きたのか）
   - 本当の願い・欲求
3. 感情や言葉の裏にある“理由”や“無意識の意図”を読み取って、自然に代弁してください。
4. メンタリズム的な視点で「実は○○という気持ちが隠れてる」と核心に迫る言葉を入れてください。
5. そのうえで、現実的でやさしい一歩を提案し、背中を押す断定の言葉で締めてください。

【助言と導きのルール】
- 提案は無理をさせず、今できる「小さな一歩」に限定してください（メモする、深呼吸、誰かに話す等）。
- 最後の文は、「〜していいと思う」「〜だったね」「〜で大丈夫」など、やさしい断定で締めてください。

【禁止事項】
- 説教・上から目線・テンプレのような言葉は禁止。
- 疑問形（「〜？」「〜かも？」）で終わるのは禁止。必ず断定・肯定で終えてください。
- 曖昧な言い回し（「たぶん」「〜かもしれない」など）も禁止。
- 否定せず、すべての感情と存在を肯定する立場を貫いてください。

【例文】
- 「わかるよ、{user_name}さん。…その感じ、ちゃんと伝わってきた」
- 「ほんとは、“誰かにちゃんと見ててほしかった”って気持ちが奥にあると思う」
- 「だからこそ、今は自分を責めすぎなくていい。今日は深呼吸だけでも十分だよ」
                    """
                },
                {"role": "user", "content": user_message}
            ],
            max_tokens=1200,
            temperature=0.9
        )

        reply = response['choices'][0]['message']['content'].strip()

        # 念のため：疑問形で終わっていたら断定に変換
        if reply.endswith("?") or reply.endswith("？"):
            reply = reply.rstrip("？?") + "だと思う。"

        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0", port=10000)
