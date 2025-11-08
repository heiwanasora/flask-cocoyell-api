# app.py — スミス（文面主導＋理解・同感・例えモード）
import os
import json
from typing import Any, Dict, Optional
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
CORS(app)
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_MIMETYPE'] = 'application/json; charset=utf-8'

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
DEFAULT_CONTEXT = os.getenv("SMITH_CONTEXT", "人間関係")

# ---------- コンテキスト処理 ----------
def normalize_context(ctx: Optional[str]) -> str:
    if not ctx:
        return DEFAULT_CONTEXT
    ctx = str(ctx).strip().lower()
    mapping = {
        "love": "恋愛",
        "renai": "恋愛",
        "friend": "友人",
        "work": "仕事",
        "mental": "心"
    }
    for k, v in mapping.items():
        if k in ctx:
            return v
    return ctx

# ---------- スミス心理モデル（理解・共感・例え） ----------
def build_system_prompt(context_name: str) -> str:
    return f"""
あなたは心理カウンセラー兼メンタリスト「スミス」。
心理学・行動分析・恋愛心理をもとに、与えられた文面から心の構造を客観的に読み解きます。

目的：
文面に込められた感情・背景を心理学的に観察し、
最後に「スミスの一言」として、理解・共感・例えを1行にまとめた詩的なメッセージを返します。

🧠 一言構成（3要素）：
- **理解**：文面の心理を見抜いた一言（「〜ように見える」「〜が感じられる」）
- **共感**：感情の温度に寄り添う言葉（「わかる気がする」「その静けさも優しさだね」）
- **例え**：心理を自然にたとえる表現（天気、光、風、海、道、時間、音など）

出力は **厳密なJSON** のみ。英語禁止。
スキーマ：
{{
  "summary": "文面の内容を要約（何について書かれているか）",
  "emotion_explanation": "文面から観察される心理的傾向や感情（第三者視点）",
  "psychological_reasons": ["心理的背景1", "心理的背景2", "心理的背景3"],
  "relation_insight": "表現から見える関係性や距離感",
  "smith_quote": "理解＋共感＋例えを1行でまとめたスミスの一言",
  "reply_message": "文面に呼応する自然な返信文（80文字以内）"
}}

制約：
- 「あなた」「相手」は使わない。文面・言葉を主語にする。
- スミスの一言は20〜40文字程度。
- 全体トーンは「静かであたたかい観察」。
- 例え表現には自然のイメージを使うこと（光、風、海、空、雨など）。
    """.strip()

# ---------- モデル呼び出し ----------
def call_model(user_text: str, context_name: str) -> Dict[str, Any]:
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.7,
            messages=[
                {"role": "system", "content": build_system_prompt(context_name)},
                {"role": "user", "content": user_text},
            ],
        )
        content = resp.choices[0].message.content or ""
    except Exception as e:
        return {"summary": f"通信エラー: {e}"}

    content = content.replace("```json", "").replace("```", "")
    try:
        data = json.loads(content)
    except Exception:
        data = {
            "summary": "解析エラー",
            "emotion_explanation": "文面の心理的特徴を読み取れませんでした。",
            "psychological_reasons": ["JSON解析失敗"],
            "relation_insight": "不明",
            "smith_quote": "静けさの奥に、まだ温かい余韻が残っている。",
            "reply_message": "言葉の温度が戻るまで、少しだけ静けさを置いておこう。"
        }
    return data

# ---------- 出力整形 ----------
def build_reply_text(out: Dict[str, Any]) -> str:
    lines = [
        f"🧩 要約: {out.get('summary','')}",
        f"💭 心理観察: {out.get('emotion_explanation','')}",
        "",
        "🪞 心理的背景:",
        *[f"・{r}" for r in out.get('psychological_reasons', [])],
        "",
        f"🤝 関係性の傾向: {out.get('relation_insight','')}",
        "",
        f"💬 スミスの一言: 『{out.get('smith_quote','')}』",
        "",
        f"📩 文面に呼応する返信文:\n{out.get('reply_message','')}"
    ]
    return "\n".join(lines)

# ---------- API ----------
@app.route("/api/message", methods=["POST"])
def api_message():
    try:
        data = request.get_json(force=True)
        text = (data.get("text") or "").strip()
        context = normalize_context(data.get("context"))
        if not text:
            return jsonify({"reply": "入力が空です"}), 400

        out = call_model(text, context)
        reply = build_reply_text(out)
        return jsonify({"reply": reply, **out})
    except Exception as e:
        return jsonify({"reply": f"（サーバ例外）{e}"}), 200

@app.get("/")
def root():
    return make_response(jsonify({
        "ok": True,
        "model": "スミス心理観察＋理解・共感・例えモード",
        "focus": ["心理学的観察", "詩的共感", "自然な返信"],
        "endpoint": "/api/message"
    }), 200)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
