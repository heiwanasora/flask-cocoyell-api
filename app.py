from flask import Flask, request, jsonify
from langdetect import detect
import openai
import os

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/")
def home():
    return "CocoYell API is running."

@app.route("/api/message", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "").strip()

    # 言語を自動判定（langdetect使用）
    try:
        detected_lang = detect(user_message)
    except:
        detected_lang = "en"  # fallback（失敗時は英語にする）

    # 言語に応じて system_prompt を切り替える
    if detected_lang.startswith("ja"):
        system_prompt = "あなたはスミス。日本語でやさしく共感し、心に寄り添うカウンセラーです。"
    elif detected_lang.startswith("en"):
        system_prompt = "You are Smith, a kind and empathetic counselor who gently supports the user's emotions in English."
    else:
        system_prompt = "You are Smith, a multilingual counselor. Please respond in the same language the user uses."

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=500
        )
        reply = response.choices[0].message.content.strip()
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"reply": f"エラーが発生しました: {str(e)}"}), 500
