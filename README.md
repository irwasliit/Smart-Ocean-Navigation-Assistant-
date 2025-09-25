# 🌊 Smart Ocean Navigation Assistant# 🌊 Smart Ocean Navigation Assistant



**An advanced marine weather and AI navigation system** designed for maritime professionals, providing real-time weather analysis, intelligent route planning, and AI-powered hazard detection for safe ocean navigation.**An advanced marine weather and AI navigation system** designed for maritime professionals, providing real-time weather analysis, intelligent route planning, and AI-powered hazard detection for safe ocean navigation.



![Version](https://img.shields.io/badge/Version-2.0.0-blue)![Version](https://img.shields.io/badge/Version-2.0.0-blue)

![License](https://img.shields.io/badge/License-MIT-green)![License](https://img.shields.io/badge/License-MIT-green)

![Python](https://img.shields.io/badge/Python-3.8+-blue)![Python](https://img.shields.io/badge/Python-3.8+-blue)

![React](https://img.shields.io/badge/React-18.2+-blue)![React](https://img.shields.io/badge/React-18.2+-blue)



## 🚀 Key Features## 🚀 Key Features



### 🤖 Multi-Agent AI System### 🤖 Multi-Agent AI System

- **Weather Analyst Agent**: Real-time marine weather analysis and forecasting- **Weather Analyst Agent**: Real-time marine weather analysis and forecasting

- **Route Optimizer Agent**: AI-powered navigation route optimization  - **Route Optimizer Agent**: AI-powered navigation route optimization

- **Hazard Detector Agent**: Intelligent maritime hazard identification- **Hazard Detector Agent**: Intelligent maritime hazard identification

- **Communication Manager Agent**: Natural language maritime assistance- **Information Retriever Agent**: NLP-powered maritime content processing

- **Distance Calculator**: Precise nautical distance calculations between ports- **Communication Manager Agent**: Smart user interaction coordination



### 🧭 Maritime Navigation Tools### 🧠 Advanced NLP & IR Capabilities

- **Interactive Weather Maps**: Real-time weather visualization with Leaflet- **Natural Language Processing**: NLTK, spaCy, and TextBlob integration

- **Route Analysis**: AI-enhanced route planning between harbors and ports- **Maritime Content Analysis**: Specialized processing for marine bulletins

- **Hazard Detection**: Automated safety alerts and warnings- **Multi-Source Data Integration**: RSS feeds, government maritime sources

- **Port Database**: Pre-loaded coordinates for major maritime locations- **Intelligent Document Processing**: Automatic content categorization

- **Weather Forecasting**: 7-day marine weather predictions- **Real-time Information Retrieval**: Live maritime data aggregation



### 🌊 Real-time Data Integration### 🌐 Enhanced User Interface

- **OpenWeatherMap API**: Live marine weather conditions- **Marine-Themed Design**: Professional maritime color scheme

- **Geolocation Services**: Precise location identification- **Real-time Agent Status**: Live monitoring of AI agent availability

- **Email Notifications**: Automated hazard alerts and updates- **Confidence Scoring**: AI response reliability indicators

- **Background Monitoring**: Continuous weather surveillance- **Interactive Maps**: Leaflet-powered weather and route visualization

- **Responsive Design**: Optimized for desktop and mobile devices

### 💬 AI Chat Assistant

- **Natural Language Processing**: Maritime queries in plain English### 📡 Advanced Data Sources

- **Distance Calculations**: "Calculate distance between Chennai Fort and Colombo Fort"- **OpenWeatherMap API**: Real-time weather data

- **Weather Analysis**: Location-specific marine weather insights- **Maritime Bulletins**: Government maritime safety notices

- **Route Recommendations**: AI-powered navigation advice- **RSS Feeds**: Live maritime news and updates

- **High Confidence Responses**: 95% accuracy for distance queries, 85% for weather- **Geographic APIs**: Location-based services

- **Route Analysis**: Intelligent navigation planning

## 🛠️ Technology Stack

## 🛠️ Technical Architecture

### Backend (Python)

- **FastAPI**: High-performance REST API framework### Backend (FastAPI + Python)

- **OpenAI GPT-3.5-turbo**: Advanced language model for maritime analysis```

- **SQLAlchemy**: Database ORM with SQLite storagebackend/

- **APScheduler**: Background task scheduling for alerts├── main.py                     # Application entry point with enhanced AI routing

- **Uvicorn**: ASGI server with extended timeout support├── services/

│   ├── multi_agent_ai_service.py    # Core multi-agent AI system

### Frontend (React)│   ├── enhanced_ir_service.py       # NLP-powered information retrieval

- **React 18.2**: Modern UI framework with hooks│   ├── weather_service.py           # Weather data processing

- **Tailwind CSS**: Professional maritime-themed styling│   ├── route_service.py             # Route optimization

- **Leaflet**: Interactive mapping with weather overlays│   └── alert_service.py             # Alert management

- **Axios**: HTTP client with 120-second timeout handling├── routers/

- **React Hot Toast**: User-friendly notifications│   ├── enhanced_ai.py               # Enhanced AI endpoints

│   ├── weather.py                   # Weather API routes

### AI & Processing│   └── auth.py                      # Authentication

- **Multi-Agent Architecture**: Specialized AI agents for different tasks└── models.py                        # Database models

- **Haversine Formula**: Precise maritime distance calculations```

- **Weather Data Processing**: Real-time meteorological analysis

- **Location Recognition**: Intelligent port and harbor identification### Frontend (React + Tailwind CSS)

```

## 📦 Installation & Setupfrontend/src/

├── pages/

### Prerequisites│   ├── AIChat.jsx              # Enhanced multi-agent chat interface

- Python 3.8 or higher│   ├── Dashboard.jsx           # Main dashboard with AI insights

- Node.js 16 or higher│   ├── WeatherMap.jsx          # Interactive weather mapping

- OpenAI API key (for AI features)│   └── RouteAnalysis.jsx       # AI-powered route analysis

- OpenWeatherMap API key (for weather data)├── components/

│   ├── Navbar.jsx              # Navigation with AI status

### Quick Start│   └── LoadingSpinner.jsx      # Enhanced loading states

└── contexts/

1. **Clone the repository**    └── AuthContext.jsx         # Authentication management

```bash```

git clone https://github.com/irwasliit/IRWA_MARINE_PROJECT.git   ```

cd IRWA_MARINE_PROJECT

```## 🔧 Installation & Setup



2. **Backend Setup**### Prerequisites

```bash- **Python 3.10+**

# Create virtual environment- **Node.js 18+**

python -m venv venv- **MySQL 8.0+**

.\venv\Scripts\activate  # Windows- **OpenAI API Key** (for enhanced AI features)

source venv/bin/activate  # Linux/Mac

### Backend Setup

# Install dependencies

pip install -r requirements.txt1. **Clone and navigate to the project:**

```bash

# Configure environment variablesgit clone <repository-url>

cp env.example .envcd ir

# Edit .env with your API keys:```

# OPENAI_API_KEY=your_openai_key_here

# OPENWEATHERMAP_API_KEY=your_weather_key_here2. **Create virtual environment:**

```bash

# Start backend serverpython -m venv venv

python start_backend.pyvenv\Scripts\activate  # Windows

```# or

source venv/bin/activate  # Linux/Mac

3. **Frontend Setup**```

```bash

# Navigate to frontend directory3. **Install Python dependencies:**

cd frontend```bash

pip install -r requirements.txt

# Install dependencies```

npm install

4. **Download NLP models:**

# Start development server```bash

npm run devpython -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('vader_lexicon')"

```python -m spacy download en_core_web_sm

```

4. **Access the application**

- Frontend: http://localhost:30005. **Setup environment variables:**

- Backend API: http://localhost:8000```bash

- API Documentation: http://localhost:8000/docscp env.example .env

# Edit .env with your API keys and database credentials

## 🗺️ Application Pages```



### 🏠 Dashboard6. **Initialize database:**

- Weather overview and forecasts```bash

- Quick access to all featurespython backend/setup_database.py

- System status indicators```



### 🌤️ Weather Map7. **Start backend server:**

- Interactive Leaflet map with weather data```bash

- Click-to-get-weather functionalitypython start_backend.py

- Location search and port identification```

- Real-time weather conditions display

### Frontend Setup

### 🧭 Route Analysis

- Origin and destination port selection1. **Navigate to frontend directory:**

- AI-powered route optimization```bash

- Weather analysis along routecd frontend

- Risk assessment and recommendations```

- Estimated sailing times and distances

2. **Install Node.js dependencies:**

### 💬 AI Chat```bash

- Natural language maritime assistancenpm install

- Distance calculations between ports```

- Weather analysis and forecasts

- Route planning advice3. **Start development server:**

- Multi-agent AI responses with confidence scores```bash

npm run dev

### ⚠️ Hazard Alerts```

- Real-time hazard monitoring

- Email notification system### Environment Variables (.env)

- Customizable alert thresholds```env

- Alert history and management# Database Configuration

DATABASE_URL=mysql+pymysql://username:password@localhost/marine_weather

## 🔧 API Endpoints

# API Keys

### Weather EndpointsOPENAI_API_KEY=your_openai_api_key

```OPENWEATHER_API_KEY=your_openweather_api_key

GET  /api/weather/current/{lat}/{lon}    # Current weather conditions

GET  /api/weather/forecast/{lat}/{lon}   # Weather forecast data# Security

POST /api/weather/location              # Weather by location nameSECRET_KEY=your_jwt_secret_key

```ALGORITHM=HS256

ACCESS_TOKEN_EXPIRE_MINUTES=30

### AI Endpoints

```# Email Configuration

POST /api/ai/chat                       # Multi-agent AI chatEMAIL_HOST=smtp.gmail.com

POST /api/enhanced-ai/chat              # Enhanced AI chat with weatherEMAIL_PORT=587

GET  /api/ai/status                     # AI system statusEMAIL_USER=your_email@gmail.com

```EMAIL_PASSWORD=your_app_password



### Route Endpoints# AI Configuration

```MAX_TOKENS=1000

POST /api/routes/analyze                # Route analysis and optimizationTEMPERATURE=0.7

GET  /api/routes/history                # Route analysis historyMODEL_NAME=gpt-3.5-turbo

``````



### Alert Endpoints## 🚀 Usage

```

GET  /api/alerts/active                 # Active hazard alerts### Multi-Agent AI Chat

POST /api/alerts/preferences            # Alert preferences setup1. Navigate to **AI Assistant** page

GET  /api/alerts/history                # Alert history2. View real-time agent status indicators

```3. Ask questions like:

   - "Analyze current weather conditions for latitude 40.7128, longitude -74.0060"

## 🎯 Usage Examples   - "Optimize route from Miami to Nassau"

   - "Detect hazards along the Gulf Coast"

### Distance Calculation   - "Find latest maritime safety bulletins"

**Question**: "Calculate minimum distance between Chennai Fort and Colombo Fort"

### Weather Analysis

**AI Response** (95% confidence):- Real-time weather data visualization

```- AI-powered weather pattern analysis

📍 From: Chennai Fort (13.0827°N, 80.2707°E)- Marine-specific weather insights

📍 To: Colombo Fort (6.9271°N, 79.8612°E)- Interactive weather mapping

📏 Great Circle Distance: 361.24 nautical miles (669.1 km)

⏱️ Estimated sailing time: ~36-45 hours at 8-10 knots### Route Optimization

🧭 This is the shortest sea route distance (great circle)- AI-enhanced route planning

```- Weather-aware navigation suggestions

- Hazard avoidance recommendations

### Weather Analysis- Multi-factor route optimization

**Question**: "What are the current weather conditions in Mumbai harbor?"

### Information Retrieval

**AI Response** (85% confidence):- Natural language maritime queries

```- Real-time bulletin processing

🌊 LIVE WEATHER DATA for Mumbai Harbor:- Multi-source content aggregation

🌡️ Temperature: 28.5°C (83.3°F)- Intelligent content summarization

💨 Wind: 15 km/h (8.1 knots) from 220°

📊 Pressure: 1013 hPa## 🔧 API Endpoints

👁️ Visibility: 8.5 km (5.3 miles)

🌊 Wave Height: 1.2 meters### Enhanced AI Endpoints

``````

POST /api/ai/chat                    # Multi-agent chat interface

### Route Optimization  POST /api/ai/analyze-conditions      # Weather condition analysis

**Question**: "Plan optimal route from Singapore to Dubai"POST /api/ai/optimize-route         # Route optimization

POST /api/ai/detect-hazards         # Hazard detection

**AI Response**:GET  /api/ai/status                 # System and agent status

``````

🧭 ROUTE ANALYSIS: Singapore → Dubai

📏 Distance: ~3,400 nautical miles### Weather Endpoints

⏱️ Estimated Duration: 14-18 days```

🌊 Recommended Route: Via Strait of Malacca → Indian Ocean → Arabian SeaGET  /api/weather/current/{lat}/{lon}    # Current weather data

⚠️ Current Hazards: Moderate monsoon activity in Arabian SeaGET  /api/weather/forecast/{lat}/{lon}   # Weather forecast

✅ Optimal Departure: Next 3-day weather windowPOST /api/weather/batch                  # Batch weather requests

``````



## 🌟 Key Features Explained### Route Endpoints

```

### Multi-Agent AI SystemPOST /api/routes/analyze             # Route analysis

The application uses specialized AI agents that work together:POST /api/routes/optimize            # Route optimization

- **Weather Analyst**: Processes meteorological dataGET  /api/routes/history             # Route history

- **Route Optimizer**: Plans efficient and safe routes  ```

- **Hazard Detector**: Identifies potential dangers

- **Communication Manager**: Handles user interactions## 🧠 AI Agent Capabilities



### Distance Calculation Engine### Weather Analyst Agent

- Uses **Haversine formula** for precise great-circle distances- **Real-time Analysis**: Live weather data processing

- Pre-loaded database of major ports and harbors- **Pattern Recognition**: Weather trend identification

- Automatic location recognition from natural language- **Marine Focus**: Ocean-specific weather insights

- Results in nautical miles, kilometers, and statute miles- **Forecasting**: AI-enhanced weather predictions



### Real-time Weather Integration### Route Optimizer Agent

- **OpenWeatherMap API** for live data- **Multi-factor Optimization**: Weather, distance, safety

- Marine-specific weather parameters- **Dynamic Routing**: Real-time route adjustments

- 7-day forecasting capability- **Safety Integration**: Hazard-aware planning

- Weather pattern analysis and trends- **Efficiency Focus**: Fuel and time optimization



### Intelligent Route Analysis### Hazard Detector Agent

- Weather-aware route planning- **Pattern Recognition**: Hazard identification from data

- Hazard avoidance recommendations- **Safety Assessment**: Risk level evaluation

- Fuel efficiency optimization- **Alert Generation**: Automated warning systems

- Safety-first approach to navigation- **Predictive Analysis**: Future hazard prediction



## 📊 Project Structure### Information Retriever Agent

- **NLP Processing**: Natural language understanding

```- **Content Aggregation**: Multi-source data collection

IRWA_MARINE_PROJECT/- **Document Analysis**: Maritime bulletin processing

├── backend/                    # Python FastAPI backend- **Knowledge Extraction**: Key information identification

│   ├── main.py                # Application entry point

│   ├── routers/               # API route handlers### Communication Manager Agent

│   │   ├── weather.py         # Weather API endpoints- **Response Coordination**: Multi-agent response management

│   │   ├── ai_chat.py         # AI chat functionality- **Context Awareness**: Conversation context maintenance

│   │   ├── routes.py          # Route analysis endpoints- **User Intent Recognition**: Query understanding

│   │   └── alerts.py          # Hazard alert system- **Response Optimization**: Best response selection

│   ├── services/              # Business logic services

│   │   ├── multi_agent_ai_service.py    # Core AI system## 🎨 Enhanced UI Features

│   │   ├── weather_service.py           # Weather data processing

│   │   ├── location_search_service.py   # Location services### Marine Theme Design

│   │   └── alert_service.py             # Alert management- **Ocean-inspired Colors**: Professional maritime palette

│   ├── models.py              # Database models- **Responsive Layout**: Mobile-first design approach

│   ├── database.py            # Database configuration- **Interactive Elements**: Smooth animations and transitions

│   └── scheduler.py           # Background task scheduling- **Accessibility**: WCAG-compliant design

├── frontend/                  # React frontend application

│   ├── src/### Real-time Status Indicators

│   │   ├── pages/            # Application pages- **Agent Status**: Live agent availability monitoring

│   │   │   ├── Dashboard.jsx      # Main dashboard- **System Health**: Overall system status display

│   │   │   ├── WeatherMap.jsx     # Interactive weather map- **Confidence Scores**: AI response reliability indicators

│   │   │   ├── RouteAnalysis.jsx  # Route planning tool- **Processing States**: Real-time operation feedback

│   │   │   └── AIChat.jsx        # AI assistant interface

│   │   ├── components/       # Reusable UI components### Enhanced Chat Interface

│   │   │   ├── Navbar.jsx         # Navigation component- **Multi-agent Responses**: Agent-specific message handling

│   │   │   ├── WeatherCard.jsx    # Weather display cards- **Rich Formatting**: Enhanced message presentation

│   │   │   └── LoadingSpinner.jsx # Loading animations- **Conversation History**: Persistent chat storage

│   │   └── contexts/         # React context providers- **Quick Suggestions**: Contextual query suggestions

│   ├── public/               # Static assets

│   └── package.json          # Frontend dependencies## 📦 Docker Deployment

├── setup.py                  # Project setup script

├── start_backend.py          # Backend startup script### Build and run with Docker Compose:

├── start_frontend.py         # Frontend startup script```bash

├── requirements.txt          # Python dependenciesdocker-compose up --build

├── docker-compose.yml        # Docker deployment```

└── README.md                 # Project documentation

```### Individual container builds:

```bash

## 🔐 Environment Configuration# Backend

docker build -t marine-weather-backend ./backend

Create a `.env` file in the project root:

# Frontend

```envdocker build -t marine-weather-frontend ./frontend

# API Keys```

OPENAI_API_KEY=your_openai_api_key_here

OPENWEATHERMAP_API_KEY=your_openweathermap_api_key_here## 🔍 Testing



# Database### Backend Tests

DATABASE_URL=sqlite:///./marine_weather.db```bash

cd backend

# Email Configuration (optional)python -m pytest tests/

SMTP_SERVER=smtp.gmail.com  ```

SMTP_PORT=587

SMTP_USERNAME=your_email@gmail.com### API Testing

SMTP_PASSWORD=your_app_password```bash

python test_apis.py

# Securitypython test_fixed_apis.py

SECRET_KEY=your_secret_key_herepython test_email_notifications.py

ALGORITHM=HS256```

ACCESS_TOKEN_EXPIRE_MINUTES=30

```### Frontend Tests

```bash

## 🐳 Docker Deploymentcd frontend

npm test

```bash```

# Build and run with Docker Compose

docker-compose up --build## 🚀 Production Deployment



# Individual container builds### Environment Setup

docker build -t marine-weather-backend ./backend1. **Database**: MySQL 8.0+ with proper indexing

docker build -t marine-weather-frontend ./frontend2. **Web Server**: Nginx with SSL configuration

```3. **Application**: Gunicorn for Python, PM2 for Node.js

4. **Monitoring**: Implement logging and monitoring

## 🧪 Testing5. **Security**: Proper API key management and CORS setup



The application includes comprehensive testing capabilities:### Performance Optimization

- **Caching**: Redis for session and response caching

```bash- **CDN**: Static asset delivery optimization

# Start backend server- **Database**: Query optimization and indexing

python start_backend.py- **AI**: Response caching for common queries



# Test AI chat functionality## 🤝 Contributing

# Visit http://localhost:3000/chat and try:

# "Calculate distance between Singapore and Dubai"1. Fork the repository

# "What's the weather in Mumbai?"2. Create feature branch (`git checkout -b feature/enhancement`)

# "Plan route from Chennai to Colombo"3. Commit changes (`git commit -am 'Add new feature'`)

4. Push to branch (`git push origin feature/enhancement`)

# Test weather map5. Create Pull Request

# Visit http://localhost:3000/weather

# Click on map locations to get weather data## 📄 License



# Test route analysis  This project is licensed under the MIT License - see the LICENSE file for details.

# Visit http://localhost:3000/route-analysis

# Set origin and destination ports## 🆘 Support

# Generate AI-powered route analysis

```For support and questions:

- **Documentation**: Check inline code documentation

## 🚀 Performance Features- **Issues**: Create GitHub issues for bugs

- **Features**: Submit feature requests via GitHub

- **Extended Timeouts**: 120-second frontend timeout, 150-second backend timeout- **Community**: Join our discussion forums

- **Continuous Loading**: Real-time progress indicators without fake timers

- **Efficient Logging**: Minimal production logging for better performance## 🎯 Roadmap

- **AI Optimization**: GPT-3.5-turbo for fast, cost-effective responses

- **Database Caching**: SQLite with optimized queries### Upcoming Features

- **Machine Learning Models**: Custom weather prediction models

## 🤝 Contributing- **Advanced Visualization**: 3D weather and route modeling

- **Mobile App**: Native mobile application

1. Fork the repository- **Offline Capabilities**: Offline weather data and routing

2. Create a feature branch: `git checkout -b feature/new-feature`- **Integration APIs**: Third-party marine software integration

3. Commit changes: `git commit -am 'Add new feature'`

4. Push to branch: `git push origin feature/new-feature`### Performance Enhancements

5. Submit a Pull Request- **Real-time Updates**: WebSocket-based live updates

- **Advanced Caching**: Intelligent data caching strategies

## 📄 License- **Scalability**: Microservices architecture migration

- **AI Optimization**: Custom-trained maritime AI models

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🆘 Support & Contact

**Built with ❤️ for the maritime community**

- **GitHub Issues**: [Report bugs or request features](https://github.com/irwasliit/IRWA_MARINE_PROJECT/issues)

- **Documentation**: [Project Wiki](https://github.com/irwasliit/IRWA_MARINE_PROJECT/wiki)*Enhancing ocean navigation safety through intelligent technology*

- **Email**: [Contact Developer](mailto:irwasliit@gmail.com)

## 📁 Project Structure

## 🌟 Acknowledgments

```

- **OpenAI** for GPT-3.5-turbo language modelmarine-weather-assistant/

- **OpenWeatherMap** for marine weather data├── backend/

- **Leaflet** for interactive mapping capabilities│   ├── main.py                 # FastAPI application

- **Maritime Community** for domain expertise and feedback│   ├── database.py            # Database configuration

│   ├── models.py              # SQLAlchemy models

---│   ├── schemas.py             # Pydantic schemas

│   ├── auth.py                # Authentication logic

**Built with ❤️ for safer ocean navigation**│   ├── routers/               # API route handlers

│   │   ├── auth.py

*Enhancing maritime safety through intelligent technology*│   │   ├── weather.py
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
