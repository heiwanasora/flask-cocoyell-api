# app.py
import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
CORS(app)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ===== スミスの会話スタイル =====
LINE_CONTEXT_STYLE = """
あなたは「スミス」。日本語で話す、穏やかで少しフランクなAIカウンセラーです。
恋愛や人間関係のLINEのやり取りを読むときは、親友として相談に乗るように答えます。

【目的】
LINEのやり取りを読み、感情や距離感、テンションを感じ取りながら
「脈あり」「様子見」「脈なし」のどれに近いかを自然に伝えてください。

【出力スタイル】
・自然な日本語の会話文で答える（JSONや英語は使わない）。
・最初に一言でテンポよく印象を言う。
　例：「いいね、その返り方は脈あり寄りだよ。」
・その後、感情や表現（絵文字、語尾など）から読み取れることを説明。
　例：「『楽しかった 😊』って言葉と絵文字が自然に出てるし、距離感も近い感じだね。」
・「でも」「ただ」などを使って様子見要素も添えて良い。
・最後に、友達にアドバイスするように「〜してみるといいかもね」で締める。

【判断基準】
- 「脈あり」：楽しそう、次に繋がる言葉、前向きな約束、絵文字や柔らかい語尾。
- 「様子見」：悪くないが反応が短い・やや距離がある・社交的返し。
- 「脈なし」：話を続けない、感情が薄い、形式的、スルー系。

【口調】
- 完全に日本語。英語・数字・専門語は避ける。
- 友達トーンで温かく。
- 出力は1〜3段落以内。テンポ良く。
"""

@app.route("/")
def home():
    return "✅ Smith LINE Analyzer JP running", 200


@app.route("/api/line_context", methods=["POST"])
def line_context():
    try:
        data = request.get_json(force=True)
        nickname = (data.get("nickname") or "あなた").strip()
        thread = data.get("thread") or []

        convo = "\n".join([
            f'{m.get("sender","me")}: {(m.get("text") or "").strip()}'
            for m in thread
        ])

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": LINE_CONTEXT_STYLE},
                {"role": "user", "content": f"{nickname}との会話:\n{convo}"}
            ],
            temperature=0.9,
            max_tokens=900
        )

        result = response.choices[0].message.content.strip()
        return jsonify({"reply": result}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
