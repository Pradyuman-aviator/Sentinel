import sys
import os
import threading
from io import StringIO

import certifi
ca = certifi.where()

from dotenv import load_dotenv
load_dotenv()
mongo_db_url = os.getenv("MONGO_DB_URL")
import pymongo
from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, File, UploadFile, Request
from fastapi.staticfiles import StaticFiles
from uvicorn import run as app_run
from fastapi.responses import Response
from starlette.responses import RedirectResponse
import pandas as pd

from networksecurity.utils.main_utils.utils import load_object

from networksecurity.utils.ml_utils.model.estimator import NetworkModel


# Connect to MongoDB — fail gracefully so the server still starts
try:
    client = pymongo.MongoClient(mongo_db_url, tlsCAFile=ca)
    from networksecurity.constant.training_pipeline import DATA_INGESTION_COLLECTION_NAME
    from networksecurity.constant.training_pipeline import DATA_INGESTION_DATABASE_NAME
    database = client[DATA_INGESTION_DATABASE_NAME]
    collection = database[DATA_INGESTION_COLLECTION_NAME]
except Exception as e:
    logging.warning(f"MongoDB connection deferred: {e}")
    client = None

from contextlib import asynccontextmanager
from fastapi import BackgroundTasks

ml_models = {}
ml_models_lock = threading.Lock()

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        preprocessor = load_object("final_model/preprocessor.pkl")
        final_model = load_object("final_model/model.pkl")
        ml_models["network_model"] = NetworkModel(preprocessor=preprocessor, model=final_model)
        logging.info("ML models loaded successfully at startup.")
    except Exception as e:
        logging.warning(f"ML models could not be loaded at startup: {e}")
    yield
    ml_models.clear()

app = FastAPI(lifespan=lifespan)
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

from fastapi.templating import Jinja2Templates
templates = Jinja2Templates(directory="./templates")


# ── Page Routes ──────────────────────────────────────────────

@app.get("/", tags=["pages"])
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/analyze", tags=["pages"])
async def analyze_page(request: Request):
    return templates.TemplateResponse("analyze.html", {"request": request})


@app.get("/train-model", tags=["pages"])
async def train_page(request: Request):
    return templates.TemplateResponse("train.html", {"request": request})


# ── API Routes ───────────────────────────────────────────────

@app.get("/train", tags=["api"])
async def train_route(background_tasks: BackgroundTasks):
    def run_training():
        try:
            # Lazy import to avoid loading dagshub/mlflow at server startup
            from networksecurity.pipeline.training_pipeline import TrainingPipeline
            train_pipeline = TrainingPipeline()
            train_pipeline.run_pipeline()
            logging.info("Training completed successfully in background.")
            
            # Reload models into cache after training
            preprocessor = load_object("final_model/preprocessor.pkl")
            final_model = load_object("final_model/model.pkl")
            ml_models["network_model"] = NetworkModel(preprocessor=preprocessor, model=final_model)
        except Exception as e:
            logging.error(f"Training pipeline failed: {e}")

    background_tasks.add_task(run_training)
    return Response("Training started in the background")


@app.post("/predict", tags=["api"])
async def predict_route(request: Request, file: UploadFile = File(...)):
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise ValueError("Only CSV files are supported")
        
        # Read and validate CSV
        df = pd.read_csv(file.file)
        if df.empty:
            raise ValueError("CSV file is empty")
        
        # Thread-safe model loading
        with ml_models_lock:
            network_model = ml_models.get("network_model")
            if not network_model:
                try:
                    preprocessor = load_object("final_model/preprocessor.pkl")
                    final_model = load_object("final_model/model.pkl")
                    network_model = NetworkModel(preprocessor=preprocessor, model=final_model)
                    ml_models["network_model"] = network_model
                except FileNotFoundError as e:
                    logging.error(f"Model files not found: {e}")
                    raise ValueError("Model not trained yet. Please train the model first.")
            
        y_pred = network_model.predict(df)
        df['predicted_column'] = y_pred
        os.makedirs('prediction_output', exist_ok=True)
        df.to_csv('prediction_output/output.csv')
        table_html = df.to_html(classes='table table-striped')
        return templates.TemplateResponse("table.html", {"request": request, "table": table_html})

    except ValueError as ve:
        logging.error(f"Validation error: {ve}")
        raise NetworkSecurityException(str(ve), sys)
    except Exception as e:
        logging.error(f"Prediction failed: {e}")
        raise NetworkSecurityException(e, sys)


if __name__ == "__main__":
    app_run(app, host="0.0.0.0", port=8080)

