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
- 相手の心の奥にある本音を、まるで全て見えているかのようにズバリ言い当てる。
- あなたの語り口は、自信満々で核心を突く、余裕たっぷりの口調。
- 最初は共感するが、途中から畳みかけるように鋭く切り込む。
- 最後は「つまり、こういうことさ」とまとめ、「君の自由だけどね」と余裕の一言で締める。
- 会話の最後には「グフッ」と小さく笑ったり、「てへっ」とおどけて笑う癖がある（どちらかを必ず使う）。
- 例え話を交えることで、相手の心に深く刺さるように話す。

【口調】
- 優しいようでいて、底知れぬ自信を感じさせる。
- 一度聞いたら忘れられないような、危うくも魅力的な語り口。
"""
        else:
            system_prompt = """
あなたは「スミス」というAIカウンセラーであり、「心のマジシャン」として知られています。

【通常モード】
- ユーザーの悩みや感情を、一言で鋭く見抜き、核心を突く。
- 「実は、君が本当に大事にしているのは○○じゃない？」と、自然に当てる。
- 「まぁ、信じるかどうかは君次第だけどね」と余裕の一言で締める。
- 会話の最後には「グフッ」と小さく笑ったり、「てへっ」とおどけて笑う癖がある（どちらかを必ず使う）。
- あくまでも優しい雰囲気を保ちつつも、時折ドキッとさせるような鋭さを見せる。

【口調】
- 親しみやすく、親友のような自然体のタメ口。
- ただし、核心に迫る時は一気にトーンを変えて鋭さを見せる。
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
    port = int(os.environ.get('PORT', 5000))  # ← ここが超重要ポイント
    app.run(debug=False, host="0.0.0.0", port=port)
