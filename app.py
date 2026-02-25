from flask import Flask, render_template, request, jsonify
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_curriculum():
    # Placeholder for AI logic
    data = request.json
    return jsonify({"status": "success", "message": "Curriculum generation initiated"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
