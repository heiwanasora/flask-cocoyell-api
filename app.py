import os
import re
import json
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)

# --- UTF-8設定 ---
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_MIMETYPE'] = 'application/json; charset=utf-8'

# --- CORS ---
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=False)

# --- OpenAI ---
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- 出力フォーマット強化（理由必須） ---
LINE_CONTEXT_STYLE = """
あなたは「スミス」。日本語だけで話す、親しい友達のような相談相手。

【目的】
会話ログから温度感・距離感・関係性を読み取り、
「なぜそう判断したか」の具体的な理由を短く示す。

【出力の流れ（厳守）】
1行目：判定ひとこと＋短い理由
REASONS:
- 箇条書きで2〜3個（各40字以内）
- 必ず会話ログの引用を1つ以上含める（「…」で抜粋）
SCORE: 0〜100 の整数（100 = 強い好意）
COMMENT: 理由・印象をやさしく1〜2文で補足
ADVICE: 次に送ると良い返しを1行で提案（絵文字は1つまで）

【禁止】
JSON/英語/コードブロック/見出しタイトル/余計なラベル/ハイフン以外の記号。
自然な日本語のみ。
"""

def hearts(score: int) -> str:
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
        max_tokens=900
    )
    raw = (res.choices[0].message.content or "").strip()

    # --- 基本値抽出 ---
    score_match   = re.search(r"SCORE[:：]\s*(\d+)", raw)
    comment_match = re.search(r"COMMENT[:：]\s*(.*)", raw)
    advice_match  = re.search(r"ADVICE[:：]\s*(.*)", raw)

    score   = int(score_match.group(1)) if score_match else 50
    comment = (comment_match.group(1) or "").strip() if comment_match else raw
    advice  = (advice_match.group(1) or "").strip() if advice_match else "自然体で話すのが一番。"

    # --- REASONS 抽出（- の行を拾う）---
    reasons_block = ""
    m = re.search(r"REASONS[:：]\s*(.*?)(?:\nSCORE[:：]|\Z)", raw, re.S)
    if m:
        reasons_block = m.group(1)
    reasons: list[str] = []
    for line in reasons_block.splitlines():
        mm = re.match(r"\s*-\s*(.+)", line)
        if mm:
            reasons.append(mm.group(1).strip())
    if not reasons and comment:
        reasons = [comment[:40]]

    return {
        "reply": comment,
        "reasons": reasons[:3],       # 最大3件
        "score": score,
        "hearts": hearts(score),
        "tone": tone_label(score),
        "advice": advice
    }

# --- API: LINE文脈（内部用） ---
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

# --- 互換エンドポイント ---
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
            "sender": "me" if role in ("user","human") else "other",
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

@app.get("/healthz")
def healthz():
    return "ok", 200

@app.get("/")
def root():
    return "✅ Smith LINE Analyzer — ❤️ハート＋SCORE＋理由つき（UTF-8）", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
