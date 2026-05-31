from flask import Flask, render_template, request, jsonify
from services.ai_service import AIService
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

ai_service = AIService()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    symbol = data.get('stock')

    if not symbol:
        return jsonify({"error": "Stock symbol is required"}), 400

    # Gemini fetches all data URLs server-side via URL Context tool.
    # Nothing is fetched on this machine.
    result = ai_service.generate_analysis(symbol)
    return jsonify({"analysis": result})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
