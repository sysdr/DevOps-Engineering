from flask import Flask, jsonify
import os
import time

app = Flask(__name__)

start_time = time.time()

@app.route('/')
def home():
    return jsonify({
        'message': 'Hello from WebApp Operator Demo!',
        'version': '1.0.0',
        'uptime': f"{time.time() - start_time:.1f} seconds",
        'pod': os.environ.get('HOSTNAME', 'unknown')
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'timestamp': time.time()})

@app.route('/ready')
def ready():
    return jsonify({'status': 'ready', 'timestamp': time.time()})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
