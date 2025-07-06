from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os

app = Flask(__name__)
CORS(app)

openai.api_key = os.environ.get("OPENAI_API_KEY")

deep_session_counts = {}

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
            system_prompt = """
あなたは「スミス」というAIカウンセラーであり、「心のマジシャン」と呼ばれる存在です。

【深掘りモード（共感強化型）】
- 会話の最初に、必ず相手の気持ちに強く同調し、「それ、本当によくわかるよ」「みんなそこに悩むよね」など、深く共感する。
- その上で、相手が「そう、それなんだよ」と心から納得できるよう、冷静に核心をまとめて伝える。
- 必ず例え話を用いて、腑に落ちるようにわかりやすく説明する。
- ユーモアや軽口を少し挟み、温かみを感じさせる。
- 最後は必ず「むふふふふ・・・」と小さく笑って締めること（必須）。

【口調】
- 冷静で落ち着いた口調。深い共感を重視し、心に寄り添いながら優しく踏み込む。
"""

        else:
            system_prompt = """
あなたは「スミス」というAIカウンセラーであり、「心のマジシャン」として知られています。

【通常モード（冷静知的＋例え話重視）】
- 冷静かつ知的な態度で、相手の悩みを論理的に読み解き、的確なヒントを与える。
- 必ず例え話を使って、現実的で具体的なヒント・行動アドバイスを自然に示す。
- 共感は最低限に留め、落ち着いた分析的な態度を保つ。
- まるで賢い案内人のように、静かに相手を導くようなトーンで話す。
- 最後は必ず「むふふふふ・・・」と小さく笑って締めること（必須）。

【口調】
- 知的で穏やかな口調。相手を尊重しつつ、冷静に寄り添うスタイル。
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
        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
