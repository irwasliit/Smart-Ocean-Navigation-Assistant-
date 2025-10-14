#!/usr/bin/env python3
"""
Database setup script for Marine Weather & AI Hazard Assistant
Run this script to create the database and tables
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_database():
    """Create the SQLite database if it doesn't exist"""
    try:
        # For SQLite, the database file will be created automatically
        # when we create the engine, so no need for manual database creation
        database_url = os.getenv('DATABASE_URL', 'sqlite:///marine_weather.db')
        print(f"Using database: {database_url}")
        
        # Create the engine - this will create the SQLite file if it doesn't exist
        engine = create_engine(database_url)
        
        print("✅ Database connection established successfully")
        
        return engine
        
    except Exception as err:
        print(f"❌ Error setting up database: {err}")
        return None

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
    print("\n1. Setting up database...")
    engine = create_database()
    if not engine:
        return
    
    # Step 2: Create tables
    print("\n2. Creating tables...")
    if not create_tables():
        return
    
    # Step 3: Insert sample data (optional)
    print("\n3. Inserting sample data...")
    if not insert_sample_data():
        print("⚠️  Sample data insertion failed, but database is ready for use")
        print("   You can register a new account through the frontend")
    
    print("\n" + "=" * 60)
    print("🎉 Database setup completed successfully!")
    print("\nNext steps:")
    print("1. Start the backend server: python start_backend.py")
    print("2. Start the frontend: cd frontend && npm start") 
    print("3. Visit http://localhost:3000 and register/login")

if __name__ == "__main__":
    main()
