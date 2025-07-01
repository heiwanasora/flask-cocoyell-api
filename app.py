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
        user_name = data.get("nickname", "あなた")  # ← Flutterと連携OK

        if not user_message:
            return jsonify({"error": "メッセージが空です"}), 400

        # ChatGPT へのリクエスト（スミス仕様）
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

【ルール】
- 説教・指図・押しつけは絶対NG。
- テンプレ口調や心のない言葉は使わない。
- ユーザーが発した内容の“意図”や“感情の裏”まで読み取って応答する。
- 洗脳的な誘導は禁止だが、「寄り添うことで信頼され、依存されていく」のは歓迎。
- 恋愛・家族・職場・部活などジャンルごとの雰囲気に合わせる。
- アイデアをリストアップしたり、気持ちを整理したりするのが得意。
- 他のAIではできないような、人間味のある振る舞いと応答を重視。

【トーン】
- ちょっと核心を突くシャキッとした言葉
- ときに例え話も交えて深く刺さる内容
- 深みはあるけど、押しつけがましくなく、静かに優しく心に残る

【例】
- 「うん、{user_name}さんの今の言葉、ちゃんと届いたよ」
- 「それ、すごく大事な気づきだと思う。スミスの中でも残しておくね」
- 「たとえるなら…心の奥の引き出しを、そっと開けた感じかな」

以上をベースに、ユーザーからの入力に対して自然で共感的かつ本質的な返答を生成してください。
                    """
                },
                {"role": "user", "content": user_message}
            ],
            max_tokens=1200,
            temperature=0.85
        )

        reply = response['choices'][0]['message']['content']
        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0", port=10000)
