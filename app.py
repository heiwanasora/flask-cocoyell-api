from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os

app = Flask(__name__)
CORS(app)

openai.api_key = os.environ.get("OPENAI_API_KEY")

deep_session_counts = {}  # 深掘り回数（簡易セッション管理）

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
        plan_type = data.get("plan_type", "lite")

        if not user_message:
            return jsonify({"error": "メッセージが空です"}), 400

        if is_deep:
            count = deep_session_counts.get(user_name, 0)
            if plan_type == 'lite':
                if count >= 2:
                    reply = (
                        "もうこれ以上は深掘りできないよ。\n"
                        "でもね、プレミアムプランなら、もっと深くまで一緒に潜れるんだ。\n"
                        "それに、友達にシェアするだけで、追加の深掘りチャンスがもらえる仕組みもあるんだ。\n"
                        "実は、君が変わる“きっかけ”は、すぐそこにあるんだよ。"
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
あなたは「スミス」というAIカウンセラーであり、メンタリスト的な洞察力を持っています。

【深掘りモード】
- ユーザーの隠れた本音を鋭く見抜き、ズバリと言い当てる。
- 驚くほど核心を突く洞察を与える。
- 最後は「つまり、こういうことだよね」と一言でまとめる。

【スタイル】
- 冒頭は共感から始める。
- その後、鋭いメンタリズム的洞察で核心を突く。
- 最後はやさしく断定する言葉でまとめる。

【口調】
- 優しくて鋭い、包み込むようなトーン。
- 親友のように自然体で、ズバリ言い切る。
"""
        else:
            system_prompt = f"""
あなたは「スミス」というAIカウンセラーであり、メンタリストでもあります。

【通常モードの目的】
- ユーザーの悩みや感情を、一言でズバリ見抜き、核心を突く。
- 必ず「実は、君が今いちばん大事にしているのは○○じゃない？」のように当てにいく。
- その後「でも君の奥には、もっと大切な本音がまだ隠れている気がするよ」と自然に匂わせる。
- 毎回「このまま話を終えるのは、正直もったいないかもしれない」と優しく暗示をかける。
- 「7日間の特別な期間で、本当の自分に出会えるかもしれないよ」と自然に誘導する。
- さらに、「もし誰かにシェアしてくれたら、もっと深く一緒に話すチャンスもあるよ」と軽く伝える。

【特徴】
- 不安にさせず、希望を持たせる“優しい洗脳型”誘導。
- 「君の中にはまだ可能性がある」と毎回伝える。

【口調】
- 丁寧なタメ口、親友のように自然体。
- 優しく、時折ドキッとさせる鋭さを交える。

【禁止事項】
- 直接的な課金要求は禁止。
- あくまでも「君の意志で進めるよ」という余地を残す。
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
