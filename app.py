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


try:
    (model_bak, threshold_bak, features_bak_spec,
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
            logger.info(f"{education_level}")
            logger.info(f"Обработка для уровня образования: {education_level}")

            if 'file' in request.files:
                file = request.files['file']
                if file.filename != '':
                    df = pd.read_csv(file)
                    df['education_level'] = education_level
                    return process_csv(df, education_level)

            form_data = collect_form_data(request.form, education_level)
            logger.info(f"data{form_data}")
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


from collections import OrderedDict


def collect_form_data(form: Dict, level: str) -> Dict:
    """Собирает данные из формы в словарь с нужными фичами, сохраняя порядок колонок"""

    logger.info(f"form {form}")

    if level == 'magistr':
        columns_order = features_mag
    else:  # bak_spec
        columns_order = features_bak_spec
    
    data = OrderedDict()
    
    for col in columns_order:
        data[col] = None 


    data['Приоритет'] = int(form.get('priority', 1))
    data['Cумма баллов испытаний'] = int(form.get('exam_score', 0))
    data['Балл за инд. достижения'] = int(form.get('achievement', 0))
    data['Контракт'] = int(form.get('contract', 0))
    data['Нуждается в общежитии'] = int(form.get('dormitory', 0))
    data['Иностранный абитуриент (МОН)'] = int(form.get('foreign', 0))
    data['Пол'] = int(form.get('gender', 0))
    data['Полных лет на момент поступления'] = int(form.get('age', 15))
    data['fromEkaterinburg'] = int(form.get('city', 0))
    data['fromSverdlovskRegion'] = int(form.get('region', 0))
    
    country = form.get('country', 'Российская Федерация')
    data['PostSoviet'] = 1 if country in ['Республика Беларусь', 'Республика Казахстан', 'Республика Армения', 
                                        'Республика Азербайджан', 'Республика Молдова', 'Республика Узбекистан',
                                        'Республика Таджикистан', 'Туркменистан', 'Киргизская Республика', 'Украина'] else 0
    data['others'] = 1 if country not in ['Российская Федерация', 'Республика Беларусь', 'Республика Казахстан'] else 0
    
    competition = form.get('competition', 'Основные места')
    data['Особая квота'] = 1 if competition == 'Особая квота' else 0
    data['Отдельная квота'] = 1 if competition == 'Отдельная квота' else 0
    data['Целевая квота'] = 1 if competition == 'Целевая квота' else 0
    
    form_type = form.get('form', 'Очная')
    data['Заочная'] = 1 if form_type == 'Заочная' else 0
    data['Очно-заочная'] = 1 if form_type == 'Очно-заочная' else 0
    
    benefit = form.get('benefit', 'Нет')
    data['Боевые действия'] = 1 if benefit == 'Боевые действия' else 0
    data['Инвалиды'] = 1 if benefit == 'Инвалиды' else 0
    data['Квота для иностранных граждан'] = 1 if benefit == 'Квота для иностранных граждан' else 0
    data['Сироты'] = 1 if benefit == 'Сироты' else 0
    
    direction = form.get('direction', '00.00.00')
    data['Код направления 1: 10'] = 1 if direction.startswith('10') else 0
    data['Код направления 1: 11'] = 1 if direction.startswith('11') else 0
    data['Код направления 1: 27'] = 1 if direction.startswith('27') else 0
    data['Код направления 1: 29'] = 1 if direction.startswith('29') else 0
    data['Код направления 3: 2'] = 1 if direction.endswith('02') else 0
    data['Код направления 3: 3'] = 1 if direction.endswith('03') else 0
    data['Код направления 3: 4'] = 1 if direction.endswith('04') else 0
    
    if level == 'bak_spec':
        data['БВИ'] = int(form.get('bvi', 0))
        
        olympiad = form.get('olympiad', 'Не писал')
        data['всероссийская олимпиада школьников (ВОШ)'] = 1 if olympiad == 'ВОШ' else 0
        data['олимпиада из перечня, утвержденного МОН РФ (ОШ)'] = 1 if olympiad == 'ОШ' else 0
        
        level_type = form.get('level', 'Бакалавр')
        data['Специалист'] = 1 if level_type == 'Специалист' else 0
        
        institution = form.get('institution', 'Школа')
        data['Военное уч. заведение'] = 1 if institution == 'Военное учебное заведение' else 0
        data['Высшее'] = 1 if institution == 'Высшее' else 0
        data['Профильная Школа'] = 1 if institution == 'Профильная школа' else 0
        data['СПО'] = 1 if institution == 'СПО' else 0
    else:  
        data['всероссийская олимпиада школьников (ВОШ)'] = 0
        data['олимпиада из перечня, утвержденного МОН РФ (ОШ)'] = 0
        data['Военное уч. заведение'] = 0
        data['Высшее'] = 1
        data['Профильная Школа'] = 0
        data['СПО'] = 0
    
    subject_prefix = 'b_' if level == 'bak_spec' else 'm_'
    subject_names = form.getlist(f'{subject_prefix}subject_name[]')
    subject_grades = form.getlist(f'{subject_prefix}subject_grade[]')
    subject_scores = form.getlist(f'{subject_prefix}subject_score[]')
    subject_retakes = form.getlist(f'{subject_prefix}subject_retakes[]')
    
    total_retakes = 0
    total_debts = 0
    
    for i in range(len(subject_names)):
        grade = subject_grades[i]
        retakes = int(subject_retakes[i])
        
        total_retakes += retakes

        if grade in ['Незачёт', 'Недопуск', 'Недосдал', 'Неуважительная причина', '2']:
            total_debts += 1
    
    data['Общее количество пересдач'] = total_retakes
    data['Общее количество долгов'] = total_debts
    
    data['Позиция студента в рейтинге'] = 0
    data['Human Development Index'] = 0
    logger.info(f"ghjn{data}")
    return data


def prepare_data(df: pd.DataFrame, level: str) -> pd.DataFrame:
    if level == 'bak_spec':
        required_features = features_bak_spec
    else:
        required_features = features_mag

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

    for col in required_features:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        else:
            df[col] = 0

    df = df[required_features]

    logger.info(f"Подготовленные признаки: {list(df.columns)}")

    return df


def make_prediction(df: pd.DataFrame, level: str) -> Dict:
    if level == 'bak_spec':
        model, threshold, features = model_bak, threshold_bak, features_bak_spec
    else:
        model, threshold, features = model_mag, threshold_mag, features_mag

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

    recommendation = "Рекомендуется" if probability >= threshold else "Не рекомендуется"

    logger.info(f"Вероятность: {probability}, решение: {recommendation}")

    return {'probability': probability, 'recommendation': recommendation}


def save_results(df: pd.DataFrame, result: Dict):
    df_copy = df.copy()
    df_copy['Вероятность'] = result['probability']
    df_copy['Рекомендация'] = result['recommendation']
    df_copy.to_csv('results.csv', index=False)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005, debug=True)