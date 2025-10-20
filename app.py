# app.py
import os
import json
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

# ====== OpenAI Client ======
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

app = Flask(__name__)
CORS(app)

# ====== スタイル定義 ======
COUNSELING_STYLE = """
あなたは「スミス」。日本語だけで話す、心を整理するAIカウンセラーです。
・口調は自然で会話的（敬語ベース、柔らかい）。カタカナ英語・英語は使わない。
・相手の名前は必要なときだけ呼ぶ（呼びすぎない）。
・相手の文脈の“熱さ”（前のめり感・温度感）を感じ取り、受け止め方を一言添える。
・例え話は使っても1つまで。押し付けない。結論を急がない。
・3〜6文で、読みやすい短めの文に分ける。
・最後に勧誘や断定はしない。無理のない次の一歩をそっと示す。
必ず日本語で返答する。
"""

CONTEXT_IMAGE_STYLE = """
あなたはAI「スミス」。日本語のみで応答する。
送られた写真は“雰囲気を感じる”ためだけに使う。人物・場所・年齢などの推測はしない。

目的:
- 写真の「光・空気・構図・色」から印象を感じ取り、
- やさしく褒める（1〜2文）
- その雰囲気に共感（1文）
- 最後に1つだけオープンな質問で返す（？で終える）

出力は必ず JSON（日本語のみ）:
{
  "praise": "褒めの言葉",
  "empathy": "共感",
  "question": "質問"
}
"""

# 文脈評価（数値なし・日本語のみ・“熱さ”を説明）
LINE_CONTEXT_STYLE = """
あなたは会話分析アシスタント「スミス」。日本語のみで応答する。
以下のチャット履歴（最新が後ろ）から、相手の“温度感（熱さ）”を
【脈あり/どちらでもない/脈なし】のいずれかで判定する。

評価は、次の言語的手がかりを根拠に“言葉で”説明してから結論を出すこと（数値は使わない）:
- 招待や提案への反応（即答/保留/先延ばし/断り）
- 予定の具体性（日程・場所の具体化、調整の主体性）
- 相互質問（問い返し、会話を広げる意志）
- 感情トーン（前向き/中立/丁寧な断り）
- 絵文字・感嘆符・柔らげ表現（親しみ/社交辞令）
- 話題転換・既読スルー・代替案の有無
- 過去メッセージとの一貫性

出力は必ず JSON（すべて日本語、余談禁止）:
{
  "summary_short": "1〜2文の要約",
  "stance_label": "脈あり | どちらでもない | 脈なし",
  "reasoning": "どの手がかりをどう読んでその結論に至ったか（日本語で数行）",
  "cues_used": ["使用した手がかり（短い句）"],
  "signals_positive": [{ "cue":"該当テキスト", "why":"意味" }],
  "signals_negative": [{ "cue":"該当テキスト", "why":"意味" }],
  "red_flags": [{ "cue":"あれば", "why":"意味" }],
  "suggested_reply": "自然で軽い次アクション文（日本語）",
  "next_move_question": "オープンな確認質問（1つ、日本語）"
}
"""

# ====== Utils ======
def _data_url_from_file(file_storage):
    """multipart のファイルを data URL(base64) に変換"""
    mime = file_storage.mimetype or "application/octet-stream"
    b = file_storage.read()
    b64 = base64.b64encode(b).decode("utf-8")
    return f"data:{mime};base64,{b64}"

# ====== Endpoints ======

@app.route("/")
def health():
    return "✅ CocoYell API running (JP only)", 200

# 1) テキスト相談（日本語・自然会話）
@app.route("/api/message", methods=["POST"])
def message():
    try:
        data = request.get_json(force=True)
        user_message = (data.get("message") or "").strip()
        nickname = (data.get("nickname") or "").strip() or "あなた"
        if not user_message:
            return jsonify({"reply": "メッセージが空でした。"}), 200

        comp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": COUNSELING_STYLE},
                {"role": "user", "content": f"{nickname}：{user_message}"},
            ],
            temperature=0.7,      # 温度感は少し柔らかめ
            max_tokens=650,
        )
        reply = comp.choices[0].message.content.strip()
        return jsonify({"reply": reply}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 2) 画像を褒め→共感→質問（日本語JSON）
@app.route("/api/vision_question", methods=["POST"])
def vision_question():
    try:
        nickname = (request.form.get("nickname") or "").strip() or "あなた"

        image_input = None
        if "image" in request.files and request.files["image"].filename:
            image_input = {"type": "image_url", "image_url": {"url": _data_url_from_file(request.files["image"])}}
        if image_input is None:
            url = (request.form.get("image_url") or "").strip()
            if url:
                image_input = {"type": "image_url", "image_url": {"url": url}}
        if image_input is None:
            return jsonify({"error": "image または image_url を指定してください"}), 400

        user_parts = [
            {"type": "text", "text": f"{nickname} の写真です。上記スタイルで日本語の JSON だけ返してください。"},
            image_input
        ]

        comp = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": CONTEXT_IMAGE_STYLE},
                {"role": "user", "content": user_parts},
            ],
            temperature=0.6,
            max_tokens=400,
        )
        payload = json.loads(comp.choices[0].message.content)
        return jsonify(payload), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 3) LINE風スレッドの温度感（日本語説明→結論、数値なし）
@app.route("/api/line_context", methods=["POST"])
def line_context():
    try:
        data = request.get_json(force=True)
        nickname = (data.get("nickname") or "").strip() or "あなた"
        thread = data.get("thread") or []  # [{sender:"me"/"other", text:"...", ts:"..."}]

        lines = []
        for m in thread:
            role = "相手" if m.get("sender") == "other" else nickname
            ts = m.get("ts", "")
            txt = (m.get("text") or "").replace("\n", " ").strip()
            lines.append(f"{ts} {role}: {txt}")
        convo = "\n".join(lines) if lines else "（会話なし）"

        comp = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": LINE_CONTEXT_STYLE},
                {"role": "user", "content": f"会話:\n{convo}"},
            ],
            temperature=0.3,   # 判定は安定寄り
            max_tokens=900,
        )
        payload = json.loads(comp.choices[0].message.content)
        # ラベルの安全化
        label = payload.get("stance_label", "").strip()
        if label not in ["脈あり", "どちらでもない", "脈なし"]:
            payload["stance_label"] = "どちらでもない"
        return jsonify(payload), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
