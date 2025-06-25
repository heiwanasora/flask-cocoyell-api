from flask import Flask, request, jsonify
from openai import OpenAI

import os

app = Flask(__name__)

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

@app.route("/api/message", methods=["POST"])
def message():
    user_input = request.json.get("message", "")

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # ここは任意で "gpt-4o" でもOK
        messages=[
            {"role": "system", "content": "You are a kind assistant who responds in the same language as the user."},
            {"role": "user", "content": user_input}
        ],
        temperature=0.7,
    )

    reply = response.choices[0].message.content
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(debug=True)
