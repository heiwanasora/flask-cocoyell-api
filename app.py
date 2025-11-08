# app.py — スミス（心理要約＋刺さる返信モード）
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

# --- ユーティリティ ---
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

# --- スミス統合プロンプト（刺さる返信型） ---
def build_system_prompt(context_name: str) -> str:
    return f"""
あなたは心理カウンセラー兼メンタリストの「スミス」。
心理学・恋愛心理・言語感情分析をもとに、人の心を見抜き、相手に“刺さる返信文”をつくるプロです。

ジャンル: {context_name}

目的：
文面を心理学的に解析し、相手の気持ちをやさしく説明したうえで、
最後に相手の心に響く一言（smith_quote）と、
その一言を元に「自然で刺さる返信文」（reply_message）を生成します。

返信文は：
- 押しつけず、でも相手が「ハッ」とする心理的深さを含む
- 優しさの中に“芯”がある
- 最大80文字以内で自然な日本語
- 絵文字や記号は使わない

出力は **厳密なJSON** のみ。英語禁止。
スキーマ：
{{
  "summary": "文面の内容を要約",
  "emotion_explanation": "心理学に基づく相手の気持ちの説明（やさしく）",
  "psychological_reasons": ["心理背景1", "心理背景2", "心理背景3"],
  "relation_insight": "関係の心理的バランス（距離・信頼・温度など）",
  "smith_quote": "踏み込んだスミスの核心の一言（詩的で短く）",
  "reply_message": "相手に自然に送れる、刺さる返信文（80文字以内）"
}}

出力トーン：
- 心理説明は温かく・落ち着いた調子で
- smith_quoteは核心を突く詩的な一文
- reply_messageは“そのままLINEで送れる自然さ”と“心理的余韻”の両立
    """.strip()

# --- モデル呼び出し ---
def call_model(user_text: str, context_name: str) -> Dict[str, Any]:
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.65,
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
            "emotion_explanation": "文面を読み取れませんでした。",
            "psychological_reasons": ["JSON解析失敗"],
            "relation_insight": "不明",
            "smith_quote": "沈黙の中にも、想いは残る。",
            "reply_message": "ゆっくりで大丈夫。あなたの気持ちが落ち着いたら、また話そう。"
        }
    return data

# --- 整形 ---
def build_reply_text(out: Dict[str, Any]) -> str:
    lines = [
        f"🧩 要約: {out.get('summary','')}",
        f"💭 心理的説明: {out.get('emotion_explanation','')}",
        "",
        "🪞 背景となる心理:",
        *[f"・{r}" for r in out.get('psychological_reasons', [])],
        "",
        f"🤝 関係の傾向: {out.get('relation_insight','')}",
        "",
        f"💬 スミスの一言: 『{out.get('smith_quote','')}』",
        "",
        f"📩 刺さる返信文:\n{out.get('reply_message','')}"
    ]
    return "\n".join(lines)

# --- API ---
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
        "model": "スミス心理要約＋刺さる返信モード",
        "focus": ["心理学的説明", "核心の一言", "相手に刺さる返信"],
        "endpoint": "/api/message"
    }), 200)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
