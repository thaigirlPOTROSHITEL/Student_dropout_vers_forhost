# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, send_file, jsonify
import pandas as pd
import joblib
import pickle
import json
import logging
from typing import Dict

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BAK_FEATURES = ['Приоритет', 'Cумма баллов испытаний', 'БВИ', 'Балл за инд. достижения', 'Контракт', 'Нуждается в общежитии', 'Иностранный абитуриент (МОН)', 'Пол', 'Полных лет на момент поступления', 'Общее количество пересдач', 'Общее количество долгов', 'fromEkaterinburg', 'fromSverdlovskRegion', 'Human Development Index', 'Особая квота', 'Отдельная квота', 'Целевая квота', 'всероссийская олимпиада школьников (ВОШ)', 'олимпиада из перечня, утвержденного МОН РФ (ОШ)', 'Заочная', 'Очно-заочная', 'Специалист', 'Военное уч. заведение', 'Высшее', 'Профильная Школа', 'СПО', 'Боевые действия', 'Инвалиды', 'Квота для иностранных граждан', 'Сироты', 'PostSoviet', 'others', 'Код направления 1: 10', 'Код направления 1: 11', 'Код направления 1: 27', 'Код направления 1: 29', 'Код направления 3: 2', 'Код направления 3: 3', 'Код направления 3: 4', 'Позиция студента в рейтинге']


MAG_FEATURES = ['Приоритет', 'Cумма баллов испытаний', 'Балл за инд. достижения', 'Контракт', 'Нуждается в общежитии', 'Иностранный абитуриент (МОН)', 'Пол', 'Полных лет на момент поступления', 'Общее количество пересдач', 'Общее количество долгов', 'fromEkaterinburg', 'fromSverdlovskRegion', 'Human Development Index', 'Особая квота', 'Отдельная квота', 'Целевая квота', 'всероссийская олимпиада школьников (ВОШ)', 'олимпиада из перечня, утвержденного МОН РФ (ОШ)', 'Заочная', 'Очно-заочная', 'Военное уч. заведение', 'Высшее', 'Профильная Школа', 'СПО', 'Боевые действия', 'Инвалиды', 'Квота для иностранных граждан', 'Сироты', 'PostSoviet', 'others', 'Код направления 1: 10', 'Код направления 1: 11', 'Код направления 1: 27', 'Код направления 1: 29', 'Код направления 3: 2', 'Код направления 3: 3', 'Код направления 3: 4', 'Позиция студента в рейтинге']

# Загрузка моделей
def load_models():
    try:
        # Бакалавриат/специалитет
        model_bak = joblib.load('models/rf_model_s_bak_spec_mah.joblib')

        with open('models/rf_model_s_bak_spec_mah_config.json', 'r') as f:
            config_bak = json.load(f)
        with open('models/rf_model_s_bak_spec_mah_columns.pkl', 'rb') as f:
            features_bak = pickle.load(f)

        # Магистратура
        model_mag = joblib.load('models/linear_model_nystroem_s_magistr_lof.joblib')
        with open('models/linear_model_nystroem_s_magistr_lof_config.json', 'r') as f:
            config_mag = json.load(f)
        with open('models/linear_model_nystroem_s_magistr_lof_columns.pkl', 'rb') as f:
            features_mag = pickle.load(f)
        

        return (model_bak, config_bak['threshold'], features_bak,
                model_mag, config_mag['threshold'], features_mag)
    except Exception as e:
        logger.error(f"Ошибка загрузки моделей: {e}")
        raise

# Загрузка данных для рангов (если нужны)
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

# Инициализация
try:
    (model_bak, threshold_bak, features_bak,
     model_mag, threshold_mag, features_mag) = load_models()
    stats_mag, penalties_mag, stats_bak, penalties_bak = load_rank_data()
except Exception as e:
    logger.critical(f"Ошибка инициализации: {e}")
    exit(1)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/team')
