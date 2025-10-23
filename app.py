# app.py
import os
import re
import json
from typing import Any, Dict, List, Optional
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from openai import OpenAI

# ---------- Flask 基本設定 ----------
app = Flask(__name__)
CORS(app)
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_MIMETYPE'] = 'application/json; charset=utf-8'

# ---------- OpenAI ----------
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---------- 環境変数 ----------
DEFAULT_CONTEXT = os.getenv("SMITH_CONTEXT", "恋愛")
POS_TH = int(os.getenv("SMITH_POSITIVE_THRESHOLD", "70"))
NEU_TH = int(os.getenv("SMITH_NEUTRAL_THRESHOLD", "40"))
STATUS_OVERRIDE = os.getenv("SMITH_STATUS_OVERRIDE", "0") == "1"

# ---------- ユーティリティ ----------
def normalize_context(ctx: Optional[str]) -> str:
    if not ctx:
        return DEFAULT_CONTEXT
    ctx = str(ctx).strip()
    alias = {
        "恋愛": {"恋愛", "love", "renai"},
        "友人": {"友人", "友情", "friend"},
        "仕事": {"仕事", "ビジネス", "work"},
    }
    for k, vals in alias.items():
        if ctx in vals:
            return k
    return ctx

def hearts(score: int) -> str:
    score = max(0, min(100, int(score)))
    filled = min(5, (score + 19) // 20)
    return "❤️" * filled + "🤍" * (5 - filled)

def tone_label(score: int) -> str:
    s = max(0, min(100, int(score)))
    if s <= 20: return "cold"
    if s <= 40: return "cool"
    if s <= 60: return "neutral"
    if s <= 80: return "warm"
    return "hot"

def status_from_score(score: int) -> str:
    if score >= POS_TH:
        return "脈あり"
    if score >= NEU_TH:
        return "様子見"
    return "脈なし"

# ---------- スミス共通プロンプト ----------
def build_system_prompt(context_name: str) -> str:
    return f"""
あなたは「スミス」。日本語で話す感情カウンセラー。
対象ジャンル: {context_name}

ユーザーの会話文から相手の心理・感情を読み取り、
理由・スコア・アドバイス・例文までを出す。

出力は **厳密なJSON** のみ。英語禁止。スキーマ：
{{
  "status": "脈あり" | "様子見" | "脈なし",
  "intent": "相手の意図を一言で要約",
  "analysis": "感情の流れを2〜3文で説明",
  "reasons": ["根拠1", "根拠2", "根拠3"],
  "score": 0〜100,
  "advice": "次の行動への一言アドバイス",
  "example": "自然で優しい返事の例文"
}}
    """.strip()

# ---------- モデル呼び出し ----------
def call_model(user_text: str, context_name: str) -> Dict[str, Any]:
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.6,
        messages=[
            {"role": "system", "content": build_system_prompt(context_name)},
            {"role": "user", "content": user_text},
        ],
    )

    content = resp.choices[0].message.content or ""
    content = content.strip().replace("```json", "").replace("```", "")
    try:
        data = json.loads(content)
    except:
        data = {
            "status": "様子見",
            "intent": "解析エラー",
            "analysis": "形式を整形できませんでしたが、中庸な印象です。",
            "reasons": ["JSONエラーのため暫定判断。"],
            "score": 50,
            "advice": "無理せず自然にやり取りを続けましょう。",
            "example": "また話せたら嬉しいな。"
        }

    score = int(data.get("score", 50))
    model_status = data.get("status", "")
    score_status = status_from_score(score)
    final_status = score_status if (STATUS_OVERRIDE or not model_status) else model_status

    return {
        "status": final_status,
        "intent": data.get("intent", ""),
        "analysis": data.get("analysis", ""),
        "reasons": data.get("reasons", [])[:3],
        "score": score,
        "advice": data.get("advice", ""),
        "example": data.get("example", "")
    }

# ---------- 返答整形 ----------
def build_reply_text(out: Dict[str, Any], context_name: str) -> str:
    lines = [
        f"心理の要約: {out['intent']}",
        "理由:",
        *[f"・{r}" for r in out['reasons']],
        "",
        f"スミスの解析: {out['analysis']}",
        f"ステータス: {out['status']}（文脈: {context_name}）",
        f"{hearts(out['score'])}   SCORE: {out['score']}",
        f"アドバイス: {out['advice']}",
        f"例文: {out['example']}",
    ]
    return "\n".join(lines).strip()

# ---------- /api/message ----------
@app.route("/api/message", methods=["POST"])
def api_message_default():
    return _handle_message(normalize_context(request.args.get("context")))

@app.route("/api/message/<context_name>", methods=["POST"])
def api_message_context(context_name: str):
    return _handle_message(normalize_context(context_name))

def _handle_message(context_name: str):
    try:
        data = request.get_json(force=True) or {}
        text = (data.get("text") or "").strip()
        if not text:
            return jsonify({"reply": "入力が空です"}), 400
        out = call_model(text, context_name)
        reply_text = build_reply_text(out, context_name)
        return jsonify({
            "reply": reply_text,
            "score": out["score"],
            "status": out["status"],
            "hearts": hearts(out["score"]),
            "tone": tone_label(out["score"]),
            "advice": out["advice"],
            "example": out["example"],
            "context": context_name
        })
    except Exception as e:
        return jsonify({"reply": f"（サーバ例外）{e}"}), 200

# ---------- LINEペースト解析 ----------
def parse_line_thread(text: str) -> list[dict]:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    thread = []
    for line in lines:
        m = re.match(r'^([^\:：]+)[:：](.+)$', line)
        if m:
            sender = m.group(1).strip()
            msg = m.group(2).strip()
        else:
            sender = "相手" if not thread else thread[-1]["sender"]
            msg = line
        thread.append({"sender": sender, "text": msg})
    return thread

def analyze_line_context(thread: list[dict], context: str):
    convo = "\n".join(f'{m["sender"]}: {m["text"]}' for m in thread)
    return call_model(convo, context)

@app.route("/api/line_paste", methods=["POST"])
def api_line_paste():
    try:
        data = request.get_json(force=True)
        text = (data.get("text") or "").strip()
        context = data.get("context") or "恋愛"

        if not text:
            return jsonify({"reply": "入力が空です"}), 400

        thread = parse_line_thread(text)
        out = analyze_line_context(thread, context)

        reply = build_reply_text(out, context)
        return jsonify({"reply": reply, "score": out["score"], "status": out["status"]})
    except Exception as e:
        return jsonify({"reply": f"（サーバー例外）{e}"}), 200

# ---------- Root ----------
@app.get("/")
def root():
    return make_response(jsonify({
        "ok": True,
        "default_context": DEFAULT_CONTEXT,
        "thresholds": {"positive": POS_TH, "neutral": NEU_TH},
        "status_override": STATUS_OVERRIDE,
        "endpoints": ["/api/message", "/api/line_paste"]
    }), 200)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
