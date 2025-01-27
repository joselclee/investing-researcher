# firebase_config.py
import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate('investing-controller-firebase-adminsdk-fbsvc-828509e477.json')
firebase_admin.initialize_app(cred)

db = firestore.client()