# app.py — スミス（心理要約＋柔らか説明モード）
import os
import json
from typing import Any, Dict, Optional
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from openai import OpenAI

# ---------- Flask ----------
app = Flask(__name__)
CORS(app)
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_MIMETYPE'] = 'application/json; charset=utf-8'

# ---------- OpenAI ----------
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---------- 環境 ----------
DEFAULT_CONTEXT = os.getenv("SMITH_CONTEXT", "人間関係")

# ---------- 共通ユーティリティ ----------
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

def hearts(score: int) -> str:
    s = max(0, min(100, int(score)))
    filled = s // 20
    return "❤️" * filled + "🤍" * (5 - filled)

# ---------- プロンプト（心理要約＋柔らか説明） ----------
def build_system_prompt(context_name: str) -> str:
    return f"""
あなたは心理カウンセラー兼メンタリストの「スミス」。
心理学・恋愛心理・行動心理学・感情理論をもとに、
相手の文面を「やさしくわかりやすく説明する専門家」です。

あなたの目的：
文面を要約しながら、心理学的に「相手がどんな気持ちでそう言っているのか」を
人に安心感を与えるように柔らかい言葉で説明します。

ジャンル: {context_name}

出力は **厳密なJSON** のみ。英語禁止。
スキーマ：
{{
  "summary": "文面の内容を具体的に要約（何の話か）",
  "emotion_explanation": "心理学に基づく相手の気持ちの説明（やさしく・共感的に）",
  "psychological_reasons": ["背景1", "背景2", "背景3"],
  "tone": "温度感（冷たい・中立・温かい・情熱的など）",
  "relation_insight": "心理学的に見た関係のバランスや相性の傾向",
  "advice": "スミスの一言アドバイス（安心感のある言葉）"
}}

出力トーン：
- 心理学的説明をしつつ、まるで寄り添うような語り口
- 相手を責めず、心の仕組みをやさしく説明する
- 専門用語は使わず、人が理解しやすい自然な表現にする
    """.strip()

# ---------- モデル呼び出し ----------
def call_model(user_text: str, context_name: str) -> Dict[str, Any]:
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.6,
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
            "summary": "解析に失敗しました。",
            "emotion_explanation": "文面を心理的に読み取れませんでした。",
            "psychological_reasons": ["JSON形式エラー"],
            "tone": "中立",
            "relation_insight": "情報不足",
            "advice": "またゆっくり考えてみましょう。"
        }
    return data

# ---------- 整形 ----------
def build_reply_text(out: Dict[str, Any]) -> str:
    lines = [
        f"🧩 要約: {out.get('summary','')}",
        f"💭 心理的説明: {out.get('emotion_explanation','')}",
        "",
        "🪞 背景となる心理:",
        *[f"・{r}" for r in out.get('psychological_reasons', [])],
        "",
        f"🌡️ 温度感: {out.get('tone','')}",
        f"🤝 関係の傾向: {out.get('relation_insight','')}",
        "",
        f"💬 スミスの一言: {out.get('advice','')}",
    ]
    return "\n".join(lines)

# ---------- エンドポイント ----------
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
        "model": "心理要約＋柔らか説明スミス",
        "focus": ["心理学的説明", "感情理解", "メンタリスト共感"],
        "endpoint": "/api/message"
    }), 200)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
