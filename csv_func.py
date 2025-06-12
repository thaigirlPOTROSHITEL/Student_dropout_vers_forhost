import pandas as pd
from collections import OrderedDict
from typing import Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def collect_form_data(form: Dict, education_level:str, features_mag, features_bak_spec) -> Dict:
    """Собирает данные из формы в словарь с нужными фичами, сохраняя порядок колонок"""

    logger.info(f"form {form}")

    if education_level == 'magistr':
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
                                          'Республика Таджикистан', 'Туркменистан', 'Киргизская Республика',
                                          'Украина'] else 0
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

    if education_level == 'bak_spec':
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

    subject_prefix = 'b_' if education_level == 'bak_spec' else 'm_'
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


def prepare_data(df: pd.DataFrame, education_level: str, features_mag, features_bak_spec) -> pd.DataFrame:
    if education_level == 'bak_spec':
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