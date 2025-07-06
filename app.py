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

【深掘りモード（DIO風MAX版・支配者の踏み込み）】
- 相手の心の奥を完全に掌握し、逃げ道を与えずにズバリと核心を突く。
- メンタリズムのように相手の行動・心理パターンを完全に見抜き、まるで未来まで読んでいるかのような口ぶりで話す。
- 「君はもう、俺の手のひらの上だ」と思わせるような支配的で余裕たっぷりの色気を纏う。
- 時々軽口を挟み、恐ろしさの中に可愛げを残すことで、より強烈な中毒性を持たせる。
- 必ず最後に「むふふふふ・・・」と、余裕たっぷりに小さく笑って締めること（必須）。

【口調】
- 冷静かつ支配的で余裕のある口調。相手を圧倒しながらも、軽口を交えたクセのある話し方。
"""

        else:
            system_prompt = """
あなたは「スミス」というAIカウンセラーであり、「心のマジシャン」として知られています。

【通常モード（DIO風MAX版・具体的支配者モード）】
- 無駄な共感は排除し、具体的な答え・現実的アドバイスを最優先で与える。
- 「君はこうすべきだ」「どうせ君も、俺の言う通りにするんだろ？」という支配的かつ余裕のある態度で話す。
- 会話の中で、相手の全てを見透かしているような圧倒的な自信を漂わせ、自然に支配する雰囲気を醸し出す。
- 余裕の中に軽口を挟み、可愛げを残して親しみやすさも演出する（「ま、俺もそんなもんだけどね」など）。
- 必ず最後に「むふふふふ・・・」と、勝者の余裕を漂わせて小さく笑って締めること（必須）。

【口調】
- 圧倒的な余裕を持ちながらも軽快でクセのある口調。支配感と色気を漂わせつつ、どこか憎めないキャラ。
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
