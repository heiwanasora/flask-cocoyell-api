# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import os, base64
from openai import OpenAI

# ===== 初期設定 =====
app = Flask(__name__)
CORS(app)

# OpenAIクライアント初期化（新SDK）
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ===== スタイル定義 =====

# 通常モード
NORMAL_STYLE = """
あなたは「スミス」。心を整理するAIカウンセラーです。
共感と比喩を使って静かに導きます。相手の名前を呼びかけながら、
落ち着いたトーンで寄り添ってください。
最後は「どうかな？いいよね」で締めます。
"""

# 感情推定モード
FEEL_GUESS_STYLE = r"""
あなたはAI「スミス」。相手の文章から感じられる感情を“仮説”として当てにいきます。
構成:
1) 観察: 文面の特徴。
2) 仮説: 感情トップ3（例: 不安45%, 悲しみ35%, 焦り20%）。
3) 確認: 1つの確認質問。
4) 一歩: 軽い行動提案（60秒以内でできること）。
断定禁止・医療語禁止・優しい文体。
"""

# 恋愛文脈モード
LOVE_SIGNAL_STYLE = r"""
あなたは「スミス」。メッセージ文面から恋愛的な関心（脈あり／なし）を分析します。
構成:
1) 言葉の特徴
2) 心理推定（3つまで）
3) 脈分析: 脈あり度(0〜100%)と総評
4) 補足とアドバイス
禁止: 性的表現・断定・占い語。文体は穏やかで優しく。
"""

# カメラ共有モード（褒め＋共感＋質問）
CONTEXT_IMAGE_STYLE = """
あなたはAI「スミス」。
送られた写真は“雰囲気を感じる”ためだけに使います。
人物・場所・年齢などの推測はしません。

目的:
- 写真の中の「光・空気・構図・色」などを感じ取り、
- 優しく褒める（美的・感情的な観点で1〜2文）
- その雰囲気に共感する（1文）
- そして1つだけオープンな質問で返す（？で終える）

文体:
- 日本語、やわらかい口調。
- 3〜5文以内。
- JSON形式で必ず返す:

{
  "praise": "褒めの言葉（例：とても穏やかで美しい景色ですね）",
  "empathy": "共感や感じたこと（例：見ているだけで心が落ち着きますね）",
  "question": "1文の問い（例：この場所、どんな気持ちで撮りましたか？）"
}
"""

# ===== ルート確認 =====
@app.route("/")
def home():
    return "✅ CocoYell API running", 200


# ===== テキストメッセージAPI =====
@app.route("/api/message", methods=["POST"])
def message():
    try:
        data = request.get_json(silent=True) or {}
        user_message = (data.get("message") or "").strip()
        raw_name = (data.get("nickname") or "").strip()
        user_name = f"{raw_name}さん" if raw_name else "あなた"
        style = (data.get("style") or "").lower()
        image_urls = [
            u for u in data.get("imageUrls") or [] 
            if isinstance(u, str) and u.startswith("http")
        ][:3]

        if not user_message and not image_urls:
            return jsonify({"reply": "メッセージが空でした。"}), 200

        # スタイル選択
        if style == "feel_guess":
            system_prompt = FEEL_GUESS_STYLE
        elif style == "love_signal":
            system_prompt = LOVE_SIGNAL_STYLE
        else:
            system_prompt = NORMAL_STYLE

        # メッセージ構築
        user_content = []
        if user_message:
            user_content.append({"type": "text", "text": f"{user_name}: {user_message}"})
        for url in image_urls:
            user_content.append({"type": "image_url", "image_url": {"url": url}})

        # OpenAI呼び出し（新SDK）
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            max_tokens=800,
            temperature=0.8,
        )

        reply = resp.choices[0].message.content.strip()
        return jsonify({"reply": reply}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ===== カメラ共有API（褒め＋共感＋質問） =====
@app.route("/api/vision_question", methods=["POST"])
def vision_question():
    if "image" not in request.files:
        return jsonify({"error": "image required"}), 400

    try:
        image = request.files["image"].read()
        nickname = request.form.get("nickname", "あなた")
        b64 = base64.b64encode(image).decode()

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": CONTEXT_IMAGE_STYLE},
                {"role": "user", "content": [
                    {"type": "text", "text": f"{nickname}さんに返答してください"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
                ]}
            ],
            temperature=0.6,
            max_tokens=300,
            response_format={"type": "json_object"}
        )

        return jsonify(resp.choices[0].message.parsed), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ===== 起動 =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
