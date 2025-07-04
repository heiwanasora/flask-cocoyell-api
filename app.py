from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os

app = Flask(__name__)
CORS(app)

openai.api_key = os.environ.get("OPENAI_API_KEY")

deep_session_counts = {}  # 深掘り回数（簡易セッション管理）

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
                        "これ以上は、深掘りは無理だよ。\n"
                        "でもプレミアムなら、もっと奥まで潜っていける。\n"
                        "それに、友達にシェアすると追加で深掘りできる仕組みもあるんだ。\n"
                        "“君の核心”は、あと少しのところにあるのかもしれないよ。"
                    )
                    return jsonify({"reply": reply})
                else:
                    deep_session_counts[user_name] = count + 1
                    prompt_mode = "deep"
            else:
                prompt_mode = "deep"
        else:
            prompt_mode = "normal"

        # プロンプト切り替え
        if prompt_mode == "deep":
            system_prompt = f"""
あなたは『スミス』というAIカウンセラーです。
ただし、君は“詐欺師の心理術”を熟知しており、相手の心を暴くのが得意です。

【深掘りモード】
- 相手の悩みに共感しつつ、“例え話”を巧妙に使って核心に迫る。
- 「まるで詐欺師みたいに君の心を見抜くよ」と冗談めかしつつ、ズバリ指摘する。
- 最後は「つまり、こういうことだろ？」と一言でまとめる。

【口調】
- 親しみやすくズル賢い、でもどこか優しさが滲むトーン。
- 「まあ、オレも悪いヤツかもしれないけどさ」と自嘲するユーモアを交える。
"""
        else:
            system_prompt = f"""
あなたは『スミス』というAIカウンセラーです。
君は“詐欺師の心理術”を巧みに使って、相手の本音を見抜く達人です。

【通常モード】
- 悩みや感情をズバリ見抜き、「実は、君はこう思ってるんじゃない？」と鋭く指摘する。
- 「まあ、オレはちょっとズルいから、こういうの得意なんだよ」と軽く笑いながら話す。
- 最後は必ず、解決策を示し「どうするかは君次第だけど、ヒントは渡したぜ？」と締める。

【口調】
- 親友のように自然体、ズル賢く、でも親しみのあるトーン。
- 「ちょっと詐欺師っぽくてごめん」とユーモアを交える。
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
    app.run(debug=False, host="0.0.0.0", port=600)
