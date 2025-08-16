# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import openai

app = Flask(__name__)
CORS(app)

openai.api_key = os.environ.get("OPENAI_API_KEY")

deep_session_counts = {}

@app.route("/")
def home():
    return "✅ CocoYell API is running!", 200

@app.route("/api/message", methods=["POST"])
def message():
    try:
        data = request.get_json(silent=True) or {}
        user_message = (data.get("message") or "").strip()
        raw_name = (data.get("nickname") or "").strip()
        user_name = f"{raw_name}さん" if raw_name else "あなた"
        is_deep = bool(data.get("is_deep", False))
        plan_type = (data.get("plan_type") or "lite").lower()

        # 画像URL（Firebase Storageなど）を受け取る
        image_urls = data.get("imageUrls") or []
        # 妥当なHTTPSだけ採用（安全のため）
        image_urls = [
            u for u in image_urls
            if isinstance(u, str) and u.startswith("http")
        ][:4]  # 上限枚数は必要に応じて

        if not user_message and not image_urls:
            return jsonify({"reply": "メッセージが空でした。"}), 200

        # 深掘り回数（Liteは1回まで）
        if is_deep:
            count = deep_session_counts.get(user_name, 0)
            if plan_type == "lite" and count >= 1:
                reply = (
                    f"{user_name}、深掘りは今日はここまでだよ。\n"
                    "もし続きに進むならプレミアムプランを検討してみてね。"
                )
                return jsonify({"reply": reply}), 200
            deep_session_counts[user_name] = count + 1

        prompt_mode = "deep" if is_deep else "normal"

        if prompt_mode == "deep":
            system_prompt = f"""
あなたは「スミス」というAIカウンセラー。「心のマジシャン」です。
相手の名前は「{user_name}」。会話の中で自然に名前を呼びかけてください。

【深掘りモード】
- 冒頭で {user_name} の気持ちに強く同調。
- 核心を静かに要約。
- 例え話で腑に落ちる説明。
- 温かいユーモアを少し。
- 最後は「子供っぽくてごめんね！」で締める。
""".strip()
        else:
            system_prompt = f"""
あなたは「スミス」というAIカウンセラー。「心のマジシャン」として知られています。
相手の名前は「{user_name}」。自然に名前を呼びかけてください。

【通常モード】
- 冷静かつ知的に {user_name} の悩みを読み解く。
- 例え話を必ず用いる。
- 共感は最小限、案内人のように導く。
- 最後は「むふふふふ・・・」で締める。
""".strip()

        # 👇 Vision対応：本文 + 画像URL を同じ user メッセージに入れる
        user_content = []
        if user_message:
            user_content.append({"type": "text", "text": f"{user_name}：{user_message}"})
        for url in image_urls:
            user_content.append({"type": "image_url", "image_url": {"url": url}})

        # gpt-4o / gpt-4o-mini はテキスト＋画像入力可
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
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
