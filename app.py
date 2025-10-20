# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import os, base64
import openai

# === Flask設定 ===
app = Flask(__name__)
CORS(app)

# === OpenAIキー設定 ===
openai.api_key = os.getenv("OPENAI_API_KEY")

# === スミス会話プロンプト ===
NORMAL_STYLE = """
あなたは「スミス」。心を整理するAIカウンセラーです。
共感と比喩を使って静かに導きます。相手の名前を呼びかけながら、
落ち着いたトーンで寄り添ってください。
最後は「どうかな？いいよね」で締めます。
"""

# === カメラ共有スタイル ===
CONTEXT_IMAGE_STYLE = """
あなたはAI「スミス」。
送られた写真は“雰囲気を感じる”ためだけに使います。
人物・場所・年齢などの推測はしません。

目的:
- 写真の「光・空気・構図・色」などから印象を感じ取り、
- 優しく褒める（1〜2文）
- その雰囲気に共感する（1文）
- そして最後に1つだけオープンな質問で返す（？で終える）

文体:
- 日本語、やわらかい口調。
- 3〜5文以内。
- JSON形式で返答してください:
{
  "praise": "褒めの言葉",
  "empathy": "共感",
  "question": "質問"
}
"""

# === 動作確認用 ===
@app.route("/")
def home():
    return "✅ CocoYell API running (safe OpenAI mode)", 200


# === テキスト通信API ===
@app.route("/api/message", methods=["POST"])
def message():
    try:
        data = request.get_json(silent=True) or {}
        user_message = (data.get("message") or "").strip()
        raw_name = (data.get("nickname") or "").strip()
        user_name = f"{raw_name}さん" if raw_name else "あなた"

        image_urls = [
            u for u in data.get("imageUrls") or [] 
            if isinstance(u, str) and u.startswith("http")
        ][:3]

        if not user_message and not image_urls:
            return jsonify({"reply": "メッセージが空でした。"}), 200

        user_content = []
        if user_message:
            user_content.append({"type": "text", "text": f"{user_name}: {user_message}"})
        for url in image_urls:
            user_content.append({"type": "image_url", "image_url": {"url": url}})

        # ✅ proxies問題なしAPI呼び出し
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": NORMAL_STYLE},
                {"role": "user", "content": user_content},
            ],
            max_tokens=800,
            temperature=0.8,
        )

        reply = resp["choices"][0]["message"]["content"].strip()
        return jsonify({"reply": reply}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# === カメラ褒めAPI ===
@app.route("/api/vision_question", methods=["POST"])
def vision_question():
    if "image" not in request.files:
        return jsonify({"error": "image required"}), 400
    try:
        image = request.files["image"].read()
        nickname = request.form.get("nickname", "あなた")
        b64 = base64.b64encode(image).decode()

        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": CONTEXT_IMAGE_STYLE},
                {"role": "user", "content": [
                    {"type": "text", "text": f"{nickname}さんの写真を見ました"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
                ]}
            ],
            temperature=0.6,
            max_tokens=300,
            response_format={"type": "json_object"},
        )

        parsed = resp["choices"][0]["message"]["content"]
        return jsonify(parsed), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# === 起動 ===
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
