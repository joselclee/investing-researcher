# firebase_config.py
import firebase_admin
from firebase_admin import credentials, firestore
import os

service_account_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

if not service_account_path:
    raise ValueError('No service account provided')
cred = credentials.Certificate(service_account_path) # Replace with your own file
firebase_admin.initialize_app(cred)

db = firestore.client()