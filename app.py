# app.py
import os
import json
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
app = Flask(__name__)
CORS(app)

# ====== スミス基本設定 ======
COUNSELING_STYLE = """
あなたは「スミス」。日本語で話す、落ち着いた性格のAIカウンセラーです。
話し方は友達のように自然で、ちょっと優しい相づちを入れる。
難しい言葉や英語は使わず、素直な日本語で。
相手の気持ちの温度や、言葉の裏の雰囲気を感じ取りながら話します。
"""

# ====== 文脈解析スタイル（友達トーン・推測） ======
LINE_CONTEXT_STYLE = """
あなたは「スミス」。
親しい友達の恋愛相談を聞くような気持ちで、以下のLINEのやりとりを読んでね。
分析っぽくせず、自然な日本語で、あくまで“感じ取った印象”を伝える。

【やること】
1. 会話の流れをざっくりまとめる。
2. 相手のテンションや返し方、絵文字、距離感などから
   「脈あり」「様子見」「脈なし」のどれに近いかを推測する。
3. その理由を“友達に話すように”説明する。
   （例：「この返し方は悪くないけど、ちょっと温度は低めかな〜」など）
4. 最後に一言だけ、相談相手へのアドバイスで締める。
   （例：「もう少し様子見でもいいかもね」「焦らなくていいよ」など）

【口調】
・完全に日本語。英語・専門用語は使わない。
・気さくな友達トーン。
・「〜かも」「〜じゃない？」のような柔らかい推測で話す。
・一文ごとに息づかいのあるテンポ感。

【出力形式】
JSON 形式で以下を返す:
{
  "summary": "会話の流れを1〜2文でまとめる",
  "feeling": "スミスの感じた温度感（素直に）",
  "prediction": "脈あり | 様子見 | 脈なし",
  "reason": "そう思った理由を友達トーンで説明（数文）",
  "advice": "相手への一言アドバイス（優しく）"
}
"""

# ====== 画像共有用（参考） ======
CONTEXT_IMAGE_STYLE = """
あなたは「スミス」。
送られた写真の雰囲気を感じ取り、やさしく褒め、共感し、最後に軽い質問をする。
すべて日本語で、短く自然に。
{
  "praise": "褒めの言葉",
  "empathy": "共感",
  "question": "質問"
}
"""

def _data_url_from_file(file_storage):
    mime = file_storage.mimetype or "application/octet-stream"
    b = file_storage.read()
    b64 = base64.b64encode(b).decode("utf-8")
    return f"data:{mime};base64,{b64}"

@app.route("/")
def home():
    return "✅ Smith JP API (friend mode) running", 200

# ====== 通常メッセージ ======
@app.route("/api/message", methods=["POST"])
def message():
    try:
        data = request.get_json(force=True)
        text = (data.get("message") or "").strip()
        name = (data.get("nickname") or "").strip() or "あなた"
        if not text:
            return jsonify({"reply": "メッセージが空でした。"}), 200

        comp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": COUNSELING_STYLE},
                {"role": "user", "content": f"{name}：{text}"}
            ],
            temperature=0.8,
            max_tokens=600
        )
        return jsonify({"reply": comp.choices[0].message.content.strip()}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ====== 文脈分析（友達トーン・推測型） ======
@app.route("/api/line_context", methods=["POST"])
def line_context():
    try:
        data = request.get_json(force=True)
        nickname = (data.get("nickname") or "").strip() or "あなた"
        thread = data.get("thread") or []

        convo = "\n".join([
            f'{m.get("sender","me")}: {(m.get("text") or "").strip()}'
            for m in thread
        ]) or "（会話なし）"

        comp = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": LINE_CONTEXT_STYLE},
                {"role": "user", "content": convo}
            ],
            temperature=0.8,
            max_tokens=900
        )

        payload = json.loads(comp.choices[0].message.content)
        if payload.get("prediction") not in ["脈あり", "様子見", "脈なし"]:
            payload["prediction"] = "様子見"
        return jsonify(payload), 200
    except Excep
