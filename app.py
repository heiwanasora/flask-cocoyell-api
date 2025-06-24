from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # クロスオリジン対応

@app.route('/')
def home():
    return 'Flaskサーバーは正常に稼働中です ✅'

@app.route('/api/message', methods=['POST'])
def message():
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'メッセージが見つかりません'}), 400
    
    user_message = data['message']
    reply = f"受け取りました: 「{user_message}」"
    return jsonify({'reply': reply})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
