# 🌊 IRWA Marine Project

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/irwasliit/IRWA_MARINE_PROJECT)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/react-18+-61DAFB.svg)](https://reactjs.org/)

**Smart Ocean Navigation Assistant** - A comprehensive marine weather monitoring and navigation system powered by AI, providing real-time weather data, intelligent route optimization, and advanced hazard detection for maritime professionals.

---

## 📋 Table of Contents

- [Features](#-features)
- [Subscription Plans](#-subscription-plans)
- [Technology Stack](#-technology-stack)
- [Project Structure](#-project-structure)
- [Setup & Installation](#-setup--installation)
- [Usage Guide](#-usage-guide)
- [API Documentation](#-api-documentation)
- [Contributors](#-contributors)
- [License](#-license)

---

## ✨ Features

### 🔐 Authentication & User Management
- User registration with email validation
- Secure JWT-based authentication
- Password encryption with bcrypt
- Profile management and settings
- Multi-tier subscription system (Free, Pro, Premium)

### 🌦️ Real-Time Weather Monitoring
- Live marine weather data (temperature, humidity, wind speed/direction)
- Wave height and period analysis
- Atmospheric pressure and visibility tracking
- Interactive weather map with location search
- Save favorite locations for quick access
- Harbor/port weather information
- Timezone-aware weather reports

### 🗺️ Intelligent Route Analysis
- AI-powered route optimization between ports
- Weather-based risk assessment along routes
- Distance and estimated sailing time calculation
- Waypoint generation and route visualization
- Historical route analysis tracking
- Weather conditions analysis for entire journey
- Hazard zone identification

### 🤖 Multi-Agent AI Chat System
- Natural Language Processing (NLP) for maritime queries
- Real-time weather information retrieval
- Safety recommendations and hazard analysis
- Distance and route calculations
- Multi-agent AI architecture for specialized responses
- Context-aware conversations
- Chat history storage and retrieval
- Support for complex maritime questions

### ⚠️ Advanced Hazard Detection & Alerts
- Real-time hazard monitoring (storms, fog, tsunamis, high winds)
- ML-based hazard probability predictions
- Customizable alert thresholds
- Email notification system
- Alert history tracking
- Location-based hazard analysis
- Severity classification (Low, Medium, High, Critical)
- Automated scheduled alert checks

### 🏢 Harbor & Location Services
- Global harbor and port database
- Nearest harbor finder
- Harbor location validation
- Advanced location search with coordinates
- Geocoding and reverse geocoding
- Support for multiple location formats

### 📊 Data Analytics & Reporting
- Weather data visualization
- Route performance analytics
- Alert statistics and trends
- Historical weather data analysis
- User activity tracking

### 🔔 Notification System
- Scheduled background alert monitoring
- Email notifications for critical alerts
- Customizable notification preferences
- Real-time alert updates
- Alert acknowledgment system

---

## 💎 Subscription Plans

### 🆓 Free Plan
- Basic weather information
- Basic AI chat (10 queries per day)
- No Saved location
- No Alert details
- Standard hazard alerts searches

### 🌟 Pro Plan
- Unlimited weather queries
- Enhanced AI chat (50 queries per day)
- Up to 5 saved locations
- Priority hazard alerts
- Email notifications
-Custom alert thresholds

### 💎 Premium Plan
- All Pro features
- Route analysis
- Unlimited AI chat queries
- Unlimited saved locations
- Multi-location alert monitoring
- Custom alert thresholds
- Advanced analytics and reporting
- Priority customer support
- API access for integration

**Upgrade anytime through the Profile page with secure payment processing!**

---

## 🛠️ Technology Stack

### Backend
- **Framework:** FastAPI (Python 3.8+)
- **Database:** MySQL with SQLAlchemy ORM
- **Authentication:** JWT (JSON Web Tokens)
- **AI/ML Libraries:** 
  - OpenAI GPT for conversational AI
  - Transformers (Hugging Face)
  - PyTorch for ML models
  - NLTK, spaCy, TextBlob for NLP
- **Task Scheduling:** APScheduler
- **Web Scraping:** BeautifulSoup4, Scrapy, Newspaper3k
- **Geospatial:** GeoPy, Folium
- **Email:** Jinja2 templating, aiofiles

### Frontend
- **Framework:** React 18+ with Vite
- **Routing:** React Router v6
- **Styling:** Tailwind CSS
- **HTTP Client:** Axios
- **State Management:** React Context API
- **Maps:** Leaflet / Mapbox integration
- **Icons:** Custom icon components

### DevOps
- **Containerization:** Docker & Docker Compose
- **Web Server:** Nginx (production)
- **CORS:** Full cross-origin support
- **Environment:** Python dotenv configuration

---

## 📁 Project Structure

```
irwa_marine/
├── backend/                          # FastAPI backend application
│   ├── main.py                       # Application entry point
│   ├── database.py                   # Database configuration
│   ├── models.py                     # SQLAlchemy database models
│   ├── schemas.py                    # Pydantic schemas
│   ├── auth.py                       # Authentication utilities
│   ├── scheduler.py                  # Background task scheduler
│   ├── setup_database.py             # Database initialization
│   ├── routers/                      # API route handlers
│   │   ├── auth.py                   # Authentication endpoints
│   │   ├── weather.py                # Weather API endpoints
│   │   ├── routes.py                 # Route analysis endpoints
│   │   ├── enhanced_routes.py        # Advanced routing features
│   │   ├── alerts.py                 # Alert management
│   │   ├── hazard_alerts.py          # Hazard detection endpoints
│   │   ├── ai_chat.py                # AI chat endpoints
│   │   ├── enhanced_ai.py            # Advanced AI features
│   │   ├── enhanced_ai_chat_router.py # Enhanced chat routing
│   │   └── billing.py                # Subscription management
│   └── services/                     # Business logic services
│       ├── weather_service.py        # Weather data processing
│       ├── route_service.py          # Route optimization
│       ├── alert_service.py          # Alert generation
│       ├── hazard_alerts_service.py  # Hazard detection logic
│       ├── email_service.py          # Email notification service
│       ├── harbor_service.py         # Harbor data management
│       ├── location_search_service.py # Location search utilities
│       ├── multi_agent_ai_service.py # Multi-agent AI system
│       ├── enhanced_ai_chat_service.py # Enhanced chat service
│       ├── huggingface_ai_service.py # Hugging Face AI integration
│       ├── ollama_ai_service.py      # Ollama AI integration
│       ├── intelligent_ai_analyzer.py # AI analysis engine
│       ├── disaster_prediction_service.py # Disaster ML models
│       ├── real_time_disaster_service.py # Real-time disaster monitoring
│       ├── enhanced_ir_service.py    # Enhanced IR processing
│       ├── simple_enhanced_ir_service.py # Simplified IR service
│       └── notification_scheduler.py # Scheduled notifications
├── frontend/                         # React frontend application
│   ├── src/
│   │   ├── main.jsx                  # Application entry point
│   │   ├── App.jsx                   # Main App component
│   │   ├── index.css                 # Global styles
│   │   ├── components/               # Reusable UI components
│   │   │   ├── Navbar.jsx            # Navigation bar
│   │   │   ├── LoadingSpinner.jsx    # Loading indicator
│   │   │   ├── ErrorBoundary.jsx     # Error handling
│   │   │   ├── WeatherWidget.jsx     # Weather display widget
│   │   │   ├── HazardAlerts.jsx      # Hazard alert component
│   │   │   ├── MapOverlay.jsx        # Map overlay UI
│   │   │   ├── LocationSearch.jsx    # Location search component
│   │   │   ├── HarborSearch.jsx      # Harbor search component
│   │   │   └── WeatherMapLocationSearch.jsx # Map location search
│   │   ├── pages/                    # Application pages
│   │   │   ├── Login.jsx             # Login page
│   │   │   ├── Register.jsx          # Registration page
│   │   │   ├── Dashboard.jsx         # Main dashboard
│   │   │   ├── WeatherMap.jsx        # Interactive weather map
│   │   │   ├── RouteAnalysis.jsx     # Route planning page
│   │   │   ├── AIChat.jsx            # AI chat interface
│   │   │   ├── Alerts.jsx            # Alert management
│   │   │   ├── HazardAlertsPage.jsx  # Hazard alerts page
│   │   │   ├── Profile.jsx           # User profile
│   │   │   └── Upgrade.jsx           # Subscription upgrade
│   │   └── contexts/
│   │       └── AuthContext.jsx       # Authentication context
│   ├── public/
│   │   └── service-worker.js         # PWA service worker
│   ├── package.json                  # NPM dependencies
│   ├── vite.config.js                # Vite configuration
│   ├── tailwind.config.js            # Tailwind CSS config
│   └── nginx.conf                    # Nginx configuration
├── docker-compose.yml                # Docker services configuration
├── requirements.txt                  # Python dependencies
├── setup.py                          # Python package setup
├── start_backend.py                  # Backend startup script
├── start_frontend.py                 # Frontend startup script (Python)
├── start_frontend.bat                # Frontend startup script (Windows)
├── env.example                       # Environment variables template
├── EMAIL_SETUP_GUIDE.md              # Email configuration guide
└── README.md                         # This file
```

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.10 or higher
- Node.js 18+ and npm
- Git

### 1️⃣ Clone the Repository

```powershell
git clone https://github.com/irwasliit/IRWA_MARINE_PROJECT.git
cd IRWA_MARINE_PROJECT
```

### 2️⃣ Backend Setup

**Step 1: Create Virtual Environment**

```powershell
python -m venv venv
.\venv\Scripts\activate
```

**Step 2: Install Dependencies**

```powershell
pip install -r requirements.txt
```

**Step 3: Configure Environment Variables**

Copy `env.example` to `.env` and configure:

```bash
# Database Configuration
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/irwa_marine

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API Keys
OPENWEATHER_API_KEY=your-openweather-api-key
OPENAI_API_KEY=your-openai-api-key

# Email Configuration (see EMAIL_SETUP_GUIDE.md)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password
```

**Step 4: Initialize Database**

```powershell
python backend/setup_database.py
```

**Step 5: Start Backend Server**

```powershell
python start_backend.py
```

Backend will run on: `http://localhost:8000`

### 3️⃣ Frontend Setup

**Step 1: Navigate to Frontend Directory**

```powershell
cd frontend
```

**Step 2: Install Dependencies**

```powershell
npm install
```

**Step 3: Configure Environment**

Create `.env` file in `frontend/` directory:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

**Step 4: Start Development Server**

```powershell
npm run dev
```

Frontend will run on: `http://localhost:5173`

### 4️⃣ Docker Setup (Alternative)

```powershell
docker-compose up -d
```

This will start all services (backend, frontend, database) in containers.

---

## 📖 Usage Guide

### Getting Started

1. **Register an Account**
   - Navigate to `http://localhost:5173/register`
   - Fill in your details (name, email, password)
   - Click "Sign Up"

2. **Login**
   - Go to login page
   - Enter credentials
   - Access the dashboard

3. **Explore Weather**
   - Click "Weather Map" in navigation
   - Search for locations or click on map
   - View real-time weather data
   - Save favorite locations

4. **Analyze Routes**
   - Navigate to "Route Analysis"
   - Select origin and destination ports
   - Get AI-powered route analysis
   - View weather conditions along route
   - Check hazard warnings

5. **Use AI Chat**
   - Go to "AI Chat" page
   - Ask questions like:
     - "What's the weather in Colombo?"
     - "Is it safe to sail from Chennai to Singapore tomorrow?"
     - "What are the current hazards near Mumbai port?"
   - Get intelligent responses with weather data

6. **Set Up Alerts**
   - Visit "Hazard Alerts" page
   - Configure alert preferences
   - Set custom thresholds (wind speed, wave height, etc.)
   - Enable email notifications
   - Monitor alert history

7. **Upgrade Plan**
   - Access "Profile" page
   - Click "Upgrade Plan"
   - Choose Pro or Premium
   - Enter payment details
   - Enjoy enhanced features!

---

## 🔌 API Documentation

### Base URL
```
http://localhost:8000
```

### Authentication Endpoints

#### POST `/auth/register`
Register a new user
```json
{
  "email": "user@example.com",
  "password": "SecurePass123",
  "full_name": "John Doe"
}
```

#### POST `/auth/login`
Login and receive JWT token
```json
{
  "username": "user@example.com",
  "password": "SecurePass123"
}
```

### Weather Endpoints

#### GET `/weather/current?lat={lat}&lon={lon}`
Get current weather data

#### GET `/weather/forecast?lat={lat}&lon={lon}`
Get 7-day weather forecast

#### POST `/weather/save-location`
Save a favorite location

#### GET `/weather/saved-locations`
Get all saved locations

### Route Endpoints

#### POST `/routes/analyze`
Analyze route between two points
```json
{
  "start_lat": 6.9271,
  "start_lon": 79.8612,
  "end_lat": 13.0827,
  "end_lon": 80.2707,
  "route_name": "Colombo to Chennai"
}
```

#### GET `/routes/history`
Get route analysis history

### AI Chat Endpoints

#### POST `/ai-chat/query`
Send a query to AI
```json
{
  "message": "What's the weather forecast for sailing?"
}
```

#### GET `/ai-chat/history`
Retrieve chat history

### Alert Endpoints

#### GET `/hazard-alerts/comprehensive`
Get comprehensive hazard alerts

#### POST `/alerts/preferences`
Set alert preferences
```json
{
  "location_id": 1,
  "alert_types": ["storm", "fog"],
  "threshold_values": {
    "wind_speed": 50,
    "wave_height": 3.0
  }
}
```

**Full API documentation available at:** `http://localhost:8000/docs`

---

## 👥 Contributors

This project is developed and maintained by:

### Project Team
- **L. Tharshikan** ( GitHub: [@TharshiHecker](https://github.com/TharshiHecker) )
- **Lingajan** (GitHub: [@Linga1010](https://github.com/Linga1010) )
- **Rajeethan** 
- **Kajaraj**

### Acknowledgments
We would like to thank the open-source community and all the libraries that made this project possible.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 🐛 Bug Reports & Feature Requests

Please use the [GitHub Issues](https://github.com/irwasliit/IRWA_MARINE_PROJECT/issues) page to report bugs or request features.

---

## 📞 Support

For support and questions:
- Documentation: [Wiki](https://github.com/irwasliit/IRWA_MARINE_PROJECT/wiki)
- Discussions: [GitHub Discussions](https://github.com/irwasliit/IRWA_MARINE_PROJECT/discussions)

---

## 🌟 Star History

If you find this project useful, please consider giving it a ⭐ on GitHub!

---

**Made with ❤️ for the marine community. Sail smarter, safer, and with confidence!**

🌊 *IRWA Marine - Navigating Tomorrow's Oceans Today* 🌊
