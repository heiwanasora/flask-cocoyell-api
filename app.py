# app.py
import os
import json
from typing import Any, Dict, List
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
CORS(app)
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_MIMETYPE'] = 'application/json; charset=utf-8'

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---- 文脈&閾値（環境変数で調整可） ----
SMITH_CONTEXT = os.getenv("SMITH_CONTEXT", "恋愛")
POS_TH = int(os.getenv("SMITH_POSITIVE_THRESHOLD", "70"))
NEU_TH = int(os.getenv("SMITH_NEUTRAL_THRESHOLD", "40"))
STATUS_OVERRIDE = os.getenv("SMITH_STATUS_OVERRIDE", "0") == "1"

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
    if score >= POS_TH: return "脈あり"
    if score >= NEU_TH: return "様子見"
    return "脈なし"

# ---- プロンプト（厳格JSONで返す指示。*出力*は後段で安全パース） ----
LINE_CONTEXT_STYLE = f"""
あなたは「スミス」。日本語で話す、共感と洞察に優れた感情カウンセラー。
対象の会話ジャンル（文脈）: {SMITH_CONTEXT}

会話テキストから「脈あり/様子見/脈なし」を判定し、相手が文章で何を意図しているかを特定し、
理由とスコア、具体的な例文までを返す。

必ず **日本語のみ**・**厳密なJSON** で出力し、余分な文字は一切出さない。
JSONスキーマ:
{{
  "status": "脈あり" | "様子見" | "脈なし",
  "intent": "相手は文章で何を意図/感情として伝えているか一言で",
  "analysis": "スミスの解析（2〜3文・共感＋洞察）",
  "reasons": ["根拠1(40字以内・必要なら「…」で引用)", "根拠2", "根拠3"],
  "score": 0-100 の整数（100=強い好意・信頼）,
  "advice": "次の一歩の提案を1行（カタカナ見出し不要・値だけ）",
  "example": "文脈と整合する一言（40字以内・過剰な誘い禁止・質問形可）"
}}
"""

# ---- OpenAI呼び出し（安全にテキスト化→JSONパース） ----
def call_model(user_text: str) -> Dict[str, Any]:
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.6,
        messages=[
            {"role": "system", "content": LINE_CONTEXT_STYLE},
            {"role": "user", "content": user_text},
        ],
        # NOTE: 古い環境での文字化け/バイナリ化を避けるため、response_formatは使わない
    )

    content = resp.choices[0].message.content
    if isinstance(content, bytes):
        # 念のため：バイナリで来た場合はUTF-8で復号
        content = content.decode("utf-8", errors="ignore")
    content = (content or "").strip()

    # もし ```json ... ``` で囲まれてきたら剥がす
    if content.startswith("```"):
        content = content.strip("`")
        i = content.find("{")
        if i != -1:
            content = content[i:]

    # JSONパース（失敗時はフォールバック）
    try:
        data = json.loads(content)
    except Exception:
        data = {
            "status": "様子見",
            "intent": "慎重に様子を見ている",
            "analysis": "出力の整形に失敗しましたが、中庸な反応です。",
            "reasons": ["JSONで受け取れなかったため暫定判断。"],
            "score": 50,
            "advice": "無理せず落ち着いてやり取りを続けよう😊",
            "example": "気づいたことがあれば、ゆっくり話そう。"
        }

    # 正規化
    try:
        score = int(data.get("score", 50))
    except Exception:
        score = 50
    score = max(0, min(100, score))

    model_status = (data.get("status") or "").strip()
    if model_status not in ("脈あり", "様子見", "脈なし"):
        model_status = ""

    score_status = status_from_score(score)
    final_status = score_status if (STATUS_OVERRIDE or not model_status) else model_status

    reasons: List[str] = [str(x).strip() for x in (data.get("reasons") or []) if str(x).strip()]
    reasons = reasons[:3]

    cleaned = {
        "status": final_status,
        "intent": (data.get("intent") or "").strip(),
        "analysis": (data.get("analysis") or "").strip(),
        "reasons": reasons,
        "score": score,
        "advice": (data.get("advice") or "").strip(),
        "example": (data.get("example") or "").strip(),
    }

    # 軽い整形／安全弁
    banned = ("結婚", "同棲", "泊ま", "旅行", "キスしよう")
    if any(x in cleaned["example"] for x in banned):
        cleaned["example"] = "負担にならない範囲で、気持ちを少し教えてくれる？"
    cleaned["example"] = cleaned["example"].replace("。。", "。").replace("、、", "、").strip(" 　")
    for i, r in enumerate(cleaned["reasons"]):
        cleaned["reasons"][i] = r.replace("。。", "。").replace("、、", "、").strip(" 　")

    return cleaned

# ---- API ----
@app.route("/api/message", methods=["POST"])
def api_message():
    try:
        data = request.get_json(force=True) or {}
        text = (data.get("text") or data.get("message") or "").strip()
        if not text:
            return jsonify({"reply": "（エラー）入力が空です。", "score": 50, "hearts": "❤️❤️🤍🤍🤍"}), 400

        out = call_model(text)

        lines = []
        lines.append(f"心理の要約: {out['intent'] or '（意図の要約）'}")
        if out["reasons"]:
            lines.append("理由:")
            lines.extend([f"・{r}" for r in out["reasons"]])
        lines.append("")
        lines.append(f"スミスの解析: {out['analysis'] or '（解析）'}")
        lines.append(f"ステータス: {out['status']} （文脈: {SMITH_CONTEXT}）")
        lines.append(f"{hearts(out['score'])}   SCORE: {out['score']}")
        lines.append(f"アドバイス: {out['advice']}")
        if out["example"]:
            lines.append(f"例文: {out['example']}")
        reply_text = "\n".join(lines).strip()

        return jsonify({
            "reply": reply_text,
            "status": out["status"],
            "intent": out["intent"],
            "analysis": out["analysis"],
            "reasons": out["reasons"],
            "score": out["score"],
            "hearts": hearts(out["score"]),
            "tone": tone_label(out["score"]),
            "advice": out["advice"],
            "example": out["example"],
            "context": SMITH_CONTEXT,
            "thresholds": {"positive": POS_TH, "neutral": NEU_TH},
        })
    except Exception as e:
        return jsonify({
            "reply": f"（サーバ例外）{e}",
            "score": 50,
            "hearts": "❤️❤️🤍🤍🤍",
            "advice": "もう一度お試しください。"
        }), 200

@app.get("/")
def root():
    return make_response(jsonify({
        "ok": True,
        "context": SMITH_CONTEXT,
        "thresholds": {"positive": POS_TH, "neutral": NEU_TH},
        "status_override": STATUS_OVERRIDE
    }), 200)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
