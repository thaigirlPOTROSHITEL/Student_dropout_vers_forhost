import joblib
import json
import pickle
import pandas as pd
import logging
from typing import Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_models():
    try:
        model_bak = joblib.load('models/rf_model_s_bak_spec_mah.joblib')
        with open('models/rf_model_s_bak_spec_mah_config.json', 'r') as f:
            config_bak = json.load(f)
        with open('models/rf_model_s_bak_spec_mah_columns.pkl', 'rb') as f:
            features_bak_spec = pickle.load(f)

        model_mag = joblib.load('models/linear_model_nystroem_s_magistr_lof.joblib')
        with open('models/linear_model_nystroem_s_magistr_lof_config.json', 'r') as n:
            config_mag = json.load(n)
        with open('models/linear_model_nystroem_s_magistr_lof_columns.pkl', 'rb') as n:
            features_mag = pickle.load(n)
            logger.info(f"mag {features_mag}")

        return (model_bak, config_bak['threshold'], features_bak_spec,
                model_mag, config_mag['threshold'], features_mag)

    except Exception as e:
        logger.error(f"Ошибка загрузки моделей: {e}")
        raise


def load_rank_data():
    try:
        with open('models/subject_stats_magistr.pkl', 'rb') as f:
            stats_mag = pickle.load(f)
        with open('models/sorted_penalties_magistr.pkl', 'rb') as f:
            penalties_mag = pickle.load(f)

        with open('models/subject_stats_bak_spec.pkl', 'rb') as f:
            stats_bak = pickle.load(f)
        with open('models/sorted_penalties_bak_spec.pkl', 'rb') as f:
            penalties_bak = pickle.load(f)

        return stats_mag, penalties_mag, stats_bak, penalties_bak

    except Exception as e:
        logger.error(f"Ошибка загрузки данных рангов: {e}")
        raise


def make_prediction(df: pd.DataFrame, model, threshold, features) -> Dict:
    missing = set(features) - set(df.columns)
    if missing:
        raise ValueError(f"Отсутствуют обязательные фичи: {missing}")

    if hasattr(model, 'predict_proba'):
        proba = model.predict_proba(df[features])[:, 1]
    else:
        proba = model.predict(df[features])

    if len(proba) > 1:
        probability = float(proba.mean())
    else:
        probability = float(proba[0])

    recommendation = "more" if probability >= threshold else "less"

    logger.info(f"Вероятность: {probability}, решение: {recommendation}")

    return {'probability': round(probability * 100, 2), 'recommendation': recommendation}


def save_results(df: pd.DataFrame, result: Dict):
    df_copy = df.copy()
    df_copy['Вероятность'] = result['probability']
    df_copy['Рекомендация'] = result['recommendation']
    df_copy.to_csv('results.csv', index=False)