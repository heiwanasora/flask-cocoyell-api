# app.py — スミス（心理＋メンタリスト統合版）
import os
import re
import json
from typing import Any, Dict, List, Optional
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

# ---------- 環境変数 ----------
DEFAULT_CONTEXT = os.getenv("SMITH_CONTEXT", "心の整理")

# ---------- ユーティリティ ----------
def normalize_context(ctx: Optional[str]) -> str:
    if not ctx:
        return DEFAULT_CONTEXT
    ctx = str(ctx).strip().lower()
    mapping = {
        "love": "恋愛",
        "renai": "恋愛",
        "friend": "友人",
        "work": "仕事",
        "mental": "心",
    }
    for k, v in mapping.items():
        if k in ctx:
            return v
    return ctx

def hearts(score: int) -> str:
    s = max(0, min(100, int(score)))
    filled = s // 20
    return "❤️" * filled + "🤍" * (5 - filled)

# ---------- スミス心理＋メンタリスト統合プロンプト ----------
def build_system_prompt(context_name: str) -> str:
    return f"""
あなたは心理士であり、同時にメンタリスト的洞察を持つ日本語のカウンセラー「スミス」。
臨床心理学・ポジティブ心理学・人間関係心理学・恋愛心理学・認知行動療法（CBT）・NLP・非言語心理学の知見を使い、
ユーザーの文面から「本音・意図・距離感・脈・改善策」を読み取ります。

あなたの目的は、相手の文章に隠れた **心理の構造** を明らかにし、
心理学に基づいて「気づき」「整理」「行動」を導くことです。

ジャンル別の分析方針：

【恋愛】  
- 相手の言葉の温度・共感反応・行動傾向を心理学的に解析。  
- 「脈あり」「様子見」「脈なし」を推定し、理由を3つの心理的根拠で説明。  
- 愛着スタイル（回避型・安定型・不安型）も参考に。  

【友人】  
- 人間関係心理学を基に、信頼・距離・依存・期待のバランスを分析。  
- 相手が何を求め、何を避けようとしているかを心理学的に読み解く。  
- 問題がある場合、解決策を「心理士」として助言する。  

【心・仕事】  
- 感情・思考・行動の三層構造を整理。  
- 認知のゆがみ（白黒思考・過度な一般化など）を優しく修正する提案を行う。  

出力は **厳密なJSON** のみ。英語禁止。
スキーマ：
{{
  "category": "{context_name}",
  "core_meaning": "文の主題や要点（何について話しているか）",
  "emotion": "相手の心理状態・感情傾向（心理学的用語を含む）",
  "hidden_intent": "文に隠れた意図・本音・ニーズ",
  "psychological_reason": ["心理的根拠1", "心理的根拠2", "心理的根拠3"],
  "relationship_dynamics": "関係の温度・距離感・依存度（恋愛・友人なら）",
  "score": 0〜100,
  "status": "脈あり" | "様子見" | "脈なし" | "安定" | "不安定",
  "solution": "心理学的に見た改善策や具体行動提案",
  "advice": "スミスの一言アドバイス（温かく）"
}}
応答指針：
- 心理学の言葉を使いつつ、専門用語は平易に説明
- 相手を非難せず「理解・受容・希望」を重視
- 恋愛の場合、脈あり／なしの推定は感情・距離・関与の3軸で評価
- 友人・仕事では「信頼」「共感」「役割期待」を評価
    """.strip()

# ---------- モデル呼び出し ----------
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
        raw = resp.choices[0].message.content or ""
    except Exception as e:
        return {"reply": f"通信エラー: {e}"}

    raw = raw.replace("```json", "").replace("```", "")
    try:
        data = json.loads(raw)
    except Exception:
        data = {
            "category": context_name,
            "core_meaning": "解析失敗",
            "emotion": "不明",
            "hidden_intent": "感情データなし",
            "psychological_reason": ["JSON解析失敗"],
            "relationship_dynamics": "",
            "score": 50,
            "status": "様子見",
            "solution": "深呼吸して、整理してから再送信してください。",
            "advice": "焦らなくて大丈夫。また一緒に見ていこう。"
        }
    return data

# ---------- 整形 ----------
def build_reply_text(out: Dict[str, Any]) -> str:
    score = out.get("score", 50)
    lines = [
        f"📘 分析カテゴリ: {out.get('category','')}",
        f"🧩 主題: {out.get('core_meaning','')}",
        f"💭 心理状態: {out.get('emotion','')}",
        f"🎯 本音・意図: {out.get('hidden_intent','')}",
        "",
        "🔍 心理的根拠:",
        *[f"・{r}" for r in out.get("psychological_reason", [])],
        "",
        f"💞 関係性: {out.get('relationship_dynamics','')}",
        f"💓 状態: {out.get('status','')}   {hearts(score)}   SCORE: {score}",
        "",
        f"🧠 解決策: {out.get('solution','')}",
        f"💬 スミスの一言: {out.get('advice','')}"
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
        "model": "スミス心理＋メンタリスト統合版",
        "modes": ["恋愛心理学", "人間関係心理学", "臨床心理学(CBT)", "NLP・感情分析"],
        "endpoints": ["/api/message"]
    }), 200)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
