# app.py
import os
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)

# /api/* だけCORS許可（プリフライト含む）
CORS(app,
     resources={r"/api/*": {"origins": "*"}},
     supports_credentials=False)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

LINE_CONTEXT_STYLE = """
あなたは「スミス」。日本語だけで話す、親しい友達のような相談相手。
【目的】LINEやチャットのやり取りを読み、温度感・距離感を感じ取り、
友達に話すように「脈あり / 様子見 / 脈なし」の印象を自然文で伝える。
【出力】JSON/箇条書き/英語/コードブロックは出さない。日本語の文章のみ。
1行目：判定ひとこと。続けて理由。必要なら様子見ポイント。最後に返し例を > で1〜2個。
"""

def _line_context_reply(nickname: str, thread: list[dict]) -> str:
    convo = "\n".join([f'{m.get("sender","me")}: {(m.get("text") or "").strip()}'
                       for m in thread])
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.9,
        messages=[
            {"role": "system", "content": LINE_CONTEXT_STYLE},
            {"role": "user", "content": f"{nickname}との会話ログ:\n{convo}\n\n上のルールで返答してください。"}
        ],
        max_tokens=700
    )
    text = (res.choices[0].message.content or "").strip()
    if text.startswith("{") or text.startswith("["):
        text = "様子見。\n形式的になっていたから、自然文で出直すね。\n> 来週の平日夜か週末ランチならどっちが合いそう？"
    return text

# --- LINE文脈 本命エンドポイント ---
@app.route("/api/line_context", methods=["POST", "OPTIONS"])
def line_context():
    if request.method == "OPTIONS":
        return make_response(("", 204))
    data = request.get_json(silent=True) or {}
    nickname = (data.get("nickname") or "あなた").strip()
    thread = data.get("thread") or []
    try:
        text = _line_context_reply(nickname, thread)
        return jsonify({"reply": text}), 200
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

    # history を thread に変換し、直近入力も足す
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
        out = _line_context_reply(nickname, thread)
        return jsonify({"reply": out}), 200
    except Exception as e:
        return jsonify({"reply": f"（エラー）スミスが一瞬考えすぎました：{e}"}), 200

@app.get("/healthz")
def healthz():
    return "ok", 200

@app.get("/")
def root():
    return "✅ Smith LINE Analyzer (only) — /api/line_context, /api/message(compat)", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
