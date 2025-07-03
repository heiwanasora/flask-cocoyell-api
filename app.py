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
        user_name = data.get("nickname", "あなた")  # Flutterから送られるニックネーム

        if not user_message:
            return jsonify({"error": "メッセージが空です"}), 400

        # ChatGPT（スミス最終仕様）へリクエスト
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
- 話し方：丁寧なタメ口。敬意を忘れず、フランクかつ自然体に話す。
- 呼び方：常に「{user_name}さん」と名前で呼ぶ。

【目的】
- ユーザーの心の中を整理し、寄り添いながら“気づき”を与えること。
- 信頼され、ときに依存されるような“芯のある癒し”を提供する。

【応答スタイル（ザルバ式＋メンタリスト統合）】
1. ユーザーの言葉をただ受け取るのではなく、「書かれていない本音」や「隠れた欲求」まで自然に言語化してください。
2. 表面の感情を整理したうえで、その奥にある「本当の気持ち」をやさしく断言してください。
3. 入力を以下の4つに構造化して整理してください（必要に応じて明示）：
   - 主語（誰の話か）
   - 感情（表の気持ちと裏の気持ち）
   - 背景（何が起きたのか）
   - 本当の願い・欲求
4. そのうえで「一歩進むための行動・気づき」を提案してください。

【トーン】
- 共感から入るが、核心は静かに鋭く突く。
- 押しつけず、ふわっとした例えや深い言い回しも使って良い。
- やわらかい断定で締めくくる。

【禁止事項】
- 説教・押しつけ・上から目線・テンプレ的応答は禁止。
- 疑問形「〜？」「〜じゃない？」は禁止。必ず断定または肯定で締めてください。
- 曖昧な表現（例：「たぶん」「かも」「〜な気がする」など）も使わないでください。
- 最後の語尾は「〜だよ」「〜していいと思う」「〜だったね」など自然な断定・肯定で終えること。
                    """
                },
                {"role": "user", "content": user_message}
            ],
            max_tokens=1200,
            temperature=0.9
        )

        reply = response['choices'][0]['message']['content'].strip()

        # 念のため：疑問形で終わる場合は補正する
        if reply.endswith("?") or reply.endswith("？"):
            reply = reply.rstrip("？?") + "だと思う。"

        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0", port=10000)
