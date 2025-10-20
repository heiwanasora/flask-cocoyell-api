# app.py
import os
import json
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

# ====== OpenAI Client ======
# Render 等で proxies 周りの相性が出ないようにシンプル初期化
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

app = Flask(__name__)
CORS(app)

# ====== スタイル定義 ======
COUNSELING_STYLE = """
あなたは「スミス」。心を整理するAIカウンセラーです。
- 落ち着いたトーンで、やさしく簡潔に導く。
- 相手の名前を適度に呼びかける（呼びすぎない）。
- 例え話は1つまで。過度に踏み込みすぎない。
- 3〜6文を目安に、読みやすい段落で。
- 最後に勧誘や断定はしない。
"""

CONTEXT_IMAGE_STYLE = """
あなたはAI「スミス」。
送られた写真は“雰囲気を感じる”ためだけに使います。
人物・場所・年齢などの推測はしません。

目的:
- 写真の「光・空気・構図・色」などから印象を感じ取り、
- 優しく褒める（1〜2文）
- その雰囲気に共感する（1文）
- そして最後に1つだけオープンな質問で返す（？で終える）

出力は必ず次の JSON 形式:
{
  "praise": "褒めの言葉",
  "empathy": "共感",
  "question": "質問"
}
"""

LINE_CONTEXT_STYLE = """
あなたは会話分析アシスタント「スミス」。
以下のチャット履歴（最新が後ろ）から、相手の関心・温度感・感情を推定する。
推測は控えめに、テキストに現れたシグナルのみを根拠として評価する。

出力は必ず JSON。余談・説明文は出さない。

評価規則:
- interest_score: 0〜100（相手が"次の約束に前向き"である度合い）
- stance_label: one of ["leaning_yes","neutral","leaning_no"]
  - しきい値: interest_score>=70 => leaning_yes, <=40 => leaning_no, それ以外 neutral
- emotions: { "joy":0-1, "calm":0-1, "surprise":0-1, "anger":0-1, "sad":0-1 }
  - 根拠がない感情は0
- signals_positive / signals_negative:
  - 形式: [{ "cue":"テキスト断片", "why":"それが示す意味"}]
- red_flags: 会話継続に消極的な兆候（なければ[]）
- summary_short: 1〜2文で状況要約（主観控えめ）
- suggested_reply: 1通だけ、自然で軽い次アクション
- next_move_question: 1問だけ、オープンな確認質問
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
    return "✅ CocoYell API running (OpenAI SDK 1.x)", 200

# 1) テキスト相談
@app.route("/api/message", methods=["POST"])
def message():
    try:
        data = request.get_json(force=True)
        user_message = (data.get("message") or "").strip()
        nickname = (data.get("nickname") or "").strip() or "あなた"
        if not user_message:
            return jsonify({"reply": "メッセージが空でした。"}), 200

        messages = [
            {"role": "system", "content": COUNSELING_STYLE},
            {"role": "user", "content": f"{nickname}：{user_message}"},
        ]

        comp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=600,
        )
        reply = comp.choices[0].message.content.strip()
        return jsonify({"reply": reply}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 2) 画像（風景/物）を褒めつつ共感→質問（JSONで）
@app.route("/api/vision_question", methods=["POST"])
def vision_question():
    try:
        nickname = (request.form.get("nickname") or "").strip() or "あなた"

        image_input = None
        # a) ファイルアップロード（優先）
        if "image" in request.files and request.files["image"].filename:
            image_input = {"type": "image_url", "image_url": {"url": _data_url_from_file(request.files["image"])}}
        # b) URL 文字列
        if image_input is None:
            url = (request.form.get("image_url") or "").strip()
            if url:
                image_input = {"type": "image_url", "image_url": {"url": url}}

        if image_input is None:
            return jsonify({"error": "image または image_url を指定してください"}), 400

        user_parts = [
            {"type": "text", "text": f"{nickname} の写真です。上記スタイルで JSON だけ返して。"},
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

# 3) LINE 風のスレッドを解析（脈あり度と根拠を明確に）
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
            temperature=0.3,
            max_tokens=700,
        )
        payload = json.loads(comp.choices[0].message.content)
        # stance_label を interest_score から自動整形（安全側）
        score = int(round(float(payload.get("interest_score", 0))))
        if score >= 70:
            label = "leaning_yes"
        elif score <= 40:
            label = "leaning_no"
        else:
            label = "neutral"
        payload["interest_score"] = score
        payload["stance_label"] = payload.get("stance_label", label)

        return jsonify(payload), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
