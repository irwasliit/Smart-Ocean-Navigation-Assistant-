# Weather Map Location Features & Email Notifications

## 🌊 Enhanced Weather Map Features

### Location Details Display
- **Fixed Location Details Box**: Now shows actual selected location information instead of default location
- **Reverse Geocoding**: Automatically fetches location names, country, state/region from coordinates
- **Real-time Updates**: Location details update immediately when you click on the map

### Smart Location Saving
- **Default Location Names**: Automatically suggests county/ocean names when saving locations
- **Editable Names**: You can change the suggested name before saving
- **Location Context**: Shows country, state, and city information for better context

### Daily Email Notifications
- **Automated Daily Reports**: Receive detailed weather emails every day at 6 AM
- **Comprehensive Weather Data**: Includes current conditions, hazard assessment, and 7-day forecast
- **AI-Generated Summaries**: Personalized weather summaries with safety recommendations
- **Beautiful Email Templates**: Professional HTML emails with responsive design

## 📧 Email Notification Features

### What You'll Receive Daily:
- **Current Weather Conditions**: Temperature, wind speed, wave height, visibility
- **Hazard Assessment**: Storm, fog, tsunami, high wind, and rough sea probabilities
- **7-Day Forecast**: Extended weather outlook with temperature trends
- **AI Safety Summary**: Personalized recommendations and warnings
- **Location-Specific Data**: Weather data specific to your saved locations

### Email Configuration
To enable email notifications, configure these environment variables:

```bash
# Email Configuration (Gmail SMTP)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
FROM_EMAIL=your_email@gmail.com
TEST_EMAIL=your_test_email@example.com
```

### Setting Up Gmail App Password
1. Enable 2-Factor Authentication on your Gmail account
2. Go to Google Account Settings > Security > App passwords
3. Generate a new app password for "Mail"
4. Use this password as `SMTP_PASSWORD` in your .env file

## 🚀 How to Use

### Saving Locations with Email Notifications
1. **Click on the map** to select a location
2. **View location details** in the right panel (shows real location name)
3. **Click "Save Location"** button
4. **Edit the location name** if needed (default name is auto-suggested)
5. **Check the email notification option** (enabled by default)
6. **Click Save** to save the location

### Managing Email Notifications
- Email notifications are **automatically enabled** when you save a location
- You'll receive **daily emails at 6 AM** for all your saved locations
- Each email contains **detailed weather information** for that specific location
- Emails include **AI-generated safety recommendations**

## 🧪 Testing Email Functionality

Run the test script to verify email notifications work:

```bash
# Set your test email in .env file
TEST_EMAIL=your_email@example.com

# Run the test
python test_email_notifications.py
```

## 🔧 Technical Implementation

### Backend Services
- **EmailService**: Handles SMTP email sending with HTML templates
- **NotificationScheduler**: Manages daily email scheduling and bulk notifications
- **WeatherService**: Enhanced with reverse geocoding for location details
- **AIService**: Generates personalized weather summaries

### Frontend Enhancements
- **Real-time Location Details**: Shows actual location information from reverse geocoding
- **Smart Location Names**: Auto-suggests meaningful names based on geographic data
- **Email Notification Toggle**: Option to enable/disable daily emails when saving locations

### Database Integration
- **SavedLocation Model**: Stores user locations with email notification preferences
- **WeatherData Model**: Historical weather data for trend analysis
- **AlertHistory Model**: Tracks sent notifications and user engagement

## 📱 Email Template Features

### HTML Email Design
- **Responsive Design**: Works on desktop and mobile devices
- **Professional Styling**: Clean, modern design with marine theme
- **Color-Coded Hazards**: Visual indicators for different hazard levels
- **Weather Icons**: Intuitive symbols for weather conditions

### Content Structure
- **Header**: Location name and current date
- **Current Conditions**: Grid layout with key weather metrics
- **Hazard Assessment**: Detailed probability breakdown
- **7-Day Forecast**: Extended outlook with temperature trends
- **AI Summary**: Personalized safety recommendations
- **Footer**: App branding and safety reminders

## 🔒 Security & Privacy

- **Secure SMTP**: Uses TLS encryption for email transmission
- **No Data Storage**: Email content is generated fresh each time
- **User Control**: Users can disable notifications anytime
- **Privacy Focused**: Only sends weather data, no personal information

## 🌐 API Endpoints

### New Endpoints Added
- `GET /api/weather/location-details/{lat}/{lng}` - Reverse geocoding
- `POST /api/weather/locations` - Save location with email preferences
- Background scheduler for daily email notifications

### Enhanced Existing Endpoints
- Weather data now includes location context
- Saved locations include email notification settings
- AI summaries integrated into weather responses

## 📊 Monitoring & Logging

- **Comprehensive Logging**: All email operations are logged
- **Error Handling**: Graceful fallbacks if email services fail
- **Success Tracking**: Monitor notification delivery rates
- **User Feedback**: Track user engagement with email notifications

This implementation provides a complete weather monitoring solution with professional email notifications, making it easy for users to stay informed about marine weather conditions for their saved locations.


