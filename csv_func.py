import pandas as pd
from collections import OrderedDict
from typing import Dict
import logging
import bisect
import pickle
import math
import uuid


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HDI_DICT = {
    'Арабская Республика Египет': 0.731,
    'Габонская Республика': 0.706,
    'Йеменская Республика': 0.455,
    'Киргизская Республика': 0.692,
    'Китайская Народная Республика': 0.768,
    'Королевство Марокко': 0.683,
    'Народная Республика Бангладеш': 0.661,
    'Республика Азербайджан': 0.745,
    'Республика Армения': 0.759,
    'Республика Беларусь': 0.808,
    'Республика Гаити': 0.535,
    'Республика Индонезия': 0.705,
    'Республика Ирак': 0.686,
    'Республика Казахстан': 0.811,
    'Республика Камерун': 0.576,
    'Республика Колумбия': 0.752,
    "Республика Кот д'Ивуар": 0.550,
    'Республика Куба': 0.764,
    'Республика Молдова': 0.767,
    'Республика Перу': 0.762,
    'Республика Судан': 0.508,
    'Республика Таджикистан': 0.685,
    'Республика Узбекистан': 0.727,
    'Российская Федерация': 0.822,
    'Сирийская Арабская Республика': 0.577,
    'Социалистическая Республика Вьетнам': 0.703,
    'Турецкая Республика': 0.838,
    'Туркменистан': 0.745,
    'Украина': 0.773,
    'Федеративная Демократическая Республика Эфиопия': 0.498,
    'Федеративная Республика Бразилия': 0.754,
    'Федеративная Республика Германия': 0.942,
    'Федеративная Республика Нигерия': 0.535
}
IS_NA = {'зач.': 70, 'неуваж.': 0, 'недсд.': 0, '4': 70, 'недоп.': 0, '5': 90, 'незач.': 20, '2': 20, '3': 50}


def get_student_rank(student_penalty, sorted_penalties):
    pos = bisect.bisect_right(sorted_penalties, student_penalty)
    return pos + 1


def power_penalty_score(student_scores, subject_stats, p=2.0):
    total_score = 0
    subject_count = 0

    for subject, student_score in student_scores.items():
        if subject not in subject_stats:
            continue

        stats = subject_stats[subject]
        mean_clean = stats['mean_clean']
        fail_ratio = stats['fail_ratio']

        if student_score < 40:
            multiplier = 1 + math.log(1 / (fail_ratio + 1e-6))
            adjusted = (mean_clean ** p) * multiplier
        else:
            delta = mean_clean - student_score
            adjusted = math.copysign(abs(delta) ** p, delta) * fail_ratio

        total_score += adjusted
        subject_count += 1

    return total_score / subject_count if subject_count else 0.0


def calculate_student_ranks(df):
    """
    Принимает DataFrame с данными студентов и возвращает словарь:
    {
        "UUID студента": ранг студента
    }
    """

    def sep_dataset_local(df):
        bak_spec_mask = df["Уровень подготовки"].isin(["Бакалавр", "Специалист"])
        magistr_mask = df["Уровень подготовки"] == "Магистр"
        bak_spec = df[bak_spec_mask].copy()
        magistr = df[magistr_mask].copy()
        return bak_spec, magistr

    def group_students(df):
        student_groups = {}
        for _, row in df.iterrows():
            student = row["UUID студента"]
            subject = row["Наименование дисциплины"]
            if pd.isna(row["Балл"]):
                grade = row["Оценка"]
                score = IS_NA.get(grade, 0)
            else:
                score = row["Балл"]
            if student not in student_groups:
                student_groups[student] = {}
            student_groups[student][subject] = score
        return student_groups

    with open('models/subject_stats_magistr.pkl', 'rb') as f:
        stats_magistr = pickle.load(f)
    with open('models/sorted_penalties_magistr.pkl', 'rb') as f:
        sorted_penalties_magistr = pickle.load(f)

    with open('models/subject_stats_bak_spec.pkl', 'rb') as f:
        stats_bak_spec = pickle.load(f)
    with open('models/sorted_penalties_bak_spec.pkl', 'rb') as f:
        sorted_penalties_bak_spec = pickle.load(f)

    bak_spec_df, magistr_df = sep_dataset_local(df)

    ranks = {}

    magistr_students = group_students(magistr_df)
    for student, scores in magistr_students.items():
        penalty = power_penalty_score(scores, stats_magistr)
        logger.info(f"ШТРАФ{penalty}")
        rank = get_student_rank(penalty, sorted_penalties_magistr)
        ranks[student] = rank

    bak_spec_students = group_students(bak_spec_df)
    for student, scores in bak_spec_students.items():
        penalty = power_penalty_score(scores, stats_bak_spec)
        logger.info(f"ШТРАФ{penalty}")
        rank = get_student_rank(penalty, sorted_penalties_bak_spec)
        ranks[student] = rank

    return ranks


def collect_form_data(form: Dict, education_level: str, features_mag, features_bak_spec) -> Dict:
    logger.info(f"form {form}")

    if education_level == 'magistr':
        columns_order = features_mag
    else:
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

    subject_prefix = 'b_' if education_level == 'bak_spec' else 'm_'
    subject_names = form.getlist(f'{subject_prefix}subject_name[]')
    subject_grades = form.getlist(f'{subject_prefix}subject_grade[]')
    subject_scores = form.getlist(f'{subject_prefix}subject_score[]')
    subject_retakes = form.getlist(f'{subject_prefix}subject_retakes[]')

    student_uuid = str(uuid.uuid4())
    student_level = 'Магистр' if education_level == 'magistr' else ('Специалист' if data.get('Специалист', 0) else 'Бакалавр')

    rows = []
    for i in range(len(subject_names)):
        grade = subject_grades[i] if i < len(subject_grades) else ''
        score = subject_scores[i] if i < len(subject_scores) else ''
        score_val = None
        try:
            score_val = float(score) if score.strip() != '' else None
        except ValueError:
            pass

        rows.append({
            "UUID студента": student_uuid,
            "Уровень подготовки": student_level,
            "Наименование дисциплины": subject_names[i],
            "Оценка": grade,
            "Балл": score_val
        })

    df_student = pd.DataFrame(rows)

    try:
        ranks = calculate_student_ranks(df_student)
        student_rank = next(iter(ranks.values())) if ranks else 1
        logger.info(f'!!!!!!!!!!!!!!!!!!!!!!!!!RANK!!!!!!!!!!!!!!!!!!!!!!!!!!!!!{str(student_rank)}')
    except Exception as e:
        logger.error(f"Ошибка при вычислении ранга: {e}")
        student_rank = 1

    data['Позиция студента в рейтинге'] = student_rank

    total_retakes = 0
    total_debts = 0
    for i in range(len(subject_names)):
        retakes = int(subject_retakes[i]) if i < len(subject_retakes) else 0
        grade = subject_grades[i] if i < len(subject_grades) else ''
        total_retakes += retakes
        if grade in ['Незачёт', 'Недопуск', 'Недосдал', 'Неуважительная причина', '2']:
            total_debts += 1

    data['Общее количество пересдач'] = total_retakes
    data['Общее количество долгов'] = total_debts
    data['Human Development Index'] = HDI_DICT.get(country, 0.0)

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