# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, send_file, jsonify
import pandas as pd
import logging
import uuid

from app_func import load_models, load_rank_data, make_prediction, save_results
from csv_func import collect_form_data, prepare_data


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


@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'POST':
        try:
            education_level = request.form.get('education_level')
            logger.info(f"Обработка для уровня образования: {education_level}")

            if education_level == 'bak_spec':
                model, threshold, features = model_bak, threshold_bak, features_bak_spec
            else:
                model, threshold, features = model_mag, threshold_mag, features_mag

            if 'file' in request.files:
                file = request.files['file']
                if file.filename != '':
                    df = pd.read_csv(file)
                    return process_student_csv(df, education_level, model, threshold, features)

            form_data = collect_form_data(request.form, education_level, features_mag, features_bak_spec)
            df = pd.DataFrame([form_data])
            df_prepared = prepare_data(df, education_level, features_mag, features_bak_spec)
            result = make_prediction(df_prepared, model, threshold, features)

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

def process_student_csv(df: pd.DataFrame, education_level: str, model, threshold, features):
    try:
        student_groups = df.groupby('id')
        
        results = []
        for student_id, group in student_groups:
            student_data = group.iloc[0].to_dict()
            subjects = []
            for _, row in group.iterrows():
                subjects.append({
                    "subject_name": row.get("subject_name", ""),
                    "subject_grade": row.get("subject_grade", ""),
                    "subject_score": row.get("subject_score", ""),
                    "subject_retakes": row.get("subject_retakes", 0)
                })
            
            student_data[f"{'m_' if education_level == 'magistr' else 'b_'}_subject_name[]"] = [s["subject_name"] for s in subjects]
            student_data[f"{'m_' if education_level == 'magistr' else 'b_'}_subject_grade[]"] = [s["subject_grade"] for s in subjects]
            student_data[f"{'m_' if education_level == 'magistr' else 'b_'}_subject_score[]"] = [s["subject_score"] for s in subjects]
            student_data[f"{'m_' if education_level == 'magistr' else 'b_'}_subject_retakes[]"] = [s["subject_retakes"] for s in subjects]
            
            form_data = collect_form_data(student_data, education_level, features_mag, features_bak_spec)
            df_student = pd.DataFrame([form_data])
            df_prepared = prepare_data(df_student, education_level, features_mag, features_bak_spec)
            
            result = make_prediction(df_prepared, model, threshold, features)
            
            results.append({
                'id': student_id,
                'probability': result['probability'],
                'recommendation': result['recommendation'],
                **student_data  
            })
        
        results_df = pd.DataFrame(results)
        results_df.to_csv('results.csv', index=False)
        
        first_result = results[0] if results else {}
        return render_template('prediction.html',
                           show_results=True,
                           probability=first_result.get('probability', 0),
                           recommendation=first_result.get('recommendation', ''),
                           error=None)

    except Exception as e:
        logger.error(f"Ошибка обработки CSV: {e}", exc_info=True)
        return render_template('prediction.html',
                           show_results=False,
                           error=f"Ошибка обработки CSV: {e}")


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