from networksecurity.components.data_ingestion import DataIngestion
from networksecurity.components.data_validation import DataValidation
from networksecurity.components.data_transformation import DataTransformation
from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging
from networksecurity.entity.config_entity import DataIngestionConfig,DataValidationConfig,DataTransformationConfig
from networksecurity.entity.config_entity import TrainingPipelineConfig

from networksecurity.components.model_trainer import ModelTrainer
from networksecurity.entity.config_entity import ModelTrainerConfig
 

import sys
import argparse

if __name__=='__main__':
    parser = argparse.ArgumentParser(description="Network Security Pipeline")
    parser.add_argument("--push-data", action="store_true", help="Push local CSV data to MongoDB")
    parser.add_argument("--train", action="store_true", help="Run the full training pipeline")
    args = parser.parse_args()

    try:
        if args.push_data:
            logging.info("Starting data push to MongoDB...")
            from push_data import NetworkDataExtract
            networkobj = NetworkDataExtract()
            records = networkobj.csv_to_json_convertor(file_path=r"Network_Data\phisingData.csv")
            no_of_records = networkobj.insert_data_mongodb(records, "Pradyumansh", "NetworkData")
            logging.info(f"Successfully inserted {no_of_records} records into MongoDB.")
            print(f"Successfully inserted {no_of_records} records into MongoDB.")

        if args.train or not args.push_data:
            trainingpipelineconfig=TrainingPipelineConfig()
            dataingestionconfig=DataIngestionConfig(trainingpipelineconfig)
            data_ingestion=DataIngestion(dataingestionconfig)
            logging.info("Initiate the data ingestion")
            dataingestionartifact=data_ingestion.initiate_data_ingestion()
            logging.info("Data Initiation Completed")
            print(dataingestionartifact)
            data_validation_config=DataValidationConfig(trainingpipelineconfig)
            data_validation=DataValidation(dataingestionartifact,data_validation_config)
            logging.info("Initiate the data Validation")
            data_validation_artifact=data_validation.initiate_data_validation()
            logging.info("data Validation Completed")
            print(data_validation_artifact)
            data_transformation_config=DataTransformationConfig(trainingpipelineconfig)
            logging.info("data Transformation started")
            data_transformation=DataTransformation(data_validation_artifact,data_transformation_config)
            data_transformation_artifact=data_transformation.initiate_data_transformation()
            print(data_transformation_artifact)
            logging.info("data Transformation completed")

            logging.info("Model Training started")
            model_trainer_config=ModelTrainerConfig(trainingpipelineconfig)
            model_trainer=ModelTrainer(model_trainer_config=model_trainer_config,data_transformation_artifact=data_transformation_artifact)
            model_trainer_artifact=model_trainer.initiate_model_trainer()

            logging.info("Model Training artifact created")
        
        
        
    except Exception as e:
           raise NetworkSecurityException(e,sys)
