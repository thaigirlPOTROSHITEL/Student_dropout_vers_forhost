# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, send_file, jsonify
import pandas as pd
import logging
import uuid
from werkzeug.datastructures import ImmutableMultiDict

from app_func import load_models, load_rank_data, make_prediction, save_results
from csv_func import collect_form_data, prepare_data, calculate_student_ranks


app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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


import io
from werkzeug.datastructures import FileStorage


@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'POST':
        try:
            education_level = request.form.get('education_level')
            if not education_level:
                return render_template('prediction.html',
                                       show_results=False,
                                       error="Не указан уровень образования")

            logger.info(f"Обработка для уровня образования: {education_level}")

            if education_level == 'bak_spec':
                model, threshold, features = model_bak, threshold_bak, features_bak_spec
            else:
                model, threshold, features = model_mag, threshold_mag, features_mag

            if 'file' in request.files:
                file = request.files['file']
                if file.filename != '':
                    try:
                        encodings = ['utf-8', 'cp1251', 'latin1', 'iso-8859-1']
                        df = None
                        for encoding in encodings:
                            try:
                                file.seek(0)
                                df = pd.read_csv(io.StringIO(file.read().decode(encoding)), sep=';')
                                break
                            except UnicodeDecodeError:
                                continue

                        if df is None:
                            raise ValueError("Не удалось прочитать файл. Проверьте кодировку")

                        logger.error(f"Ошибка при обработке файла: {df}")

                        if education_level == 'magistr':
                            df['Уровень подготовки'] = 'Магистр'
                        else:
                            df['Уровень подготовки'] = 'Бакалавр'

                        df = process_student_csv(df, education_level, features_mag, features_bak_spec)
                        df_prepared = prepare_data(df, education_level, features_mag, features_bak_spec)

                        logger.info(f"DATASET: {df_prepared}")

                        result = make_prediction_csv(df_prepared, model, threshold, features)

                        logger.error(f"RESULT!!!!!!!!!!!!!!!!!!!!!!!!!!!!!: {result}")

                        output = io.StringIO()
                        result.to_csv(output, index=False, sep=';')

                        mem = io.BytesIO()
                        mem.write(output.getvalue().encode('utf-8'))
                        mem.seek(0)

                        return send_file(
                            mem,
                            mimetype='text/csv',
                            as_attachment=True,
                            download_name='predictions.csv'
                        )

                    except Exception as e:
                        logger.error(f"Ошибка при обработке файла: {e}")
                        return render_template('prediction.html',
                                               show_results=False,
                                               error=f"Ошибка обработки файла: {str(e)}")

            form_data = collect_form_data(request.form, education_level, features_mag, features_bak_spec)
            df = pd.DataFrame([form_data])
            df_prepared = prepare_data(df, education_level, features_mag, features_bak_spec)

            result = make_prediction(df_prepared, model, threshold, features)

            return render_template('prediction.html',
                      active_tab=education_level, 
                      show_results=True,
                      probability=result['probability'],
                      recommendation=result['recommendation'])
        except Exception as e:
            logger.error(f"Непредвиденная ошибка: {e}")
            return render_template('prediction.html',
                                   show_results=False,
                                   error=f"Произошла непредвиденная ошибка: {str(e)}")

    return render_template('prediction.html', show_results=False, error=None)


def process_student_csv(df: pd.DataFrame, education_level: str, features_mag, features_bak_spec):
    try:
        column_mapping = {
            'Наименование дисциплины': 'subject_name',
            'Оценка': 'subject_grade',
            'Баллы': 'subject_score',
            'Количество пересдач': 'subject_retakes'
        }
        df = df.rename(columns=column_mapping)

        student_groups = df.groupby('id_студента')
        processed_data = []

        for student_id, group in student_groups:
            student_data = group.iloc[0].to_dict()

            prefix = 'm_' if education_level == 'magistr' else 'b_'
            subjects = {
                f"{prefix}subject_name[]": [],
                f"{prefix}subject_grade[]": [],
                f"{prefix}subject_score[]": [],
                f"{prefix}subject_retakes[]": []
            }

            for _, row in group.iterrows():
                subjects[f"{prefix}subject_name[]"].append(str(row.get("subject_name", "")))
                subjects[f"{prefix}subject_grade[]"].append(str(row.get("subject_grade", "")))
                subjects[f"{prefix}subject_score[]"].append(str(row.get("subject_score", "")))
                subjects[f"{prefix}subject_retakes[]"].append(str(row.get("subject_retakes", 0)))

            full_data = {**student_data, **subjects}

            multidict_data = []
            for key, value in full_data.items():
                if isinstance(value, list):
                    for item in value:
                        multidict_data.append((key, item))
                else:
                    multidict_data.append((key, value))

            form_input = ImmutableMultiDict(multidict_data)

            form_data = collect_form_data(form_input, education_level, features_mag, features_bak_spec)
            processed_data.append({
                'id_студента': student_id,
                **form_data
            })

        return pd.DataFrame(processed_data)

    except Exception as e:
        logger.error(f"Ошибка обработки CSV: {e}", exc_info=True)
        raise


def make_prediction_csv(df: pd.DataFrame, model, threshold: float, features: list):
    missing = set(features) - set(df.columns)
    if missing:
        raise ValueError(f"Отсутствуют обязательные фичи: {missing}")

    if hasattr(model, 'predict_proba'):
        proba = model.predict_proba(df[features])[:, 1]
    else:
        proba = model.predict(df[features])

    result_df = pd.DataFrame({
        'id': df.index if 'id' not in df.columns else df['id'],
        'probability': (proba * 100).round(2),
        'above_threshold': proba >= threshold
    })

    return result_df

from flask import send_from_directory

@app.route('/download_example/<education_level>')
def download_example(education_level):
    try:
        if education_level == 'magistr':
            filename = 'example_magistr.csv'
        elif education_level == 'bak_spec':
            filename = 'example_bak_spec.csv'
        else:
            return jsonify({'error': 'Invalid education level'}), 400

        return send_from_directory(
            'static/examples',
            filename,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f"Ошибка при скачивании примера CSV: {e}")
        return jsonify({'error': str(e)}), 500
    
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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005, debug=True)