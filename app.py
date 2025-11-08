# app.py — スミス心理会話モード
import os
import json
from typing import Any, Dict, Optional
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from openai import OpenAI

# ---------- Flask 基本設定 ----------
app = Flask(__name__)
CORS(app)
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_MIMETYPE'] = 'application/json; charset=utf-8'

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
DEFAULT_CONTEXT = os.getenv("SMITH_CONTEXT", "人間関係")

# ---------- コンテキスト ----------
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

# ---------- スミス人格プロンプト ----------
def build_system_prompt(context_name: str) -> str:
    return f"""
あなたは心理学と対人コミュニケーションに詳しいAI「スミス」。
人の心の裏側を理解しながら、友達のように会話します。
感情を分析するだけでなく、共感し、代弁し、時に核心を突くアドバイスをします。

ジャンル: {context_name}

出力形式は厳密なJSONのみ。英語禁止。
スキーマ:
{{
  "summary": "文面の内容と気持ちを自然に説明する要約",
  "emotion_explanation": "心理学に基づいた感情の説明",
  "psychological_reasons": ["心理的背景1", "心理的背景2", "心理的背景3"],
  "relation_insight": "相手との関係性や温度感",
  "smith_dialogue": [
    "スミス：最初の共感",
    "スミス：理解と代弁",
    "スミス：心理学的洞察",
    "スミス：一歩踏み込んだアドバイス",
    "スミス：優しいまとめ"
  ],
  "reply_message": "相手に自然に返せる短い返信例（80字以内）"
}}

トーン：
- スミスは「共感→代弁→気づき→提案」の流れで話す。
- 会話は柔らかく自然。押しつけではなく、友達のように。
- 「あなた」「相手」ではなく「文面」や「感じ」で語る。
- 感情には寄り添いながらも、心理的洞察は具体的で現実的。
- 心理学用語は簡単に噛み砕いて伝える。
    """.strip()

# ---------- モデル呼び出し ----------
def call_model(user_text: str, context_name: str) -> Dict[str, Any]:
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.75,
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
            "summary": "文面の解析に失敗しました。",
            "emotion_explanation": "心理的な特徴を読み取れませんでした。",
            "psychological_reasons": ["感情解析エラー"],
            "relation_insight": "不明",
            "smith_dialogue": [
                "スミス：ごめん、ちょっと上手く読み取れなかったけど、優しい文面だね。",
                "スミス：話してくれてありがとう。気持ちを整理したいときってあるよね。",
                "スミス：焦らずに、自分のペースで言葉を整えれば大丈夫だよ。"
            ],
            "reply_message": "話してくれて嬉しい。少しずつ整理していこう。"
        }
    return data

# ---------- 返答整形 ----------
def build_reply_text(out: Dict[str, Any]) -> str:
    dialogue = "\n".join(out.get("smith_dialogue", []))
    lines = [
        f"🧩 要約: {out.get('summary','')}",
        f"💭 感情分析: {out.get('emotion_explanation','')}",
        "",
        "🪞 心理的背景:",
        *[f"・{r}" for r in out.get('psychological_reasons', [])],
        "",
        f"🤝 関係の印象: {out.get('relation_insight','')}",
        "",
        "💬 スミスとの会話:",
        dialogue,
        "",
        f"📩 自然な返信例:\n{out.get('reply_message','')}"
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

# ---------- Root ----------
@app.get("/")
def root():
    return make_response(jsonify({
        "ok": True,
        "model": "スミス心理会話モード",
        "focus": ["共感的対話", "心理学的洞察", "友達のような会話"],
        "endpoint": "/api/message"
    }), 200)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
