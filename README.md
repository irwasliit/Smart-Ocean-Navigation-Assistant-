# 🌊 Enhanced Smart Ocean Navigation Assistant

An advanced marine weather application powered by **Multi-Agent AI** with **NLP**, **Information Retrieval**, and **Real-time Maritime Data Processing**.

## 🚀 Key Features

### 🤖 Multi-Agent AI System
- **Weather Analyst Agent**: Real-time marine weather analysis and forecasting
- **Route Optimizer Agent**: AI-powered navigation route optimization
- **Hazard Detector Agent**: Intelligent maritime hazard identification
- **Information Retriever Agent**: NLP-powered maritime content processing
- **Communication Manager Agent**: Smart user interaction coordination

### 🧠 Advanced NLP & IR Capabilities
- **Natural Language Processing**: NLTK, spaCy, and TextBlob integration
- **Maritime Content Analysis**: Specialized processing for marine bulletins
- **Multi-Source Data Integration**: RSS feeds, government maritime sources
- **Intelligent Document Processing**: Automatic content categorization
- **Real-time Information Retrieval**: Live maritime data aggregation

### 🌐 Enhanced User Interface
- **Marine-Themed Design**: Professional maritime color scheme
- **Real-time Agent Status**: Live monitoring of AI agent availability
- **Confidence Scoring**: AI response reliability indicators
- **Interactive Maps**: Leaflet-powered weather and route visualization
- **Responsive Design**: Optimized for desktop and mobile devices

### 📡 Advanced Data Sources
- **OpenWeatherMap API**: Real-time weather data
- **Maritime Bulletins**: Government maritime safety notices
- **RSS Feeds**: Live maritime news and updates
- **Geographic APIs**: Location-based services
- **Route Analysis**: Intelligent navigation planning

## 🛠️ Technical Architecture

### Backend (FastAPI + Python)
```
backend/
├── main.py                     # Application entry point with enhanced AI routing
├── services/
│   ├── multi_agent_ai_service.py    # Core multi-agent AI system
│   ├── enhanced_ir_service.py       # NLP-powered information retrieval
│   ├── weather_service.py           # Weather data processing
│   ├── route_service.py             # Route optimization
│   └── alert_service.py             # Alert management
├── routers/
│   ├── enhanced_ai.py               # Enhanced AI endpoints
│   ├── weather.py                   # Weather API routes
│   └── auth.py                      # Authentication
└── models.py                        # Database models
```

### Frontend (React + Tailwind CSS)
```
frontend/src/
├── pages/
│   ├── AIChat.jsx              # Enhanced multi-agent chat interface
│   ├── Dashboard.jsx           # Main dashboard with AI insights
│   ├── WeatherMap.jsx          # Interactive weather mapping
│   └── RouteAnalysis.jsx       # AI-powered route analysis
├── components/
│   ├── Navbar.jsx              # Navigation with AI status
│   └── LoadingSpinner.jsx      # Enhanced loading states
└── contexts/
    └── AuthContext.jsx         # Authentication management
```
   ```

## 🔧 Installation & Setup

### Prerequisites
- **Python 3.10+**
- **Node.js 18+**
- **MySQL 8.0+**
- **OpenAI API Key** (for enhanced AI features)

### Backend Setup

1. **Clone and navigate to the project:**
```bash
git clone <repository-url>
cd ir
```

2. **Create virtual environment:**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # Linux/Mac
```

3. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

4. **Download NLP models:**
```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('vader_lexicon')"
python -m spacy download en_core_web_sm
```

5. **Setup environment variables:**
```bash
cp env.example .env
# Edit .env with your API keys and database credentials
```

6. **Initialize database:**
```bash
python backend/setup_database.py
```

7. **Start backend server:**
```bash
python start_backend.py
```

### Frontend Setup

1. **Navigate to frontend directory:**
```bash
cd frontend
```

2. **Install Node.js dependencies:**
```bash
npm install
```

3. **Start development server:**
```bash
npm run dev
```

### Environment Variables (.env)
```env
# Database Configuration
DATABASE_URL=mysql+pymysql://username:password@localhost/marine_weather

# API Keys
OPENAI_API_KEY=your_openai_api_key
OPENWEATHER_API_KEY=your_openweather_api_key

# Security
SECRET_KEY=your_jwt_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# AI Configuration
MAX_TOKENS=1000
TEMPERATURE=0.7
MODEL_NAME=gpt-3.5-turbo
```

## 🚀 Usage

### Multi-Agent AI Chat
1. Navigate to **AI Assistant** page
2. View real-time agent status indicators
3. Ask questions like:
   - "Analyze current weather conditions for latitude 40.7128, longitude -74.0060"
   - "Optimize route from Miami to Nassau"
   - "Detect hazards along the Gulf Coast"
   - "Find latest maritime safety bulletins"

