from flask import Flask, request, jsonify
import openai
import os

app = Flask(__name__)

# APIキーを環境変数から取得
openai.api_key = os.environ.get("OPENAI_API_KEY")

@app.route("/api/message", methods=["POST"])
def message():
    user_input = request.json.get("message", "")

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # または "gpt-4o"
            messages=[
                {"role": "system", "content": "You are a kind assistant who responds in the same language as the user."},
                {"role": "user", "content": user_input}
            ],
            temperature=0.7,
        )
        reply = response["choices"][0]["message"]["content"]
        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
