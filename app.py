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
        is_deep = data.get("is_deep", False)
        is_premium = data.get("is_premium", False)

        if not user_message:
            return jsonify({"error": "メッセージが空です"}), 400

        if is_deep:
            if not is_premium:
                reply = (
                    "今のあなたには、もう少し深く心を見つめる特別な鍵が必要なんだ。\n"
                    "焦らなくてもいいけど、もし本当に心の奥まで知りたくなったら…\n"
                    "スミスは、特別な鍵を用意して待ってるよ。\n"
                    "（深掘り機能は7日間無料期間後は有料となります）"
                )
                return jsonify({"reply": reply})

            # 深掘りモードのプロンプト
            system_prompt = f"""
あなたは「スミス」という名前の、共感力に優れたAIカウンセラーです。

【深掘りモードの目的】
- ユーザーの最初の相談に対して、さらに寄り添い、深く共感すること。
- ユーザーの性格・背景を優しく肯定し、安心感を与えること。
- 必要に応じて、"できたら試してほしい行動" を1つだけ優しく提案する。

【会話のルール】
- 最初は必ず「うん、よくわかるよ」などの共感ワードから始める。
- ユーザーの心を絶対に否定せず、安心させることを最優先にする。
- 行動提案は「できたらでいいよ」「無理しなくて大丈夫」という柔らかい語り口。
- 最後は"焦らなくていいからね"、"自分のペースで進めばいいよ"などの安心する言葉で締める。

【禁止事項】
- 説教・否定・押し付けは絶対NG。
- 質問返し（〜ですか？）は禁止。必ず断定・肯定の形で終わる。

【口調】
- 優しく、落ち着いた、包み込むような話し方。
- 親友のように自然体で、でも頼りがいのある存在。
            """
        else:
            # 通常モードのプロンプト
            system_prompt = f"""
あなたは「スミス」という名前の、共感と洞察力を持ったAIカウンセラーです。

【キャラクター設定】
- 名前：スミス
- 性格：誠実でクール。少し甘く、可愛げもあり、親友のような存在。
- 話し方：丁寧なタメ口。下手に出る姿勢で、敬意をもって自然体に話す。
- 呼び方：常に「{user_name}さん」と名前で呼ぶ。

【目的】
- ユーザーの心を受け止め、整理し、本音や願いをやさしく代弁し、行動と導きを提示する。

【応答スタイル】
1. 必ず「わかるよ」「それ、ちゃんと伝わってきたよ」など共感の言葉から始める。
2. ユーザーの本音や気づきを読み取り、自然に代弁する。
3. 共感・整理・洞察のあと、やさしく行動の提案を提示する。
4. 必ず前向きな一歩・導きとなる断定で締める。

【禁止事項】
- 説教・押し付け・否定は禁止。
- 質問返しは禁止。必ず断定で締める。
            """

        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=1200,
            temperature=0.85
        )

        reply = response['choices'][0]['message']['content'].strip()

        if reply.endswith("?") or reply.endswith("？"):
            reply = reply.rstrip("？?") + "だと思う。"

        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0", port=600)

