import os
from datetime import timedelta
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    
    # Use MySQL if DATABASE_URL is provided, else fallback to local SQLite for development
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'campusride.db')
        
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY') or 'AIzaSyB1sARIOwKuH5MGum-jgkxJN5bp0Szixkw'
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY') or 'AIzaSyBMSObYr2AVek5b2Jz9oPMA0IsBZLgL6PI'
    
    # Remember Me functionality persistence
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    SESSION_PERMANENT = True
