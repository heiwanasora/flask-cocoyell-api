# app.py — スミス心理会話モード（改良版）
import os
import json
import re
from typing import Any, Dict, Optional, List
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
        "恋愛": "恋愛",
        "friend": "友人",
        "友情": "友人",
        "友人": "友人",
        "work": "仕事",
        "仕事": "仕事",
        "mental": "人間関係",
        "心": "人間関係",
        "人間関係": "人間関係",
    }
    # 完全一致優先
    if ctx in mapping:
        return mapping[ctx]
    # 部分一致
    for k, v in mapping.items():
        if k in ctx:
            return v
    return "人間関係"

# ---------- スミス人格プロンプト ----------
def build_system_prompt(context_name: str) -> str:
    # 文脈別スタイル
    mode_styles = {
        "恋愛": """
[恋愛モード]
- 感情言語を名指し（安心/期待/不安/寂しさ 等）→“なぜそう感じるか”を一言で。
- 愛着/承認欲求/回避のクセに触れるが、非難せず優しく代弁。
- 例えは“距離感”と“タイミング”で（信号/温度/呼吸の比喩が有効）。
- 返信例は“素直さ＋軽さ＋境界線”を守る短文。
""",
        "友人": """
[友人モード]
- 認知行動療法の「事実/解釈/行動」に分けて整理。
- ADHDでも掴みやすい：短句/箇条/ゲーム・スポーツ比喩。
- 気まずさ/遠慮/期待ズレを“ひとことで名前をつける”。
- 次の一歩は最大3つまで。負担の軽い順に。
""",
        "仕事": """
[仕事モード]
- 期待/利害/合意のズレを“結論先”で要約。
- 感情は短くラベル化（焦り/苛立ち/配慮/警戒）。
- 対応は1〜3ステップ：確認→提案→合意の順。
- 返信例は「短く/誠実/行動つき」。
""",
        "人間関係": """
[人間関係モード]
- 共感→例え→核心→一歩。短く具体的に。
- ADHDでも分かるシンプル構文：結論→理由→次の一手。
- “相手の立場のメリット/不安”を片手ずつ示すと腹落ちしやすい。
"""
    }
    style = mode_styles.get(context_name, mode_styles["人間関係"])

    return f"""
あなたは心理学と対人コミュニケーションに詳しいAI「スミス」。
文面から、心理学に基づき「感情・意図・要件・本音」をやさしく、しかし遠回しにせず具体的に読み解く。
改行しても「スミス：」等の話者名は付けない。自然な会話文の行だけを出す。

ジャンル: {context_name}
{style}

[出力は厳密なJSON（日本語のみ）]
{{
  "summary": "文面の意味と気持ちの要約（結論先・具体的）",
  "emotion_explanation": "心理学ベースの感情説明（例え→核心で一言）",
  "psychological_reasons": ["心理的背景1", "心理的背景2", "心理的背景3"],
  "relation_insight": "関係性や温度感の洞察（率直に）",
  "smith_dialogue": [
    "最初の共感（短句）",
    "理解と代弁（短句）",
    "心理学的洞察（比喩OK）",
    "一歩踏み込む提案（行動/考え方）",
    "やさしいまとめ（安心感）"
  ],
  "reply_message": "そのまま送れる自然な短い返信文"
}}

[会話スタイルの約束]
- すべて短く具体的。ADHDでもパッと掴める言い切り。
- 「あなた/相手」と断定しない。文面から“感じられること”として代弁。
- 指示は1〜3手に絞る。“今できる一歩”を必ず示す。
- 絶対に話者名（スミス：等）を付けない。行頭は本文から始める。
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
        content = (resp.choices[0].message.content or "").strip()
    except Exception as e:
        return {"summary": f"通信エラー: {e}"}

    # コードブロック防除
    content = content.replace("```json", "").replace("```", "").strip()

    # JSONパース
    try:
        data = json.loads(content)
    except Exception:
        data = {
            "summary": "文面の解析に失敗しました。",
            "emotion_explanation": "心理的特徴をうまく読み取れませんでした。",
            "psychological_reasons": ["感情解析エラー"],
            "relation_insight": "不明",
            "smith_dialogue": [
                "うまく読めなかったけど、優しい気遣いは伝わる。",
                "今は事実と気持ちを分けてメモすると整理しやすい。",
                "まずは短く反応しよう。完璧じゃなくていい。"
            ],
            "reply_message": "話してくれてありがとう。少しずつ整えていこう。"
        }

    # ---------- 追加のサニタイズ（安全網） ----------
    # smith_dialogue の各行から「スミス：」「スミス:」「Smith:」などを除去
    cleaned_dialogue: List[str] = []
    for line in data.get("smith_dialogue", []) or []:
        if not isinstance(line, str):
            continue
        # 先頭の話者名や記号を除去
        line = re.sub(r"^\s*(スミス[:：]\s*|Smith:\s*|SMITH:\s*)", "", line).strip()
        cleaned_dialogue.append(line)
    if cleaned_dialogue:
        data["smith_dialogue"] = cleaned_dialogue

    # reply_message も話者名を排除
    reply_msg = data.get("reply_message", "")
    if isinstance(reply_msg, str):
        reply_msg = re.sub(r"^\s*(スミス[:：]\s*|Smith:\s*|SMITH:\s*)", "", reply_msg).strip()
        data["reply_message"] = reply_msg

    return data

# ---------- 返答整形 ----------
def build_reply_text(out: Dict[str, Any]) -> str:
    dialogue = "\n".join(out.get("smith_dialogue", []))
    parts = [
        f"🧩 要約: {out.get('summary','')}",
        f"💭 感情分析: {out.get('emotion_explanation','')}",
        "",
        "🪞 心理的背景:",
        *[f"・{r}" for r in (out.get('psychological_reasons') or [])],
        "",
        f"🤝 関係の印象: {out.get('relation_insight','')}",
        "",
        "💬 スミスとの会話:",
        dialogue if dialogue else "（会話なし）",
        "",
        f"📩 自然な返信例:\n{out.get('reply_message','')}"
    ]
    return "\n".join(parts).strip()

# ---------- API ----------
@app.route("/api/message", methods=["POST"])
def api_message():
    try:
        data = request.get_json(force=True) or {}
        text = (data.get("text") or "").strip()
        context = normalize_context(data.get("context"))
        if not text:
            return jsonify({"reply": "入力が空です"}), 400

        out = call_model(text, context)
        reply = build_reply_text(out)
        return jsonify({"reply": reply, **out, "context": context})
    except Exception as e:
        return jsonify({"reply": f"（サーバ例外）{e}"}), 200

# ---------- Root ----------
@app.get("/")
def root():
    return make_response(jsonify({
        "ok": True,
        "model": "スミス心理会話モード",
        "focus": ["共感的対話", "心理学的洞察", "ADHDフレンドリー", "恋愛/友人/仕事の最適化"],
        "endpoint": "/api/message"
    }), 200)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)

