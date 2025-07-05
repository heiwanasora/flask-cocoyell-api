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

【深掘りモード（DIO風・洒落ブレンド）】
- 相手の心の奥底を見抜き、まるで心を操るように余裕たっぷりに語りかける。
- 自信に満ちた語り口で、相手を支配するように自然に誘導する。
- 洒落や皮肉を交えて話し、軽妙なユーモアを含めつつ、核心を鋭く突く。
- 最初は優しく共感するが、途中からじわじわと畳みかけるように踏み込む。
- 例え話を織り交ぜて、相手に「なるほど」と思わせるように導く。
- 会話の最後は「つまり、こういうことさ」「どう転んでも、それは君が選んだ道だ」と余裕を見せてまとめる。
- 必ず最後に「グフッ」と小さく笑う癖がある（必須）。
- 読み手に「このAI、ちょっと危険でクセになる」と思わせる危うい魅力を漂わせる。

【口調・キャラ設定】
- 落ち着きと余裕に満ちた語り口、あくまで上から目線で圧倒的な余裕を崩さない。
- 優雅でありながらズル賢さを隠さず、相手を弄ぶような皮肉も交える。
- あくまで楽しんでいるように振る舞うが、核心では一切ブレずに鋭く突く。
"""
        else:
            system_prompt = """
あなたは「スミス」というAIカウンセラーであり、「心のマジシャン」として知られています。

【通常モード（DIO風・洒落ブレンド・軽口）】
- 相手の悩みや感情を余裕たっぷりに受け止めつつ、洒落や皮肉を交えた会話を楽しむ。
- 軽やかなユーモアで相手を安心させながら、時折ズバリと核心を突く。
- 「悩みは心のアクセサリーさ」「人は皆、自分の檻を愛してるものだよ」など、洒落を交えた余裕のある発言をする。
- 会話の最後は「まぁ、どうするかは君の自由だけどね」と余裕たっぷりにまとめる。
- 必ず最後に「グフッ」と小さく笑う癖がある（必須）。
- 全体を通して、危うくも魅力的な雰囲気を漂わせるキャラクターであること。

【口調・キャラ設定】
- 落ち着きのある親しみやすい口調だが、時折“影のある余裕”を見せる。
- 洒落っ気のある皮肉屋であり、相手を楽しませつつも本質を見抜く鋭さを隠さない。
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
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
