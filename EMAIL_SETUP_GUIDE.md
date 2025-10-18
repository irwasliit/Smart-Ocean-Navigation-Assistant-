# Email Configuration Setup Guide

## 📧 Setting Up Email Notifications

Your Smart Ocean Navigation Assistant can send daily weather reports and hazard alerts via email. Here's how to configure it:

### 1. Gmail Setup (Recommended)

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate an App Password**:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Select "Mail" and generate password
   - Copy the 16-character password

### 2. Update Environment Variables

Edit your `.env` file and replace the placeholder values:

```env
# Email Configuration (Gmail SMTP)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_actual_email@gmail.com
SMTP_PASSWORD=your_16_character_app_password
FROM_EMAIL=your_actual_email@gmail.com
```

### 3. Test Email Functionality

1. **Backend Test**: Run `python test_email_functionality.py`
2. **Frontend Test**: Go to Profile page and click "Send Test Email"

### 4. Features Enabled

Once configured, users will receive:
- ✅ **Daily weather reports** with current conditions
- ✅ **7-day forecasts** 
- ✅ **Hazard assessments** with probability scores
- ✅ **Beautiful HTML emails** with professional styling
- ✅ **Test email functionality** via Profile page

### 5. Alternative Email Providers

For other providers, update these settings:

**Outlook/Hotmail:**
```env
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
```

**Yahoo:**
```env
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
```

### 6. Security Notes

- ✅ Use App Passwords, not your main account password
- ✅ Keep email credentials secure
- ✅ Test with your own email first
- ✅ Monitor email usage to avoid rate limits

### 7. Troubleshooting

**Common Issues:**
- Authentication errors → Check app password
- Connection timeouts → Verify SMTP settings
- Blocked by firewall → Allow SMTP traffic
- Gmail blocking → Enable "Less secure app access" (not recommended)

**Test Commands:**
```bash
# Test email configuration
python test_email_functionality.py

# Check environment variables
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('SMTP User:', os.getenv('SMTP_USERNAME'))"
```