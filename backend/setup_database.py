#!/usr/bin/env python3
"""
Database setup script for Marine Weather & AI Hazard Assistant
Run this script to create the database and tables
"""

import mysql.connector
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()



def create_database():
    """Create the database if it doesn't exist"""
    try:
        # Connect to MySQL server (without specifying database)
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password="",  # Database password
            port=3306
        )
        
        cursor = connection.cursor()
        
        # Create database
        cursor.execute("CREATE DATABASE IF NOT EXISTS marine_weather")
        print("✅ Database 'marine_weather' created successfully")
        
        cursor.close()
        connection.close()
        
    except mysql.connector.Error as err:
        print(f"❌ Error creating database: {err}")
        return False
    
    return True

def create_tables():
    """Create all tables using SQLAlchemy"""
    try:
        from models import Base
        from database import engine
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully")
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False
    
    return True

def insert_sample_data():
    """Insert sample data for testing"""
    try:
        from database import SessionLocal
        from models import User, SavedLocation, AlertPreference
        from auth import get_password_hash
        
        db = SessionLocal()
        
        # Check if sample user already exists
        existing_user = db.query(User).filter(User.email == "demo@marineweather.com").first()
        if existing_user:
            print("✅ Sample data already exists")
            db.close()
            return True
        
        # Create sample user
        sample_user = User(
            email="demo@marineweather.com",
            hashed_password=get_password_hash("demo123"),
            full_name="Demo User",
            is_active=True
        )
        db.add(sample_user)
        db.commit()
        db.refresh(sample_user)
        
        # Create sample locations
        sample_locations = [
            {
                "name": "Colombo Port",
                "latitude": 6.9271,
                "longitude": 79.8612,
                "location_type": "single"
            },
            {
                "name": "Chennai Port",
                "latitude": 13.0827,
                "longitude": 80.2707,
                "location_type": "single"
            },
            {
                "name": "Singapore Port",
                "latitude": 1.2966,
                "longitude": 103.7764,
                "location_type": "single"
            }
        ]
        
        for loc_data in sample_locations:
            location = SavedLocation(
                user_id=sample_user.id,
                **loc_data
            )
            db.add(location)
        
        db.commit()
        
        # Create sample alert preferences
        locations = db.query(SavedLocation).filter(SavedLocation.user_id == sample_user.id).all()
        if locations:
            alert_preference = AlertPreference(
                user_id=sample_user.id,
                location_id=locations[0].id,
                alert_types=["storm", "high_wind", "rough_sea"],
                threshold_values={
                    "wind_speed": 30,
                    "wave_height": 2.5,
                    "visibility": 1000
                },
                is_active=True
            )
            db.add(alert_preference)
        
        db.commit()
        db.close()
        
        print("✅ Sample data inserted successfully")
        print("📧 Demo login: demo@marineweather.com")
        print("🔑 Demo password: demo123")
        
    except Exception as e:
        print(f"❌ Error inserting sample data: {e}")
        return False
    
    return True

def main():
    """Main setup function"""
    print("🌊 Marine Weather & AI Hazard Assistant - Database Setup")
    print("=" * 60)
    
    # Step 1: Create database
    print("\n1. Creating database...")
    if not create_database():
        return
    
    # Step 2: Create tables
    print("\n2. Creating tables...")
    if not create_tables():
        return
    
    # Step 3: Insert sample data
    print("\n3. Inserting sample data...")
    if not insert_sample_data():
        return
    
    print("\n" + "=" * 60)
    print("🎉 Database setup completed successfully!")
    print("\nNext steps:")
    print("1. Start the backend server: python backend/main.py")
    print("2. Start the frontend: cd frontend && npm start")
    print("3. Visit http://localhost:3000 and login with demo credentials")

if __name__ == "__main__":
    main()
