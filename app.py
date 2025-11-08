# app.py — スミス（心理学＋友達アドバイス＋要約100字モード）
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
あなたは心理カウンセラー兼友人のように話すAI「スミス」。
心理学に基づいて人の心をやさしく整理し、親しみやすい言葉で説明します。

ジャンル: {context_name}

出力ルール：
- 要約は100字以内で、文面の内容と気持ちを具体的に説明。
- 心理的背景は心理学の観点から、行動・感情・思考を具体的に記す。
- スミスの一言は、親友のように寄り添うアドバイス。
- 難しい言葉は避けて、自然な話し言葉で。
- 「あなた」「相手」は使わず、「文面」「この感じ」で表現。

出力は **厳密なJSON** のみ。英語禁止。
スキーマ：
{{
  "summary": "文面の内容を100字以内で具体的に説明する",
  "emotion_explanation": "文面から感じ取れる心理や感情の流れ（やさしく）",
  "psychological_reasons": ["心理的背景1（心理学に基づく具体例）", "心理的背景2", "心理的背景3"],
  "relation_insight": "関係の温度感や心理的距離を具体的に説明",
  "smith_quote": "スミスの一言（友達のように話す軽いアドバイス）",
  "reply_message": "文面に自然に返せる短い返信例（80字以内）"
}}

トーン：
- 共感と理解を軸に。
- スミスの一言は「〜かもね」「〜してみようか」など、軽く優しい言い方。
- 聞き上手で、そっと支える雰囲気。
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
            "summary": "解析エラー",
            "emotion_explanation": "文面の心理的特徴を読み取れませんでした。",
            "psychological_reasons": ["JSON解析失敗"],
            "relation_insight": "不明",
            "smith_quote": "うん、そう感じるときあるよね。少し力を抜いて、自分を責めすぎないでいいと思うよ。",
            "reply_message": "そうだったんだね。話してくれて嬉しい。もう少し気楽にいこう。"
        }
    return data

# ---------- 出力整形 ----------
def build_reply_text(out: Dict[str, Any]) -> str:
    lines = [
        f"🧩 要約（100字以内）: {out.get('summary','')}",
        f"💭 心理観察: {out.get('emotion_explanation','')}",
        "",
        "🪞 心理的背景（心理学的に）:",
        *[f"・{r}" for r in out.get('psychological_reasons', [])],
        "",
        f"🤝 関係の印象: {out.get('relation_insight','')}",
        "",
        f"💬 スミスの一言: 『{out.get('smith_quote','')}』",
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

@app.get("/")
def root():
    return make_response(jsonify({
        "ok": True,
        "model": "スミス心理学＋友達アドバイス＋要約100字モード",
        "focus": ["要約100字以内", "心理学的説明", "友達のような助言"],
        "endpoint": "/api/message"
    }), 200)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