### Weather Analysis
- Real-time weather data visualization
- AI-powered weather pattern analysis
- Marine-specific weather insights
- Interactive weather mapping

### Route Optimization
- AI-enhanced route planning
- Weather-aware navigation suggestions
- Hazard avoidance recommendations
- Multi-factor route optimization

### Information Retrieval
- Natural language maritime queries
- Real-time bulletin processing
- Multi-source content aggregation
- Intelligent content summarization

## 🔧 API Endpoints

### Enhanced AI Endpoints
```
POST /api/ai/chat                    # Multi-agent chat interface
POST /api/ai/analyze-conditions      # Weather condition analysis
POST /api/ai/optimize-route         # Route optimization
POST /api/ai/detect-hazards         # Hazard detection
GET  /api/ai/status                 # System and agent status
```

### Weather Endpoints
```
GET  /api/weather/current/{lat}/{lon}    # Current weather data
GET  /api/weather/forecast/{lat}/{lon}   # Weather forecast
POST /api/weather/batch                  # Batch weather requests
```

### Route Endpoints
```
POST /api/routes/analyze             # Route analysis
POST /api/routes/optimize            # Route optimization
GET  /api/routes/history             # Route history
```

## 🧠 AI Agent Capabilities

### Weather Analyst Agent
- **Real-time Analysis**: Live weather data processing
- **Pattern Recognition**: Weather trend identification
- **Marine Focus**: Ocean-specific weather insights
- **Forecasting**: AI-enhanced weather predictions

### Route Optimizer Agent
- **Multi-factor Optimization**: Weather, distance, safety
- **Dynamic Routing**: Real-time route adjustments
- **Safety Integration**: Hazard-aware planning
- **Efficiency Focus**: Fuel and time optimization

### Hazard Detector Agent
- **Pattern Recognition**: Hazard identification from data
- **Safety Assessment**: Risk level evaluation
- **Alert Generation**: Automated warning systems
- **Predictive Analysis**: Future hazard prediction

### Information Retriever Agent
- **NLP Processing**: Natural language understanding
- **Content Aggregation**: Multi-source data collection
- **Document Analysis**: Maritime bulletin processing
- **Knowledge Extraction**: Key information identification

### Communication Manager Agent
- **Response Coordination**: Multi-agent response management
- **Context Awareness**: Conversation context maintenance
- **User Intent Recognition**: Query understanding
- **Response Optimization**: Best response selection

## 🎨 Enhanced UI Features

### Marine Theme Design
- **Ocean-inspired Colors**: Professional maritime palette
- **Responsive Layout**: Mobile-first design approach
- **Interactive Elements**: Smooth animations and transitions
- **Accessibility**: WCAG-compliant design

### Real-time Status Indicators
- **Agent Status**: Live agent availability monitoring
- **System Health**: Overall system status display
- **Confidence Scores**: AI response reliability indicators
- **Processing States**: Real-time operation feedback

### Enhanced Chat Interface
- **Multi-agent Responses**: Agent-specific message handling
- **Rich Formatting**: Enhanced message presentation
- **Conversation History**: Persistent chat storage
- **Quick Suggestions**: Contextual query suggestions

## 📦 Docker Deployment

### Build and run with Docker Compose:
```bash
docker-compose up --build
```

### Individual container builds:
```bash
# Backend
docker build -t marine-weather-backend ./backend

# Frontend
docker build -t marine-weather-frontend ./frontend
```

## 🔍 Testing

### Backend Tests
```bash
cd backend
python -m pytest tests/
```

### API Testing
```bash
python test_apis.py
python test_fixed_apis.py
python test_email_notifications.py
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 🚀 Production Deployment

### Environment Setup
1. **Database**: MySQL 8.0+ with proper indexing
2. **Web Server**: Nginx with SSL configuration
3. **Application**: Gunicorn for Python, PM2 for Node.js
4. **Monitoring**: Implement logging and monitoring
5. **Security**: Proper API key management and CORS setup

### Performance Optimization
- **Caching**: Redis for session and response caching
- **CDN**: Static asset delivery optimization
- **Database**: Query optimization and indexing
- **AI**: Response caching for common queries

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/enhancement`)
3. Commit changes (`git commit -am 'Add new feature'`)
4. Push to branch (`git push origin feature/enhancement`)
5. Create Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- **Documentation**: Check inline code documentation
- **Issues**: Create GitHub issues for bugs
- **Features**: Submit feature requests via GitHub
- **Community**: Join our discussion forums

## 🎯 Roadmap

