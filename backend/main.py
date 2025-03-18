"""
Модель прогнозирования ключевой ставки ЦБ РФ
Версия 1.0
"""

import warnings
import optuna
import yaml

import uvicorn
from fastapi import FastAPI
from fastapi import File
from pydantic import BaseModel

from src.pipelines.pipeline import pipeline_training, pipeline_training_future
from src.data.get_metrics import load_dict_metrics
from src.data.get_data import get_dataset

warnings.filterwarnings('ignore')
optuna.logging.set_verbosity(optuna.logging.WARNING)

# переменная для запуска приложения
app = FastAPI()
CONFIG_PATH = '../config/params.yml'


# @app.get("/Hello")
# def welcome():
#     """
#     Hello!
#     return: None
#     """
#     return {"message": "Hello World"}

@app.post("/train_test")
def train_test():
    """
    Train test model, logging metrics
    return: None
    """
    with open(CONFIG_PATH, encoding='utf-8') as file:
        config = yaml.load(file, Loader=yaml.FullLoader)
    dict_metrics_path = config['train']['dict_metrics_path']
    pipeline_training(config_path=CONFIG_PATH)
    dict_metrics = load_dict_metrics(dict_metrics_path)
    return {"message": "Model trained", "metrics": dict_metrics}

@app.post("/train_future")
def train_future():
    """
    Train future model
    return: None
    """
    with open(CONFIG_PATH, encoding='utf-8') as file:
        config = yaml.load(file, Loader=yaml.FullLoader)
    pipeline_training_future(config_path=CONFIG_PATH)
    return {"message": "Model trained"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
