import os
import re
import json
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)

# --- UTF-8設定（日本語と絵文字を正しく返す） ---
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_MIMETYPE'] = 'application/json; charset=utf-8'

# --- CORS設定（Flutterなど外部アクセス許可） ---
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=False)

# --- OpenAI初期化 ---
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- スミス人格設定 ---
LINE_CONTEXT_STYLE = """
あなたは「スミス」。日本語だけで話す、親しい友達のような相談相手。

【目的】
LINEやチャットのやり取りを読み、温度感・距離感・関係性を感じ取り、
「脈あり / 様子見 / 脈なし」の印象を自然文で伝える。

【出力の流れ】
1行目：判定ひとこと＋短い理由（自然文）。必要なら様子見ポイントを一言。
その後、下の3行を**必ずこの順で**、半角の見出し＋半角コロンで出力すること。
- SCORE: 0〜100 の整数（100 = 強い好意、0 = 脈なし）
- COMMENT: 理由・印象をやさしく1〜2文で説明
- ADVICE: 次に送ると良い返しを1行で提案（絵文字は1つまで）

【禁止】
JSON/英語/コードブロック/見出しタイトル/余計なラベル/箇条書きのハイフン。
自然な日本語のみ。
"""

# --- ハート5段階変換 ---
def hearts(score: int) -> str:
    if score <= 20: return "❤️🤍🤍🤍🤍"
    if score <= 40: return "❤️❤️🤍🤍🤍"
    if score <= 60: return "❤️❤️❤️🤍🤍"
    if score <= 80: return "❤️❤️❤️❤️🤍"
    return "❤️❤️❤️❤️❤️"

# --- 温度ラベル変換 ---
def tone_label(score: int) -> str:
    if score <= 20: return "cold"
    elif score <= 40: return "cool"
    elif score <= 60: return "neutral"
    elif score <= 80: return "warm"
    else: return "hot"

# --- スミス応答処理 ---
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

    # --- スコア抽出 ---
    score_match = re.search(r"SCORE[:：]\s*(\d+)", raw)
    comment_match = re.search(r"COMMENT[:：]\s*(.*)", raw)
    advice_match = re.search(r"ADVICE[:：]\s*(.*)", raw)

    score = int(score_match.group(1)) if score_match else 50
    comment = comment_match.group(1).strip() if comment_match else raw
    advice = advice_match.group(1).strip() if advice_match else "自然体で話すのが一番。"

    return {
        "reply": comment,
        "score": score,
        "hearts": hearts(score),
        "tone": tone_label(score),
        "advice": advice
    }

# --- メインAPI ---
@app.route("/api/line_context", methods=["POST", "OPTIONS"])
def line_context():
    if request.method == "OPTIONS":
        return make_response(("", 204))
    data = request.get_json(silent=True) or {}
    nickname = (data.get("nickname") or "あなた").strip()
    thread = data.get("thread") or []
    try:
        result = _line_context_reply(nickname, thread)
        return make_response(
            json.dumps(result, ensure_ascii=False),
            200,
            {'Content-Type': 'application/json; charset=utf-8'}
        )
    except Exception as e:
        return jsonify({"reply": f"（エラー）スミスが一瞬考えすぎました：{e}"}), 200

# --- /api/message 互換 ---
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
        return make_response(
            json.dumps(result, ensure_ascii=False),
            200,
            {'Content-Type': 'application/json; charset=utf-8'}
        )
    except Exception as e:
        return jsonify({"reply": f"（エラー）スミスが一瞬考えすぎました：{e}"}), 200

# --- ヘルスチェック ---
@app.get("/healthz")
def healthz():
    return "ok", 200

# --- ルート ---
@app.get("/")
def root():
    return "✅ Smith LINE Analyzer — ❤️ハート5段階＋スコア＋UTF-8対応", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=False)
