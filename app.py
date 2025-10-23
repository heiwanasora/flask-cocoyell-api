@app.route("/api/message", methods=["POST"])
def api_message():
    try:
        data = request.get_json(force=True) or {}
        text = (data.get("text") or data.get("message") or "").strip()
        if not text:
            return jsonify({"reply": "（エラー）入力が空です。", "score": 50, "hearts": "❤️❤️🤍🤍🤍"}), 400

        out = call_model(text)

        # --- 表示部分（1回のみ） ---
        reply_text = (
            f"心理の要約: {out['intent']}\n"
            f"理由:\n" + "\n".join([f"・{r}" for r in out['reasons']]) + "\n\n"
            f"スミスの解析: {out['analysis']}\n"
            f"ステータス: {out['status']}（文脈: {SMITH_CONTEXT}）\n"
            f"{hearts(out['score'])}   SCORE: {out['score']}\n"
            f"アドバイス: {out['advice']}\n"
            f"例文: {out['example']}"
        )

        # --- Flutter側に返すJSON（重複防止） ---
        return jsonify({
            "reply": reply_text,
            "score": out["score"],
            "status": out["status"],
            "hearts": hearts(out["score"]),
            "advice": out["advice"],
            "example": out["example"],
        })

    except Exception as e:
        return jsonify({
            "reply": f"（サーバ例外）{e}",
            "score": 50,
            "hearts": "❤️❤️🤍🤍🤍",
            "advice": "もう一度お試しください。"
        }), 200
