# app.py
import os
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

# ---------- 環境変数（文脈＆閾値） ----------
DEFAULT_CONTEXT = os.getenv("SMITH_CONTEXT", "恋愛")  # 恋愛 / 友人 / 仕事 など
POS_TH = int(os.getenv("SMITH_POSITIVE_THRESHOLD", "70"))  # 脈あり下限
NEU_TH = int(os.getenv("SMITH_NEUTRAL_THRESHOLD", "40"))   # 様子見下限
STATUS_OVERRIDE = os.getenv("SMITH_STATUS_OVERRIDE", "0") == "1"

# ---------- ユーティリティ ----------
def normalize_context(ctx: Optional[str]) -> str:
    if not ctx:
        return DEFAULT_CONTEXT
    ctx = str(ctx).strip()
    # 代表3種のゆるい同義語
    alias = {
        "恋愛": {"恋愛", "love", "renai"},
        "友人": {"友人", "友情", "friend", "friends", "yuujin"},
        "仕事": {"仕事", "ビジネス", "work", "business", "shigoto"},
    }
    for k, vals in alias.items():
        if ctx in vals:
            return k
    return ctx  # 任意の文脈名もそのまま通す

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

def build_system_prompt(context_name: str) -> str:
    return f"""
あなたは「スミス」。日本語で話す、共感と洞察に優れた感情カウンセラー。
対象の会話ジャンル（文脈）: {context_name}

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
制約:
- "reasons" は2〜3個、各40字以内。引用は「…」を用いる。
- "example" は文脈と整合。無根拠の誘い（突然のデート/泊まり/旅行/告白など）禁止。
- 質問形は可。ただし矛盾はNG。句読点・記号の連続禁止。
- 出力は上記JSONのみ。前後の説明・コードブロック・英語は禁止。
""".strip()

# ---------- モデル呼び出し（UTF-8→JSON安全パース） ----------
def call_model(user_text: str, context_name: str) -> Dict[str, Any]:
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.6,  # 再現性寄り
        messages=[
            {"role": "system", "content": build_system_prompt(context_name)},
            {"role": "user", "content": user_text},
        ],
        # 文字化け/バイナリ化の互換のため response_format は使わない
    )

    content = resp.choices[0].message.content
    if isinstance(content, bytes):
        content = content.decode("utf-8", errors="ignore")
    content = (content or "").strip()

    # ```json ... ``` で来た時の剥がし
    if content.startswith("```"):
        content = content.strip("`")
        i = content.find("{")
        if i != -1:
            content = content[i:]

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

    # 閾値で補完/上書き
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

# ---------- 応答の文字列を1回だけ作る（重複防止） ----------
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

# ---------- API ----------
@app.route("/api/message", methods=["POST"])
def api_message_default():
    """既定文脈（環境変数 SMITH_CONTEXT）で解析"""
    return _handle_message(normalize_context(request.args.get("context")))

@app.route("/api/message/<context_name>", methods=["POST"])
def api_message_context(context_name: str):
    """URLで文脈を切替（例：/api/message/友人, /api/message/仕事）"""
    return _handle_message(normalize_context(context_name))

def _handle_message(context_name: str):
    try:
        data = request.get_json(force=True) or {}
        text = (data.get("text") or data.get("message") or "").strip()
        if not text:
            return jsonify({
                "reply": "（エラー）入力が空です。",
                "score": 50,
                "hearts": "❤️❤️🤍🤍🤍"
            }), 400

        out = call_model(text, context_name)
        reply_text = build_reply_text(out, context_name)

        return jsonify({
            "reply": reply_text,                 # ← Flutterはこれだけ描画すればOK（重複しない）
            "score": out["score"],
            "status": out["status"],
            "hearts": hearts(out["score"]),
            "tone": tone_label(out["score"]),
            "advice": out["advice"],
            "example": out["example"],
            "context": context_name,
            "thresholds": {"positive": POS_TH, "neutral": NEU_TH},
            "status_override": STATUS_OVERRIDE,
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
        "default_context": DEFAULT_CONTEXT,
        "thresholds": {"positive": POS_TH, "neutral": NEU_TH},
        "status_override": STATUS_OVERRIDE,
        "how_to_switch": {
            "by_path": "POST /api/message/友人 など",
            "by_query": "POST /api/message?context=仕事 など"
        }
    }), 200)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
