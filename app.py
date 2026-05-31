from flask import Flask, render_template, request, jsonify
from services.ai_service import AIService
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

ai_service = AIService()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        symbol = data.get('stock')

        if not symbol:
            return jsonify({"error": "Stock symbol is required"}), 400

        result = ai_service.generate_analysis(symbol)

        return jsonify({
            "success": True,
            "analysis": result
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Page not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )