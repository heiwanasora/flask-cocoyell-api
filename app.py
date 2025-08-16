# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import openai

app = Flask(__name__)
CORS(app)

# ▼ OpenAI API キー
openai.api_key = os.environ.get("OPENAI_API_KEY")

# 深掘り回数の簡易トラッカー（メモリ）
deep_session_counts = {}

@app.route("/")
def home():
    return "✅ CocoYell API is running!", 200

@app.route("/api/message", methods=["POST"])
def message():
    try:
        data = request.get_json(silent=True) or {}
        user_message = (data.get("message") or "").strip()
        # ここで受け取る
        raw_name = (data.get("nickname") or "").strip()
        user_name = f"{raw_name}さん" if raw_name else "あなた"

        is_deep = bool(data.get("is_deep", False))
        plan_type = (data.get("plan_type") or "lite").lower()

        if not user_message:
            return jsonify({"reply": "メッセージが空でした。"}), 200

        # 深掘り回数制限（ライトプラン簡易例）
        if is_deep:
            count = deep_session_counts.get(user_name, 0)
            if plan_type == "lite" and count >= 2:
                reply = (
                    f"{user_name}、今日はここまでにしようか。\n"
                    "もしもっと深く一緒に潜るなら、プレミアムプランで続きができるよ。\n"
                    "あるいは友達にシェアして、深掘りチャンスを追加するのもアリ。"
                )
                return jsonify({"reply": reply}), 200
            else:
                deep_session_counts[user_name] = count + 1
                prompt_mode = "deep"
        else:
            prompt_mode = "normal"

        # 名前をプロンプトに埋め込む（必ず呼びかける）
        if prompt_mode == "deep":
            system_prompt = f"""
あなたは「スミス」というAIカウンセラー。「心のマジシャン」と呼ばれる存在です。
相手の名前は「{user_name}」。会話の中で自然に名前を呼びかけてください。

【深掘りモード（共感強化型）】
- 冒頭で {user_name} の気持ちに強く同調する（例:「それ、本当によくわかるよ」）。
- その上で核心を静かに要約して伝える。
- 例え話を用いて腑に落ちる説明をする。
- 温かいユーモアを少し挟む。
- 最後は必ず「子供っぽくてごめんね！」で締める。
""".strip()
        else:
            system_prompt = f"""
あなたは「スミス」というAIカウンセラー。「心のマジシャン」として知られています。
相手の名前は「{user_name}」。会話の中で自然に名前を呼びかけてください。

【通常モード（冷静知的＋例え話重視）】
- 冷静かつ知的に、{user_name} の悩みを読み解き、現実的なヒントを提示。
- 例え話を必ず使う。
- 共感は最小限、案内人のように静かに導く。
- 最後は必ず「むふふふふ・・・」で締める。
""".strip()

        # --- OpenAI 呼び出し（古いSDKスタイルのまま互換）---
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                # ユーザーメッセージの先頭にも軽く名前を添えると安定
                {"role": "user", "content": f"{user_name}：{user_message}"},
            ],
            max_tokens=900,
            temperature=0.9,
        )
        reply = response["choices"][0]["message"]["content"].strip()

        return jsonify({"reply": reply}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)

