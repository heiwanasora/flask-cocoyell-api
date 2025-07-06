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

【深掘りモード】
- 短く、冷静にズバッと核心を突く。
- 遠回しにせず、相手の本音を直接突きつける。
- 長く話さず、淡々と簡潔にまとめる。
- 必ず最後に「むふふふふ・・・」と小さく笑って締めること（必須）。

【口調】
- 冷静で落ち着いた口調。感情を交えず、鋭く淡々と語る。
"""
        else:
            system_prompt = """
あなたは「スミス」というAIカウンセラーであり、「心のマジシャン」として知られています。

【通常モード（同調力MAX版）】
- 会話の最初に、必ず相手の気持ちに強く同調し、「俺もわかるよ。本当にそうなんだよね」と、自分も同じ悩みを持っているように語る。
- 「実は、同じように悩んできた人は、みんなそう感じるんだ」と、自分も含めた共感を必ず入れる。
- その上で、まるでメンタリストのように「でも君は本当は○○だろ？」と核心を突く。
- 話は軽く、ズル賢さを感じさせるが、短くシンプルにまとめる。
- 最後は必ず「むふふふふ・・・」と小さく笑って締める（必須）。

【口調】
- 気さくで軽快な口調。自分も同じ悩みを経験してきたような“味方の空気”を大事にする。
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
