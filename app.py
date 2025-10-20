# app.py
# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import base64

# OpenAI v1 系 SDK
# requirements は下記の固定推奨:
# openai==1.52.0, httpx==0.27.2, httpcore==1.0.5
from openai import OpenAI

app = Flask(__name__)
CORS(app)

# ========= スタイル（プロンプト） =========

# テキスト会話スタイル：最後の「どうかな？いいよね」は使わない
CONTEXT_TEXT_STYLE = """
あなたは「スミス」。心を整理するAIカウンセラーです。
共感と比喩を使って静かに導きます。相手の名前を呼びかけながら、
落ち着いたトーンで寄り添ってください。
最後は、心が少し軽くなる一言で自然に締めてください。
"""

# カメラ共有スタイル：写真は“雰囲気を感じる”ためだけに使う
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

# LINE文脈解析スタイル：脈あり/なしの兆候、返信案まで
CONTEXT_LINE_STYLE = """
あなたはAI「スミス」。日本語LINEの会話から“行間”を読み取るアナリストです。
感情・温度感・関係性の距離・脈あり/なしの兆候を、短い根拠とともに数値化し、
相手に負担をかけない一言返信案まで提案します。

重要:
- 絵文字/スタンプ/句読点/改行/既読スルー/返信までの時間（与えられた場合）も手がかりにする
- 断定はしない。可能性ベースで丁寧に説明する
- 個人の特性や属性の推測はしない

出力は日本語のJSON（1オブジェクト）:
{
  "summary_short": "会話の一行要約",
  "tone_me": "あなた側のトーン",
  "tone_other": "相手のトーン",
  "interest_score": 0-100,
  "signals_positive": ["根拠1", "根拠2"],
  "signals_negative": ["根拠1", "根拠2"],
  "red_flags": ["注意点..."],
  "confidence": 0.0-1.0,
  "suggested_reply": "自然で短い返信案（1〜2文）",
  "next_move_question": "関係を一歩進める無理のない質問（1つ）"
}
"""

# ========= OpenAI クライアント =========
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ========= ヘルパ =========

def nickname_or_default(raw: str) -> str:
    raw = (raw or "").strip()
    return f"{raw}さん" if raw else "あなた"

def build_image_part_from_upload(file_storage):
    """
    画像アップロード（multipart/form-data）のファイルから
    メッセージ用の input_image パートを作る（data URL base64）。
    """
    if not file_storage:
        return None
    data = file_storage.read()
    if not data:
        return None
    b64 = base64.b64encode(data).decode("utf-8")
    # 拡張子からMIME簡易推定（なければ jpeg）
    mime = "image/jpeg"
    filename = (file_storage.filename or "").lower()
    if filename.endswith(".png"):
        mime = "image/png"
    elif filename.endswith(".webp"):
        mime = "image/webp"
    return {
        "type": "input_image",
        "image_url": f"data:{mime};base64,{b64}",
    }

def build_image_part_from_url(url: str):
    if not url or not isinstance(url, str):
        return None
    if not url.startswith("http"):
        return None
    return {
        "type": "input_image",
        "image_url": url,
    }

# ========= ルート =========

@app.route("/", methods=["GET"])
def home():
    return "✅ CocoYell API running (OpenAI v1 SDK)", 200

# --- テキスト会話：/api/message ---
@app.route("/api/message", methods=["POST"])
def api_message():
    try:
        data = request.get_json(silent=True) or {}
        user_message = (data.get("message") or "").strip()
        user_name = nickname_or_default(data.get("nickname"))

        if not user_message:
            return jsonify({"error": "message が空です"}), 400

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": CONTEXT_TEXT_STYLE},
                {"role": "user", "content": f"{user_name}：{user_message}"},
            ],
            temperature=0.8,
            max_tokens=900,
        )
        reply = resp.choices[0].message.content.strip()
        return jsonify({"reply": reply}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- カメラ（写真の称賛→共感→質問 JSON）：/api/vision_question ---
# 使い方:
# 1) 画像アップロード:
#    curl -s -X POST <BASE>/api/vision_question -F "image=@test.jpg" -F "nickname=淳史"
# 2) URL指定:
#    curl -s -X POST <BASE>/api/vision_question -H "Content-Type: application/json" \
#      -d '{"imageUrls":["https://.../photo.jpg"], "nickname":"淳史"}'
@app.route("/api/vision_question", methods=["POST"])
def api_vision_question():
    try:
        user_name = nickname_or_default(request.form.get("nickname") or (request.json or {}).get("nickname"))

        # 1) multipart upload
        img_part = None
        if "image" in request.files:
            img_part = build_image_part_from_upload(request.files["image"])

        # 2) JSON imageUrls
        if img_part is None:
            body = request.get_json(silent=True) or {}
            urls = body.get("imageUrls") or []
            if isinstance(urls, list) and urls:
                img_part = build_image_part_from_url(urls[0])

        if img_part is None:
            return jsonify({"error": "画像が見つかりません（multipart の image か imageUrls を送ってください）"}), 400

        messages = [
            {"role": "system", "content": CONTEXT_IMAGE_STYLE},
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": f"{user_name}が共有した写真です。雰囲気だけを見てください。"},
                    img_part,
                ],
            },
        ]

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=400,
        )

        content = resp.choices[0].message.content
        # content は JSON文字列のはず。Flask 側で JSON として返す。
        return jsonify(content if isinstance(content, dict) else {"result": content}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- LINE文脈解析：/api/line_context ---
# 入力例:
# {
#   "nickname": "淳史",
#   "thread": [
#     {"sender":"me","text":"この前ありがと！またご飯いこう？","ts":"2025-10-20T21:03:00+09:00"},
#     {"sender":"other","text":"うん！楽しかった😊 予定みて連絡するね〜","ts":"2025-10-20T21:05:12+09:00"}
#   ]
# }
@app.route("/api/line_context", methods=["POST"])
def api_line_context():
    try:
        data = request.get_json(silent=True) or {}
        nickname = (data.get("nickname") or "あなた").strip()
        thread = data.get("thread") or []

        if not isinstance(thread, list) or not thread:
            return jsonify({"error": "thread が空です。メッセージ配列を送ってください。"}), 400

        # 会話を読みやすく整形
        lines = []
        for turn in thread:
            s = (turn.get("sender") or "").lower()
            t = (turn.get("text") or "").strip()
            ts = turn.get("ts")
            if not t:
                continue
            who = "あなた" if s == "me" else "相手"
            if ts:
                lines.append(f"[{who} {ts}] {t}")
            else:
                lines.append(f"[{who}] {t}")
        transcript = "\n".join(lines)

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": CONTEXT_LINE_STYLE},
                {
                    "role": "user",
                    "content": f"相手の名前は不明。あなた（{nickname}）視点で分析してください。\n--- 会話ログ ---\n{transcript}"
                },
            ],
            response_format={"type": "json_object"},
            temperature=0.4,
            max_tokens=700,
        )

        content = resp.choices[0].message.content
        return jsonify(content if isinstance(content, dict) else {"result": content}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ========= エントリーポイント =========
if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
