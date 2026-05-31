# AI Stock Analysis Dashboard

A sophisticated, institutional-grade stock analysis platform powered by Google's Gemini AI. This dashboard provides deep multi-timeframe market analysis, technical indicators, volume analysis, sentiment analysis, and risk assessment for stocks traded on NSE and BSE.

## 🎯 Features

### Core Capabilities
- **Institutional-Grade Analysis**: Multi-timeframe market analysis using hedge fund and quantitative trading methodologies
- **AI-Powered Insights**: Leverages Google's Gemini AI for deep market analysis
- **Real-Time Data**: Fetches live financial data from Yahoo Finance and market news
- **Technical Indicators**: EMA 9, EMA 20, RSI, MACD, Bollinger Bands, VWAP analysis
- **Smart Money Analysis**: Detects institutional accumulation/distribution patterns
- **Sentiment Analysis**: Integrates market sentiment from financial news

### Analysis Components
1. **Price Structure Analysis**
   - Trend detection and strength analysis
   - Supply/demand zone identification
   - Consolidation pattern recognition
   - Breakout and reversal detection

2. **Multi-Timeframe Analysis**
   - 1-minute intraday data
   - Hourly data
   - Daily data
   - Trend alignment across timeframes

3. **Volume & Momentum**
   - Unusual volume detection
   - Buying/selling pressure analysis
   - Breakout confirmation
   - Smart money participation detection

4. **Risk Analysis**
   - Volatility risk assessment
   - Reversal and trap probability
   - News risk evaluation
   - Overall trade quality scoring

5. **Trade Decision Engine**
   - High-probability setup identification
   - BUY/SELL/HOLD signals
   - Risk-reward analysis

### Frontend Features
- **Modern UI**: Glassmorphism design with neon accents
- **3D Background**: Interactive Three.js animated background
- **Real-time Visualization**: Stock charts and analysis display
- **Responsive Design**: Built with Tailwind CSS
- **Smooth Animations**: GSAP-powered animations

## 🏗️ Project Structure

```
.
├── app.py                  # Flask application entry point
├── app.spec               # PyInstaller configuration for executable build
├── GEMINI.md              # AI system prompt and analysis framework
├── requirements.txt       # Python dependencies
├── services/
│   ├── ai_service.py      # Google Gemini AI integration & data fetching
│   └── indicators.py      # Technical indicators calculations
├── static/
│   ├── assets/            # Static assets
│   ├── css/
│   │   └── style.css      # Custom styling
│   ├── gsap/              # GSAP animations
│   ├── js/
│   │   ├── animations.js  # UI animations
│   │   ├── dashboard.js   # Dashboard logic
│   │   └── three-bg.js    # Three.js background
│   └── three/             # Three.js models
├── templates/
│   └── index.html         # Main dashboard UI
└── README.md              # This file
```

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Google Gemini API key
- MarketAux API key (for news data)

### Installation

1. **Clone the repository**
   ```bash
   cd d:\Work\STOCK
   ```

2. **Create virtual environment** (recommended)
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   Create a `.env` file in the root directory:
   ```env
   GOOGLE_API_KEY=your_gemini_api_key_here
   NEWS_API_TOKEN=your_marketaux_api_token_here
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

   The application will start on `http://localhost:5000`

## 📋 API Endpoints

### GET `/`
Returns the main dashboard HTML interface.

**Response**: HTML dashboard page

---

### POST `/analyze`
Analyzes a stock symbol using the AI service.

**Request Body**:
```json
{
  "stock": "SYMBOL"
}
```

**Parameters**:
- `stock` (string, required): Stock ticker symbol (e.g., "AAPL", "RELIANCE", "TCS")

**Response**:
```json
{
  "analysis": "Detailed institutional-grade trading analysis..."
}
```

**Example**:
```bash
curl -X POST http://localhost:5000/analyze \
  -H "Content-Type: application/json" \
  -d '{"stock":"RELIANCE"}'
```

## 🔧 Technical Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | Flask (Python web framework) |
| **AI/ML** | Google Genai (Gemini API) |
| **Data Source** | Yahoo Finance API, MarketAux News API |
| **Frontend** | HTML5, Tailwind CSS, JavaScript |
| **Visualization** | Three.js (3D), Lightweight Charts, GSAP |
| **Data Processing** | Pandas, Requests |

## 📊 Data Sources

### Financial Data
- **Yahoo Finance v8 API**
  - 1-day intraday (1-minute intervals)
  - 8-day intraday (1-minute intervals)
  - 1-month historical (1-hour intervals)

### News & Sentiment
- **MarketAux News API**
  - Real-time market news
  - Entity filtering
  - Sentiment analysis

## 🧠 AI Analysis Framework

The AI uses institutional-grade methodology covering:

- **Price Action**: Higher highs/lows, consolidation, breakouts, liquidity traps
- **Technical Analysis**: Moving averages, RSI, MACD, Bollinger Bands, VWAP
- **Volume Analysis**: Institutional accumulation/distribution, breakout confirmation
- **Multi-Timeframe**: Short-term, medium-term, and swing structure alignment
- **Sentiment**: News-based market sentiment and divergence detection
- **Risk Assessment**: Volatility, reversal, trap, and gap continuation risks

The system generates **high-probability trading setups** with BUY, SELL, or HOLD signals based on:
- Setup quality
- Probability of success
- Risk-reward assessment
- Institutional behavior patterns

## 🛠️ Building Executable

To build a standalone executable using PyInstaller:

```bash
pyinstaller app.spec
```

The executable will be created in the `dist/` directory.

## 📝 Environment Variables

Required environment variables (set in `.env`):

```env
GOOGLE_API_KEY=your_google_gemini_api_key
NEWS_API_TOKEN=your_marketaux_news_api_token
FLASK_ENV=development
DEBUG=True
```

## ⚠️ Important Notes

- **Data Fetching**: All market data is fetched server-side; nothing is fetched directly from client browsers
- **Rate Limiting**: Implement request throttling to respect API rate limits
- **API Keys**: Never commit `.env` files with real API keys to version control
- **Error Handling**: The service includes retry logic with exponential backoff for network requests

## 🔒 Security Considerations

- Store API keys securely in environment variables
- Use HTTPS in production
- Implement rate limiting on endpoints
- Validate all user inputs (stock symbols)
- Consider CORS restrictions for production deployment

## 🐛 Troubleshooting

### Connection Errors to Yahoo Finance
- Check internet connection
- Yahoo Finance may rate limit - the code includes retry logic with exponential backoff
- Verify User-Agent headers are properly set

### Gemini API Errors
- Verify `GOOGLE_API_KEY` is correctly set in `.env`
- Check API quota and billing status
- Ensure the API is enabled in Google Cloud Console

### Port Already in Use
- Change the port in `app.py`: `app.run(debug=True, port=5001)`
- Or kill the process using port 5000

## 📈 Future Enhancements

- [ ] Portfolio tracking
- [ ] Alert system for price/signal changes
- [ ] Historical analysis comparison
- [ ] Custom indicator support
- [ ] Export reports functionality
- [ ] User authentication & preferences
- [ ] Database integration for analysis history

## 📄 License

[Add your license here]

## 👨‍💻 Contributing

[Add contribution guidelines here]

## 📧 Support

For issues, questions, or suggestions, please [add contact information here].

---

**Disclaimer**: This tool is for educational and analytical purposes only. Trading involves risk. Always conduct your own research and consult with financial advisors before making investment decisions.
