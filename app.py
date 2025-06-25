from flask import Flask, request, jsonify
from openai import OpenAI
import os

app = Flask(__name__)

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

@app.route("/api/message", methods=["POST"])
def message():
    user_input = request.json.get("message", "")

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # または "gpt-4o"
        messages=[
            {"role": "system", "content": "You are a kind assistant who replies in the user's language."},
            {"role": "user", "content": user_input}
        ],
        temperature=0.7,
    )

    return jsonify({"reply": response.choices[0].message.content})

if __name__ == "__main__":
    app.run(debug=True)
