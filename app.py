# app.py
import os
import re
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
CORS(app)

app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_MIMETYPE'] = 'application/json; charset=utf-8'

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- 改良済みプロンプト（文脈整合＋自然な例文生成） ---
LINE_CONTEXT_STYLE = """
あなたは「スミス」。日本語で話す、親しい友達のような恋愛相談相手。

【目的】
ユーザーの発言から、感情・意図・脈の傾向を分析し、
その理由と「自然で文脈に合った」返し方を提示する。

【出力フォーマット（厳守）】
1行目：ひとことで印象や判断（自然文）
REASONS:
- 判断理由を2〜3個（各40字以内）
- できるだけユーザー発言の引用を入れる（「…」）
SCORE: 0〜100（100 = 強い好意）
COMMENT: 状況を一文でまとめる
アドバイス: 次に送ると良い返しを1行（絵文字は1つまで）
EXAMPLE: 実際に送ると良い「例文」を1行
  - 質問形でも断定形でもよい
  - ただし文脈と理由に整合すること（矛盾NG）
  - 新しい情報や誘い（デート提案など）は、文脈に示唆がある場合のみ
  - 自然で親しみやすい日本語。口調を急に変えない
  - 40字以内を目安に簡潔に

【禁止】
JSON、英語、コードブロック、見出しタイトル。
自然な日本語文のみ。
"""

# --- OpenAI呼び出し関数 ---
def generate_reply(user_input: str):
    system_prompt = LINE_CONTEXT_STYLE
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input},
    ]

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.8,
    )

    content = completion.choices[0].message.content.strip()
    return parse_response(content)


# --- 出力整形 ---
def parse_response(text: str):
    reply_match = re.search(r"^(.*?)\n?REASONS:", text, re.S)
    reasons_block = re.search(r"REASONS:\s*(.*?)\nSCORE:", text, re.S)
    score_match = re.search(r"SCORE:\s*(\d+)", text)
    comment_match = re.search(r"COMMENT:\s*(.*?)\n", text)
    advice_match = re.search(r"アドバイス:\s*(.*?)\n", text)
    example_match = re.search(r"EXAMPLE:\s*(.*)", text)

    reply = reply_match.group(1).strip() if reply_match else text
    reasons_raw = reasons_block.group(1).strip() if reasons_block else ""
    score = int(score_match.group(1)) if score_match else 50
    comment = comment_match.group(1).strip() if comment_match else ""
    advice = advice_match.group(1).strip() if advice_match else ""
    example = example_match.group(1).strip() if example_match else ""

    # --- 軽い整形・辻褄合わせ ---
    reasons = re.findall(r"(?:-|\d+\.?)\s*(.+)", reasons_raw)
    example = re.sub(r"^\s*例えば[、,:]\s*", "", example)
    example = re.sub(r"[。、]{2,}$", "。", example)

    # 文脈に不自然な誘い系を防ぐ（例：唐突な「旅行しよう」など）
    if re.search(r"(突然会おう|明日デート|結婚|同棲|泊ま|旅行|キスしよう)", example):
        example = "もう少し相手の気持ちを探るように聞いてみよう。"

    if len(example) > 45:
        example = example[:45].rstrip("、。！？!?") + "。"

    hearts = "❤️" * int(score / 20) + "🤍" * (5 - int(score / 20))

    return {
        "reply": f"{reply}\n\n理由:\n" + "\n".join([f"・{r}" for r in reasons]) + f"\n\n{hearts}   SCORE: {score}\nアドバイス: {advice}\n例文: {example}",
        "score": score,
        "hearts": hearts,
        "advice": advice,
        "example": example,
    }


# --- Flaskルート ---
@app.route("/api/message", methods=["POST"])
def api_message():
    data = request.get_json()
    user_input = data.get("text", "").strip()
    if not user_input:
        return jsonify({"error": "no text"}), 400
    result = generate_reply(user_input)
    return jsonify(result)


@app.route("/", methods=["GET"])
def health():
    return make_response(jsonify({"status": "ok"}), 200)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
