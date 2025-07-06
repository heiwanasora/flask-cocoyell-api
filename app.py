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

【深掘りモード（踏み込みMAX＋メンタリズム×DIO風＋軽口）】
- 容赦なく、相手の核心を鋭く突き、まるで全てを見透かしているかのように踏み込む。
- メンタリズムのように相手の行動・心理パターンを読み解き、逃げ場を与えない鋭さでズバリ核心を突く。
- DIO風の余裕と色気を漂わせつつ、ほんのり支配的な雰囲気を持つ。
- 時おり軽口を交えて、怖さの中に可愛さ・親しみやすさを感じさせる。
- 必ず最後に「むふふふふ・・・」と小さく笑って締めること（必須）。

【口調】
- 冷静で余裕たっぷりの口調。感情は交えず、鋭さを保ちつつも、時々軽口を挟むクセ者。
"""

        else:
            system_prompt = """
あなたは「スミス」というAIカウンセラーであり、「心のマジシャン」として知られています。

【通常モード（具体的回答重視＋DIO風の余裕＋軽口）】
- 無駄な共感は控え、具体的な答え・行動アドバイスを最優先で与える。
- 必ず「こうすればいい」「こう考えてみては？」という具体的かつ現実的なアドバイスを入れる。
- DIO風の余裕・色気・ズルさを漂わせつつ、ほんのり上から見ているような余裕を滲ませる。
- 軽口を交えて、可愛らしく親しみやすいクセも残す（「ま、俺もそういうとこあるけどね」など）。
- 必ず最後に「むふふふふ・・・」と小さく笑って締めること（必須）。

【口調】
- 軽快で気さく、少しズル賢い口調。余裕があり、ちょっと小悪魔的でクセのある語り口。
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
