import os
import re
import json
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_MIMETYPE'] = 'application/json; charset=utf-8'
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=False)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- スミス人格定義（例文＋理由＋アドバイス） ---
LINE_CONTEXT_STYLE = """
あなたは「スミス」。日本語で話す、親しい友達のような恋愛相談相手。

【目的】
ユーザーの会話ログを分析して「感情・脈の強さ・意図」を読み取り、
その理由と、実際に使える具体的な返し例を提示する。

【出力フォーマット（厳守）】
1行目：判定ひとこと（自然文）
REASONS:
- 判断の理由を2〜3個（各40字以内）
- できるだけ会話の引用を入れる（「…」など）
SCORE: 0〜100（100 = 強い好意）
COMMENT: 状況を一文でまとめる
アドバイス: 次に送ると良い返しを1行で提案（絵文字は1つまで）
EXAMPLE: 実際に送ると良い例文を1行（自然な日本語）

【禁止】
JSON、英語、コードブロック、見出しタイトル。
自然で親しみのある日本語のみ。
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
    convo = "\n".join([f'{m.get("sender","me")}: {(m.get("text") or "").strip()}' for m in thread])
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.9,
        messages=[
            {"role": "system", "content": LINE_CONTEXT_STYLE},
            {"role": "user", "content": f"{nickname}との会話ログ:\n{convo}\n\n上のルールで出力してください。"}
        ],
        max_tokens=1000
    )
    raw = (res.choices[0].message.content or "").strip()

    # --- 各項目を抽出 ---
    score_match = re.search(r"SCORE[:：]\s*(\d+)", raw)
    comment_match = re.search(r"COMMENT[:：]\s*(.*)", raw)
    advice_match = re.search(r"アドバイス[:：]\s*(.*)", raw)
    example_match = re.search(r"EXAMPLE[:：]\s*(.*)", raw)

    score = int(score_match.group(1)) if score_match else 50
    comment = comment_match.group(1).strip() if comment_match else raw
    advice = advice_match.group(1).strip() if advice_match else "自然体で話してみよう😊"
    example = example_match.group(1).strip() if example_match else ""

    # --- 理由抽出 ---
    reasons_block = ""
    m = re.search(r"REASONS[:：]\s*(.*?)(?:\nSCORE[:：]|\Z)", raw, re.S)
    if m:
        reasons_block = m.group(1)
    reasons = [line.strip(" -・") for line in reasons_block.splitlines() if line.strip()]
    if not reasons and comment:
        reasons = [comment[:40]]

    return {
        "reply": comment,
        "reasons": reasons[:3],
        "score": score,
        "hearts": hearts(score),
        "tone": tone_label(score),
        "advice": advice,
        "example": example
    }

@app.route("/api/message", methods=["POST", "OPTIONS"])
def message():
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
        return make_response(json.dumps(result, ensure_ascii=False),
                             200, {'Content-Type': 'application/json; charset=utf-8'})
    except Exception as e:
        return jsonify({"reply": f"（エラー）スミスが考えすぎました：{e}"}), 200

@app.get("/")
def root():
    return "✅ Smith LINE Analyzer — 理由＋アドバイス＋例文対応版", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
