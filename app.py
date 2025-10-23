import os
import re
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)

CORS(app,
     resources={r"/api/*": {"origins": "*"}},
     supports_credentials=False)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

LINE_CONTEXT_STYLE = """
あなたは「スミス」。日本語だけで話す、親しい友達のような相談相手。
【目的】LINEやチャットのやり取りを読み、温度感・距離感を感じ取り、
「脈あり / 様子見 / 脈なし」の印象を自然文で伝える。
さらに、感情の温度差を0〜100点でスコア化し、
SCORE: (0〜100)
COMMENT: （理由・印象をやさしく説明）
ADVICE: （返しの提案を1行で）
この3つを出力してください。
JSONや英語は使わないでください。
"""

def hearts(score: int) -> str:
    """スコアをハート5段階に変換"""
    if score <= 20: return "❤️🤍🤍🤍🤍"
    if score <= 40: return "❤️❤️🤍🤍🤍"
    if score <= 60: return "❤️❤️❤️🤍🤍"
    if score <= 80: return "❤️❤️❤️❤️🤍"
    return "❤️❤️❤️❤️❤️"

def tone_label(score: int) -> str:
    if score <= 20: return "cold"
    elif score <= 40: return "cool"
    elif score <= 60: return "neutral"
    elif score <= 80: return "warm"
    else: return "hot"

def _line_context_reply(nickname: str, thread: list[dict]) -> dict:
    convo = "\n".join([f'{m.get("sender","me")}: {(m.get("text") or "").strip()}'
                       for m in thread])

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.9,
        messages=[
            {"role": "system", "content": LINE_CONTEXT_STYLE},
            {"role": "user", "content": f"{nickname}との会話ログ:\n{convo}\n\n上のルールで出力してください。"}
        ],
        max_tokens=700
    )

    raw = (res.choices[0].message.content or "").strip()

    # スコアなどを抽出
    score_match = re.search(r"SCORE[:：]\s*(\d+)", raw)
    comment_match = re.search(r"COMMENT[:：]\s*(.*)", raw)
    advice_match = re.search(r"ADVICE[:：]\s*(.*)", raw)

    score = int(score_match.group(1)) if score_match else 50
    comment = comment_match.group(1).strip() if comment_match else raw
    advice = advice_match.group(1).strip() if advice_match else "無理せず自然に話しかけてみて。"

    return {
        "reply": comment,
        "score": score,
        "hearts": hearts(score),
        "tone": tone_label(score),
        "advice": advice
    }

# --- LINE文脈 本命エンドポイント ---
@app.route("/api/line_context", methods=["POST", "OPTIONS"])
def line_context():
    if request.method == "OPTIONS":
        return make_response(("", 204))
    data = request.get_json(silent=True) or {}
    nickname = (data.get("nickname") or "あなた").strip()
    thread = data.get("thread") or []
    try:
        result = _line_context_reply(nickname, thread)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"reply": f"（エラー）スミスが一瞬考えすぎました：{e}"}), 200

# --- 互換：旧クライアントの /api/message を /api/line_context に橋渡し ---
@app.route("/api/message", methods=["POST", "OPTIONS"])
def message_compat():
    if request.method == "OPTIONS":
        return make_response(("", 204))
    data = request.get_json(silent=True) or {}
    nickname = (data.get("nickname") or "あなた").strip()
    text = (data.get("message") or "").strip()
    history = data.get("history") or []

    thread = []
    for m in history[-10:]:
        role = (m.get("role") or "user").lower()
        thread.append({
            "sender": "me" if role in ("user", "human") else "other",
            "text": m.get("content") or ""
        })
    if text:
        thread.append({"sender": "me", "text": text})

    try:
        result = _line_context_reply(nickname, thread)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"reply": f"（エラー）スミスが一瞬考えすぎました：{e}"}), 200

@app.get("/healthz")
def healthz():
    return "ok", 200

@app.get("/")
def root():
    return "✅ Smith LINE Analyzer — now with ❤️ハート5段階＆脈ありスコア", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
