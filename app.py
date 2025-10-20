# app.py
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ====== 通常メッセ（必要なら残す） ==========================================
BASE_TONE = """
あなたは「スミス」。穏やかでフレンドリーな日本語話者。
比喩は控えめ、落ち着いて短く要点を返す。英語/絵文字は基本使わない。
"""
@app.route("/api/message", methods=["POST"])
def message():
    data = request.get_json(force=True)
    nickname = (data.get("nickname") or "あなた").strip()
    text = (data.get("message") or "").strip()
    msg = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.7,
        messages=[
            {"role": "system", "content": BASE_TONE},
            {"role": "user", "content": f"{nickname}からの相談: {text}"}
        ],
        max_tokens=500,
    )
    return jsonify({"reply": msg.choices[0].message.content.strip()}), 200

# ====== LINE文脈／友達トーンで“文章のみ”を返す ==============================
LINE_CONTEXT_STYLE = """
あなたは「スミス」。日本語だけで話す、親しい友達のような相談相手。

【目的】
LINEのやり取りを読み、会話の温度感と距離感を感じ取り、
友達に話すように「脈あり / 様子見 / 脈なし」の印象を自然文で伝える。

【出力形式（厳守）】
・JSON、箇条書き、英語、コードブロックは一切出さない。
・日本語の文章だけで、テンポよく短く。
・構成はこの順番で、見出しの記号や番号は使わない：

1行目：判定をひとこと（例：脈あり寄り。／様子見。／脈薄め。）
続けて：そう感じた理由（語尾は柔らかく。絵文字は使っても1つまで）
必要なら：様子見ポイントを一言だけ添える
最後に：いま出せるベストな返し例を1〜2個、引用記号（> ）で書く
（例）
脈あり寄り。
「楽しかった」が自然に出ていて、次の予定の話も自分からしている。距離感は近め。
ただ「予定みて」は前向きな保留だから、押し急がないのが安心。
> 来週の平日夜と週末ランチならどっちが合いそう？
> 和食かイタリアンで迷ってる。気分どっち寄り？

【判断の観点】
・肯定的な感想、絵文字、柔らかい語尾、次アクションの示唆はプラス。
・形式的・短文・話題が広がらない・先延ばしだけはマイナス。
"""

@app.route("/api/line_context", methods=["POST"])
def line_context():
    data = request.get_json(force=True)
    nickname = (data.get("nickname") or "あなた").strip()
    thread = data.get("thread") or []

    # me/other の簡易ログ化
    convo = "\n".join([
        f'{m.get("sender","me")}: {(m.get("text") or "").strip()}'
        for m in thread
    ])

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.9,
        messages=[
            {"role": "system", "content": LINE_CONTEXT_STYLE},
            {"role": "user", "content": f"{nickname}との会話ログ:\n{convo}\n\n上のルールで返答してください。"}
        ],
        max_tokens=700
    )
    text = res.choices[0].message.content.strip()
    # 念のため：もしJSON風が混ざったらテキストだけに落とす
    if text.startswith("{") or text.startswith("["):
        text = "様子見。\n形式的で読みにくい返しになっていたから、自然文で出直すね。\n> 来週の平日夜か週末ランチならどっちが合いそう？"
    return jsonify({"reply": text}), 200

@app.route("/")
def home():
    return "✅ Smith LINE Analyzer (friend-tone / JP only)", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
