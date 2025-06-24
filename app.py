from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return 'Flaskサーバー稼働中'

@app.route('/api/message', methods=['POST'])
def message():
    data = request.get_json()
    user_message = data.get('message', '')
    return jsonify({'reply': f'受け取りました: 「{user_message}」'})

if __name__ == '__main__':
    app.run()
