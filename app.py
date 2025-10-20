from flask import Flask, request, jsonify
from flask_cors import CORS
import os, base64
from openai import OpenAI

app = Flask(__name__)
CORS(app)

# ✅ 新SDKの書き方
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/")
def home():
    return "✅ CocoYell API running (new OpenAI SDK)", 200

# === テキストメッセージ ===
@app.route("/api/message", methods=["POST"])
def message():
    try:
        data = request.get_json(silent=True) or {}
        message = (data.get("message") or "").strip()
        nickname = (data.get("nickname") or "あなた").strip()

        if not message:
            return jsonify({"reply": "メッセージが空です。"}), 200

        system_prompt = f"""
あなたはAI「スミス」。穏やかで知的なカウンセラーです。
名前は{nickname}さん。感情を読み取りながら、比喩と優しさを交えて返します。
最後は「どうかな？いいよね」で締めてください。
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
            max_tokens=800,
            temperature=0.8,
        )

        reply = response.choices[0].message.content.strip()
        return jsonify({"reply": reply}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# === カメラ認識API ===
@app.route("/api/vision_question", methods=["POST"])
def vision_question():
    if "image" not in request.files:
        return jsonify({"error": "imageファイルが必要です"}), 400
    try:
        image = request.files["image"].read()
        nickname = request.form.get("nickname", "あなた")
        b64 = base64.b64encode(image).decode()

        system_prompt = f"""
あなたはAI「スミス」。
送られた写真を“感じ取る”だけに使い、人物・場所・年齢などは推測しません。
雰囲気を褒めて、優しく共感し、最後に質問で返します。
出力形式はJSONで:
{{
  "praise": "褒め",
  "empathy": "共感",
  "question": "質問"
}}
"""

        result = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"{nickname}さんの写真です。"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
                    ],
                },
            ],
            temperature=0.7,
            max_tokens=400,
            response_format={"type": "json_object"},
        )

        return jsonify(result.choices[0].message.content), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
