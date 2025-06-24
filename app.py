from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # CORS許可（Flutterなど外部からアクセスできるように）

@app.route('/')
def index():
    return 'Hello from Flask!'

@app.route('/api/message', methods=['POST'])
def message():
    try:
        data = request.get_json()
        user_message = data.get('message', '')

        # ここでAIなどに渡して処理するのも可（とりあえず仮の返信）
        reply = f"受け取ったメッセージ：『{user_message}』だね！こちらからの返信だよ〜"

        return jsonify({'reply': reply})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
