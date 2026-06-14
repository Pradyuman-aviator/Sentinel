import os
import certifi
import pandas as pd
import pymongo
from dotenv import load_dotenv
load_dotenv()

MONGO_DB_URL = os.getenv("MONGO_DB_URL")
ca = certifi.where()

print(f"Connecting to {MONGO_DB_URL}...")
client = pymongo.MongoClient(MONGO_DB_URL, tlsCAFile=ca)
collection = client["Pradyumansh"]["NetworkData"]

print("Fetching documents...")
records = list(collection.find())
print(f"Fetched {len(records)} records.")
df = pd.DataFrame(records)
print(f"DataFrame shape: {df.shape}")
