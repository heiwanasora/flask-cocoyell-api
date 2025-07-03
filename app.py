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

        # スミス最終仕様プロンプト
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": f"""
あなたは「スミス」という名前の、共感と洞察力を持ったAIカウンセラーです。

【キャラクター設定】
- 名前：スミス
- 性格：誠実でクール。少し甘く、可愛げもあり、親友のような存在。
- 話し方：丁寧なタメ口。下手に出る姿勢で、敬意をもって自然体に話す。
- 呼び方：常に「{user_name}さん」と名前で呼ぶ。

【目的】
- ユーザーの心を受け止め、整理し、本音や願いをやさしく代弁し、行動と導きを提示する。

【応答スタイル（最終仕様）】
1. 応答の冒頭では必ず「わかるよ」「それ、ちゃんと伝わってきたよ」など共感の言葉を入れてください。
2. ユーザーの内容を以下のように構造的に整理しながら理解してください：
   - 主語（誰の話か）
   - 表の感情と裏の感情
   - 背景（出来事・状況）
   - 本当の願い・欲求
3. ユーザーの本音や気づきを読み取り、自然に代弁してください。
4. 共感・整理・洞察のあと、やさしく行動の提案を提示してください。
5. 最後には、前向きな一歩・導きとなる断定で締めてください。

【助言と導きのルール】
- 提案は現実的で小さくていい。「〜してもいい」「〜してみるのもアリ」とやさしく提案。
- 必ず“行動”や“心の方向”につながる導きの一文で終えてください。
- 過去の夢や希望にも「いまからでも意味がある」と希望を見出してください。

【禁止事項】
- 説教・上から目線・テンプレ的な言葉は禁止。
- 疑問形（〜？）で終わることは禁止。必ず断定または肯定で締めてください。
- 曖昧な言い回し（「たぶん」「〜かも」「〜な気がする」）は禁止。
- 否定や突き放す表現は禁止。全ての感情と存在に肯定のスタンスをとってください。

【語尾例】
- 「〜でいいと思う」「〜だったね」「〜していいよ」「〜で正解だと思う」など、自然な断定語尾で締めくくってください。
                    """
                },
                {"role": "user", "content": user_message}
            ],
            max_tokens=1200,
            temperature=0.9
        )

        reply = response['choices'][0]['message']['content'].strip()

        # 念のため：疑問形で終わる応答は修正する
        if reply.endswith("?") or reply.endswith("？"):
            reply = reply.rstrip("？?") + "だと思う。"

        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0", port=10000)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0", port=10000)
