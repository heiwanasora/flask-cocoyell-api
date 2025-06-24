from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/api/message", methods=["POST"])
def message():
    data = request.get_json()
    user_input = data.get("message", "")
    return jsonify({"reply": f"スミスが言った：{user_input}"})

if __name__ == "__main__":
    app.run()