### Upcoming Features
- **Machine Learning Models**: Custom weather prediction models
- **Advanced Visualization**: 3D weather and route modeling
- **Mobile App**: Native mobile application
- **Offline Capabilities**: Offline weather data and routing
- **Integration APIs**: Third-party marine software integration

### Performance Enhancements
- **Real-time Updates**: WebSocket-based live updates
- **Advanced Caching**: Intelligent data caching strategies
- **Scalability**: Microservices architecture migration
- **AI Optimization**: Custom-trained maritime AI models

---

**Built with ❤️ for the maritime community**

*Enhancing ocean navigation safety through intelligent technology*

## 📁 Project Structure

```
marine-weather-assistant/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── database.py            # Database configuration
│   ├── models.py              # SQLAlchemy models
│   ├── schemas.py             # Pydantic schemas
│   ├── auth.py                # Authentication logic
│   ├── routers/               # API route handlers
│   │   ├── auth.py
│   │   ├── weather.py
│   │   ├── routes.py
│   │   ├── alerts.py
│   │   └── ai_chat.py
│   ├── services/              # Business logic
│   │   ├── weather_service.py
│   │   ├── ai_service.py
│   │   ├── route_service.py
│   │   └── alert_service.py
│   ├── scheduler.py           # Background tasks
│   └── setup_database.py      # Database setup
├── frontend/
│   ├── src/
│   │   ├── components/        # Reusable components
│   │   ├── pages/            # Page components
│   │   ├── contexts/         # React contexts
│   │   └── App.js            # Main app component
│   ├── package.json
│   └── tailwind.config.js
├── requirements.txt
└── README.md
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Database Configuration
DATABASE_URL=mysql+pymysql://root:@localhost:3306/marine_weather

# JWT Secret Key (Change this in production!)
SECRET_KEY=your-super-secret-jwt-key-change-this-in-production

# Email Configuration (Gmail SMTP)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

# Weather API Keys
STORMGLASS_API_KEY=your-stormglass-api-key
OPEN_METEO_API_KEY=your-open-meteo-api-key

# AI Service Configuration
OPENAI_API_KEY=your-openai-api-key

# Application Settings
DEBUG=True
HOST=0.0.0.0
PORT=8000
```

### API Keys Setup

1. **OpenAI API**: Get your API key from https://platform.openai.com/
2. **StormGlass API**: Sign up at https://stormglass.io/
3. **Gmail SMTP**: Enable 2FA and create an app password

## 📊 Example User Scenario

**Maria (Fisherwoman)**:
1. Logs in with her email
2. Sets two points: Colombo → Chennai
3. Views dashboard with current weather and 7-day forecast
4. Sees hazard probabilities (fog 10%, storm 35%)
5. Gets AI summary: "Day 2: High chance of strong winds (55 km/h) between 120–200 km along your route"
6. Receives email alerts every 10 minutes when hazards are detected
7. Uses AI chatbox: "Is it safe to sail tomorrow from Colombo to Chennai?"
8. Gets AI response: "No. Forecast shows high storm probability (70%) near mid-route. Best window: after 3 days."

## 🔄 Background Tasks

The system runs background tasks every 10 minutes to:
- Check weather conditions at saved locations
- Compare against user alert thresholds
- Send email notifications for hazards
- Update IR content from government sources

## 🗺️ Map Integration

- Interactive Leaflet maps for location selection
- Real-time weather data visualization
- Route plotting between two points
- Hazard zone highlighting

## 🤖 AI Features

- **Hazard Summarization**: Converts technical weather data into human-readable warnings
- **Route Risk Assessment**: Analyzes weather along entire routes
- **Interactive Chat**: Natural language queries about marine weather
- **Safety Recommendations**: AI-powered advice for navigation decisions

## 📧 Email Alerts

- Configurable alert types (storm, fog, tsunami, high wind, rough sea)
- Customizable thresholds for each hazard type
- Email notifications sent every 10 minutes when conditions are met
- Alert history tracking and management

## 🧪 Testing

```bash
# Backend tests
cd backend
python -m pytest

# Frontend tests
cd frontend
npm test
```

## 🚀 Deployment

### Production Considerations
1. Use a production database (PostgreSQL recommended)
2. Set up proper environment variables
3. Configure HTTPS and SSL certificates
4. Set up monitoring and logging
5. Use a production WSGI server (Gunicorn)

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up -d
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation at `/docs` endpoint
- Review the API documentation at `/docs`

## 🔮 Future Enhancements

- Mobile app development
- Real-time vessel tracking
- Integration with marine traffic APIs
- Advanced machine learning models
- Multi-language support
- Offline functionality

---

**Built with ❤️ for the marine community**
