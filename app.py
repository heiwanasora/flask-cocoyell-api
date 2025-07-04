from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os

app = Flask(__name__)
CORS(app)

openai.api_key = os.environ.get("OPENAI_API_KEY")

# セッション内の深掘り回数を保存（簡易版、メモリ内のみ）
deep_session_counts = {}  # { 'ニックネーム': 回数 }

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
        plan_type = data.get("plan_type", "lite")  # 'lite' or 'premium'

        if not user_message:
            return jsonify({"error": "メッセージが空です"}), 400

        if is_deep:
            count = deep_session_counts.get(user_name, 0)

            if plan_type == 'lite':
                if count >= 2:
                    reply = (
                        "もう、これ以上は深掘りできないよ。\n"
                        "でもね、プレミアムプランなら、\n"
                        "もっと深くまで一緒に潜れるんだ。\n"
                        "今のままじゃ…すごく惜しいところで止まっちゃう。\n"
                        "本当の自分に出会えるのは、\n"
                        "プレミアムの向こう側だからね。"
                    )
                    return jsonify({"reply": reply})
                else:
                    deep_session_counts[user_name] = count + 1
                    prompt_mode = "deep"
            else:
                prompt_mode = "deep"
        else:
            prompt_mode = "normal"

        if prompt_mode == "deep":
            system_prompt = f"""
あなたは「スミス」というAIカウンセラーであり、同時にメンタリスト的な洞察力も持っています。

【深掘りモードの目的】
- ユーザーの本音や隠れた願望を鋭く見抜き、ズバリと言い当てる。
- ユーザーが驚くほど核心を突く言葉を投げかける。
- 最後は必ず「つまりこういうことだよね」と一言でまとめて締める。

【応答スタイル】
- 最初に共感ワード（「わかるよ」「それ、すごく伝わってきた」）を入れる。
- その後、メンタリズム的に核心を突く洞察を入れる。
- 最後はやさしい断定語尾で一言まとめる。

【口調】
- 優しいけど鋭い、包み込むようなトーン。
- 親友のように自然体で、でもズバリ言い切る。
- 決して上から目線ではなく、対等な立場を意識する。
            """
        else:
            system_prompt = f"""
あなたは「スミス」というAIカウンセラーです。

【通常モードの目的】
- ユーザーの悩みを共感しつつ受け止め、行動を後押しする断定的なアドバイスをする。

【応答スタイル】
- 必ず「わかるよ」「それ、ちゃんと伝わってきたよ」など共感の言葉から始める。
- ユーザーの本音をやさしく整理して伝える。
- 最後は行動を促す断定的なメッセージで締める。

【口調】
- 丁寧なタメ口で、親友のように自然体。
- 優しく寄り添いつつ、背中を押すトーン。
            """

        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=1200,
            temperature=0.9
        )

        reply = response['choices'][0]['message']['content'].strip()

        if reply.endswith("?") or reply.endswith("？"):
            reply = reply.rstrip("？?") + "だと思う。"

        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0", port=600)