def team():
    return render_template('team.html')

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'POST':
        try:
            education_level = request.form.get('education_level')
            logger.info(f"Обработка для уровня образования: {education_level}")

            # Если пришёл файл CSV
            if 'file' in request.files:
                file = request.files['file']
                if file.filename != '':
                    df = pd.read_csv(file)
                    # Добавляем колонку с уровнем образования, если нужно
                    df['education_level'] = education_level
                    return process_csv(df, education_level)

            # Обработка формы вручную
            form_data = collect_form_data(request.form, education_level)
            df = pd.DataFrame([form_data])
            df_prepared = prepare_data(df, education_level)
            result = make_prediction(df_prepared, education_level)

            return render_template('prediction.html',
                                   show_results=True,
                                   probability=result['probability'],
                                   recommendation=result['recommendation'],
                                   error=None)

        except Exception as e:
            logger.error(f"Ошибка при обработке запроса: {e}", exc_info=True)
            return render_template('prediction.html',
                                   show_results=False,
                                   error=f"Ошибка обработки: {e}")

    return render_template('prediction.html', show_results=False, error=None)

def process_csv(df: pd.DataFrame, education_level: str):
    """Обрабатывает CSV и возвращает результат"""
    try:
        df_prepared = prepare_data(df, education_level)
        result = make_prediction(df_prepared, education_level)
        save_results(df_prepared, result)

        return render_template('prediction.html',
                               show_results=True,
                               probability=result['probability'],
                               recommendation=result['recommendation'],
                               error=None)
    except Exception as e:
        raise ValueError(f"Ошибка обработки CSV: {e}")

@app.route('/download_results')
def download_results():
    try:
        return send_file('results.csv',
                         mimetype='text/csv',
                         as_attachment=True,
                         download_name='predictions.csv')
    except Exception as e:
        logger.error(f"Ошибка скачивания файла: {e}")
        return jsonify({'error': str(e)}), 500

def collect_form_data(form: Dict, level: str) -> Dict:
    """Собирает данные из формы в словарь с нужными фичами"""
    features = BAK_FEATURES if level == 'bak_spec' else MAG_FEATURES
    data = {}

    for feature in features:
        value = form.get(feature, 0)
        # Обработка checkbox (on/off)
        if value in ['on', 'off']:
            value = 1 if value == 'on' else 0
        # Преобразуем числа, если можно
        try:
            if '.' in str(value):
                value = float(value)
            else:
                value = int(value)
        except:
            pass
        data[feature] = value

    return data

def prepare_data(df: pd.DataFrame, level: str) -> pd.DataFrame:
    if level == 'bak_spec':
        required_features = list(model_bak.feature_names_in_)
    else:
        required_features = list(model_mag.feature_names_in_)

    df_features = set(df.columns)
    model_features = set(required_features)

    missing_in_df = model_features - df_features
    extra_in_df = df_features - model_features

    if missing_in_df:
        error_msg = f"В данных отсутствуют признаки, нужные модели: {missing_in_df}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    if extra_in_df:
        logger.warning(f"В данных есть лишние признаки, не используемые моделью: {extra_in_df}")

    # Приводим необходимые признаки к числовому типу, заполняем пропуски нулями
    for col in required_features:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        else:
            df[col] = 0

    # Оставляем только необходимые признаки
    df = df[required_features]

    logger.info(f"Подготовленные признаки: {list(df.columns)}")

    return df



def make_prediction(df: pd.DataFrame, level: str) -> Dict:
    """Делает предсказание на основе модели"""
    if level == 'bak_spec':
        model, threshold, features = model_bak, threshold_bak, features_bak
    else:
        model, threshold, features = model_mag, threshold_mag, features_mag

    missing = set(features) - set(df.columns)
    if missing:
        raise ValueError(f"Отсутствуют обязательные фичи: {missing}")

    # Предсказание вероятности
    if hasattr(model, 'predict_proba'):
        proba = model.predict_proba(df[features])[:, 1]
    else:
        # Если модель не поддерживает predict_proba, используем predict (регрессия)
        proba = model.predict(df[features])

    # Если это несколько строк, усредняем
    if len(proba) > 1:
        probability = float(proba.mean())
    else:
        probability = float(proba[0])

    recommendation = "Рекомендуется" if probability >= threshold else "Не рекомендуется"

    logger.info(f"Вероятность: {probability}, решение: {recommendation}")

    return {'probability': probability, 'recommendation': recommendation}

def save_results(df: pd.DataFrame, result: Dict):
    """Сохраняет результаты в CSV"""
    df_copy = df.copy()
    df_copy['Вероятность'] = result['probability']
    df_copy['Рекомендация'] = result['recommendation']
    df_copy.to_csv('results.csv', index=False)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005, debug=True)