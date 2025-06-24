from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # ← CORS全許可

@app.route("/")
def home():
    return "Hello from Flask!"

@app.route("/api/message", methods=["POST"])
def message():
    try:
        data = request.get_json()
        user_input = data.get("message", "")
        return jsonify({"reply": f"スミスが言った：{user_input}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run()
