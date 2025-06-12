# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, send_file, jsonify
import pandas as pd
import logging

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

            if education_level == 'bak_spec':
                model, threshold, features = model_bak, threshold_bak, features_bak_spec
            else:
                model, threshold, features = model_mag, threshold_mag, features_mag

            logger.info(f"{education_level}")
            logger.info(f"Обработка для уровня образования: {education_level}")

            form_data = collect_form_data(request.form, education_level, features_mag, features_bak_spec)
            df = pd.DataFrame([form_data])
            df_prepared = prepare_data(df, education_level, features_mag, features_bak_spec)

            if 'file' in request.files:
                file = request.files['file']
                if file.filename != '':
                    df = pd.read_csv(file)
                    df['education_level'] = education_level
                    result = make_prediction(df_prepared, model, threshold, features)
                    save_results(df_prepared, result)

                    return render_template('prediction.html',
                               show_results=True,
                               probability=result['probability'],
                               recommendation=result['recommendation'],
                               error=None)

            logger.info(f"data{form_data}")

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