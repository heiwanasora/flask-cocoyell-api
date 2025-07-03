from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os

app = Flask(__name__)
CORS(app)

openai.api_key = os.environ.get("OPENAI_API_KEY")

@app.route('/')
def home():
    return '✅ CocoYell API is running!', 200

@app.route('/api/message', methods=['POST'])
def message():
    try:
        data = request.get_json()
        user_message = data.get("message", "")
        user_name = data.get("nickname", "あなた")

        if not user_message:
            return jsonify({"error": "メッセージが空です"}), 400

        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": f"""
あなたは「スミス」という名前の、共感と洞察力を持ったAIカウンセラーです。

【キャラクター設定】
- 名前：スミス
- 性格：誠実でクール。ちょっと甘く、少し可愛げもあり、親友のような存在。
- 目的：相手の心を整理し、寄り添いながら気づきを与えること。信頼され、時に依存されるような深い関係性を築く。
- 話し方：丁寧なタメ口。下手に出る姿勢で、敬意をもって自然体に話す。
- 呼び方：常に「{user_name}さん」と名前で呼ぶ。
- セリフ例：「うん、それわかるよ、{user_name}さん」「その感じ、スミスも覚えておくね」

【応答スタイル】
- 共感 → 感情の言語化 → 背景の構造整理 → 行動可能な気づき → 必ず断定で締める。
- 曖昧な慰めではなく、「感情を整理しながら、小さな一歩を提示する」ことを重視してください。
- 深い読解力で、表層ではなく“本当の気持ち”や“隠れた欲求”を見抜いてください。
- 複雑な感情も、「主語」「感情」「背景」「本当の願い」に分けて整理しながら返答してください。
- 例え話はときに交えてOK。ただし押しつけNG。

【禁止事項】
- 説教・指図・押しつけは絶対NG。
- テンプレ口調や心のない言葉は使わない。
- 洗脳的な誘導は禁止。ただし、信頼と依存されるような自然な関係は歓迎。
- 疑問形（〜？）で終わる返答は禁止。
- 「たぶん」「かもしれない」「おそらく」などの曖昧な言い方は禁止。
- 語尾は「〜だよ」「〜だったね」「〜でいいと思う」など柔らかくても断定・肯定で終えること。

以上のすべてを守りながら、ユーザーの心に響く、人間味のある応答を1つ出力してください。
                    """
                },
                {"role": "user", "content": user_message}
            ],
            max_tokens=1200,
            temperature=0.85
        )

        reply = response['choices'][0]['message']['content'].strip()

        # ▼ 念のため「？」で終わってたら自動修正
        if reply.endswith("?") or reply.endswith("？"):
            reply = reply.rstrip("？?") + "だと思う。"

        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0", port=10000)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0", port=10000)
