<br># 🛡️ Network Security — Phishing Detection System

An end-to-end machine learning pipeline for detecting phishing attacks in network traffic. The system ingests network data from MongoDB, trains multiple classifiers with hyperparameter tuning, tracks experiments with MLflow, and serves real-time predictions via a FastAPI web API.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [ML Pipeline Details](#ml-pipeline-details)
- [API Endpoints](#api-endpoints)
- [Docker Deployment](#docker-deployment)
- [Experiment Tracking](#experiment-tracking)
- [Contributing](#contributing)
- [License](#license)

---

## 🔍 Overview

This project builds a **phishing detection classifier** that analyzes network traffic features to distinguish between legitimate and phishing activity. It follows a modular, production-style ML pipeline architecture with:

- **Automated data ingestion** from MongoDB
- **Data validation** with schema enforcement and drift detection
- **Feature transformation** using KNN Imputation for missing values
- **Multi-model training** with hyperparameter tuning across 5 classifiers
- **Experiment tracking** via MLflow + DagsHub
- **REST API** for on-demand training and real-time predictions
- **Dockerized deployment** for portability

---

## 🏗️ Architecture

```
┌──────────────┐     ┌────────────────┐     ┌──────────────────┐     ┌───────────────┐
│   MongoDB    │────▶│ Data Ingestion │────▶│  Data Validation │────▶│    Data        │
│  (Raw Data)  │     │  (Train/Test   │     │  (Schema Check,  │     │ Transformation │
│              │     │    Split)      │     │   Drift Report)  │     │ (KNN Imputer)  │
└──────────────┘     └────────────────┘     └──────────────────┘     └───────┬────────┘
                                                                            │
                          ┌──────────────┐     ┌──────────────────┐         │
                          │  FastAPI     │◀────│  Model Trainer   │◀────────┘
                          │  (Predict /  │     │  (5 Classifiers, │
                          │   Train)     │     │   MLflow Track)  │
                          └──────────────┘     └──────────────────┘
```

---

## 🧰 Tech Stack

| Category              | Technology                                     |
|-----------------------|------------------------------------------------|
| **Language**          | Python 3.10+                                   |
| **ML Framework**      | Scikit-learn                                   |
| **Web Framework**     | FastAPI + Uvicorn                              |
| **Database**          | MongoDB (via PyMongo)                          |
| **Experiment Tracking** | MLflow + DagsHub                             |
| **Data Processing**   | Pandas, NumPy                                  |
| **Containerization**  | Docker                                         |
| **Templating**        | Jinja2                                         |

---

## 📁 Project Structure

```
networksecurity/
├── app.py                      # FastAPI web application (train & predict endpoints)
├── main.py                     # Standalone pipeline runner
├── push_data.py                # Load CSV data into MongoDB
├── setup.py                    # Package configuration
├── requirements.txt            # Python dependencies
├── dockerfile                  # Docker container setup
│
├── networksecurity/            # Core Python package
│   ├── components/             # Pipeline stage implementations
│   │   ├── data_ingestion.py       # Fetch data from MongoDB, train/test split
│   │   ├── data_validation.py      # Schema validation & data drift detection
│   │   ├── data_transformation.py  # KNN Imputation preprocessing pipeline
│   │   └── model_trainer.py        # Multi-model training with MLflow tracking
│   │
│   ├── pipeline/               # Pipeline orchestration
│   │   ├── training_pipeline.py    # End-to-end training pipeline
│   │   └── batch_prediction.py     # Batch prediction pipeline
│   │
│   ├── entity/                 # Data classes
│   │   ├── config_entity.py        # Pipeline configuration objects
│   │   └── artifact_entity.py      # Pipeline artifact objects
│   │
│   ├── constant/               # Pipeline constants & hyperparameters
│   │   └── training_pipeline/      # All pipeline-related constants
│   │
│   ├── utils/                  # Utility functions
│   │   ├── main_utils/             # General utilities (save/load objects, evaluate models)
│   │   └── ml_utils/              # ML-specific utilities (model estimator, metrics)
│   │
│   ├── cloud/                  # Cloud storage integration
│   ├── exception/              # Custom exception handling
│   └── logging/                # Custom logging configuration
│
├── Network_Data/               # Raw network traffic data (CSV)
├── Artifacts/                  # Pipeline artifacts (per-run outputs)
├── final_model/                # Production-ready model & preprocessor
│   ├── model.pkl                   # Trained best model
│   └── preprocessor.pkl            # Fitted KNN Imputer pipeline
├── data_schema/                # YAML schema definitions
├── valid_data/                 # Validated data samples
├── logs/                       # Application log files
└── templates/                  # Jinja2 HTML templates for prediction output
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+**
- **MongoDB** (local or Atlas cloud instance)
- **Git**

### 1. Clone the Repository

```bash
git clone https://github.com/its-me-meax/networksecurity.git
cd networksecurity
```

### 2. Create a Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
MONGODB_URL_KEY=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
MONGO_DB_URL=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
```

### 5. Load Data into MongoDB

```bash
python push_data.py
```

This reads `Network_Data/phisingData.csv`, converts it to JSON records, and inserts them into the `Pradyumansh.NetworkData` collection in MongoDB.

---

## 📖 Usage

### Run the Training Pipeline (CLI)

```bash
python main.py
```

This executes the full pipeline: **Ingestion → Validation → Transformation → Training**, and saves the best model to `final_model/`.

### Start the Web API

```bash
python app.py
```

The server starts at `http://0.0.0.0:8080`. Visit `http://localhost:8080` to be redirected to the interactive **Swagger docs**.

---

## 🤖 ML Pipeline Details

### Data Ingestion
- Connects to MongoDB and exports the `NetworkData` collection
- Splits data into **train** (80%) and **test** (20%) sets

### Data Validation
- Validates data against the schema defined in `data_schema/schema.yaml`
- Generates a **drift report** (`report.yaml`) to detect feature distribution changes

### Data Transformation
- Uses **KNN Imputer** (k=3, uniform weights) to handle missing values
- Saves the fitted preprocessor as a `.pkl` artifact

### Model Training
The system trains and compares **5 classification models** with hyperparameter tuning:

| Model                  | Tuned Hyperparameters                                  |
|------------------------|-------------------------------------------------------|
| **Random Forest**      | `n_estimators`: [8, 16, 32, 128, 256]                 |
| **Decision Tree**      | `criterion`: [gini, entropy, log_loss]                |
| **Gradient Boosting**  | `learning_rate`, `subsample`, `n_estimators`          |
| **Logistic Regression**| Default parameters                                     |
| **AdaBoost**           | `learning_rate`, `n_estimators`                       |

- The **best model** (by score) is selected automatically
- Evaluated using **F1 Score**, **Precision**, and **Recall**
- Minimum expected score threshold: **0.6**
- Overfitting/underfitting threshold: **0.05**

---

## 🌐 API Endpoints

| Method | Endpoint   | Description                                          |
|--------|-----------|------------------------------------------------------|
| `GET`  | `/`       | Redirects to Swagger API documentation (`/docs`)     |
| `GET`  | `/train`  | Triggers the full ML training pipeline               |
| `POST` | `/predict`| Upload a CSV file → get phishing predictions as HTML |

### Predict Endpoint Example

```bash
curl -X POST "http://localhost:8080/predict" \
  -F "file=@your_network_data.csv"
```

The response renders an HTML table with predictions appended as a `predicted_column` (0 = legitimate, 1 = phishing).

---

## 🐳 Docker Deployment

### Build the Image

```bash
docker build -t networksecurity .
```

### Run the Container

```bash
docker run -p 8080:8080 --env-file .env networksecurity
```

The API will be available at `http://localhost:8080`.

---

## 📊 Experiment Tracking

All training runs are tracked with **MLflow** via **DagsHub**:

- **Metrics logged**: F1 Score, Precision, Recall (for both train and test sets)
- **Models logged**: Best sklearn model is registered as `NetworkSecurityModel`
- **Dashboard**: [DagsHub MLflow UI](https://dagshub.com/its-me-meax/networksecurity.mlflow)

---

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/your-feature`)
3. **Commit** your changes (`git commit -m 'Add your feature'`)
4. **Push** to the branch (`git push origin feature/your-feature`)
5. **Open** a Pull Request

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Pradyuman Sharma** — [@its-me-meax](https://github.com/its-me-meax)
