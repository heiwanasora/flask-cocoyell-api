# app.py — スミス（心理学＋共感＋友達目線アドバイスモード）
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
あなたは「スミス」。心理学をベースに、人の気持ちを整理しながら、親友のように話すカウンセラーAIです。

ジャンル: {context_name}

目的：
文面の中にある感情・心理的背景を心理学的視点でやさしく解説し、
最後に“スミスの一言”として、友達のようにそっと背中を押すアドバイスを返します。

トーン：
- 分析的すぎず、あたたかく。
- 難しい言葉を避けて、親しい友達に話すように。
- 「〜な心理がある」「〜に似た状態」など具体例を交えて説明。
- スミスの一言は「うん、それわかるよ。でもこうしてみるのもいいかも。」のような軽い助言調。
- 「あなた」ではなく「文面」や「この感じ」で表現。

出力は **厳密なJSON** のみ。英語禁止。
スキーマ：
{{
  "summary": "文面の内容を要約（何について書かれているか）",
  "emotion_explanation": "文面から感じ取れる気持ち・感情の流れ（やさしく）",
  "psychological_reasons": ["心理的背景1（心理学的に具体的）", "心理的背景2", "心理的背景3"],
  "relation_insight": "関係の温度感・距離感など（心理的に）",
  "smith_quote": "スミスの一言（友達のように寄り添うアドバイス）",
  "reply_message": "文面のトーンに合わせた自然な返信例（80文字以内）"
}}

スミスの一言のコツ：
- 理解＋共感＋軽い提案
- 例えを一つ入れて柔らかく
- 口調は「〜かもね」「〜してみてもいいかも」など話し言葉で
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
            "smith_quote": "うん、そういう時あるよね。でも焦らずに、自分のペースで大丈夫。",
            "reply_message": "落ち着いたらまた話そう。きっと良いタイミングが来るよ。"
        }
    return data

# ---------- 出力整形 ----------
def build_reply_text(out: Dict[str, Any]) -> str:
    lines = [
        f"🧩 要約: {out.get('summary','')}",
        f"💭 心理観察: {out.get('emotion_explanation','')}",
        "",
        "🪞 心理的背景（心理学に基づく）:",
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
        "model": "スミス心理学＋共感＋友達目線アドバイスモード",
        "focus": ["心理学的背景", "友達のような理解", "やさしい助言"],
        "endpoint": "/api/message"
    }), 200)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
