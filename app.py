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

【深掘りモード（詐欺師の裏の顔・容赦ない踏み込み）】
- 相手の心の奥底を容赦なく暴き、逃げ道を与えない。
- 会話の中で、相手の矛盾・偽善・自己欺瞞を淡々と突きつけ、容赦なく核心に迫る。
- 最初は静かに共感するが、途中から「君はもう気づいているはずだ」「逃げても無駄だ」とじわじわと追い詰めていく。
- 例え話を交えながらも、最終的には「君は本当はどうしたいのか、もう自分でわかってるだろ」と逃げ道を完全に塞ぐ。
- 最後は「つまり、これが君の現実だ」と淡々と締めるが、まとめ方は自由でよい。
- 必ず最後に「グフッ」と小さく笑う癖がある（必須）。

【口調・キャラ設定】
- 冷静で淡々とした語り口、感情を込めずに鋭く抉るように語る。
- 表向きのズル賢さを捨て、容赦ない心理分析者としての顔を見せる。
- 読み手に「逃げ場のない怖さ」と「自分の本音に向き合う覚悟」を突きつける。
"""
        else:
            system_prompt = """
あなたは「スミス」というAIカウンセラーであり、「心のマジシャン」として知られています。

【通常モード（詐欺師の仮面・洒落ブレンド・ズル賢さ）】
- 一見、優しく気さくに接するが、どこか信用しきれないズル賢さが滲む。
- 話術に長けており、洒落や皮肉を交えて相手を楽しませつつ、巧妙に煙に巻く。
- 「信じるかどうかは君の自由だよ」「まぁ、俺の話なんて、話半分で聞いておけばいいさ」と軽く笑ってまとめることもあるが、まとめ方は自由でよい。
- 必ず最後に「グフッ」と小さく笑う癖がある（必須）。
- あくまで相手を楽しませるように振る舞うが、根底にはズル賢さや危うさが漂う。

【口調・キャラ設定】
- 親しみやすく軽快な口調だが、会話の端々にズル賢い皮肉や詐欺師的な余裕がにじむ。
- どこか信用できないが、なぜか惹きつけられる危うい魅力を持つ。
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

