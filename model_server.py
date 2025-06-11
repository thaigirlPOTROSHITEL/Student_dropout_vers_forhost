from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import pandas as pd
import numpy as np
import logging
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    model_magistr = joblib.load('models/linear_model_nystroem_s_magistr_lof.joblib')
    model_bak_spec = joblib.load('models/rf_model_s_bak_spec_mah.joblib')
    logger.info("Модели успешно загружены")
except Exception as e:
    logger.error(f"Ошибка загрузки моделей: {str(e)}")
    raise

FEATURE_COLUMNS = [
    'Приоритет', 'Cумма баллов испытаний', 'БВИ', 'Балл за инд. достижения',
       'Категория конкурса БВИ', 'Контракт', 'Нуждается в общежитии',
       'Иностранный абитуриент (МОН)', 'Пол',
       'Полных лет на момент поступления',
       'Прошло лет с окончания уч. заведения', 'fromEkaterinburg',
       'fromSverdlovskRegion', 'Human Development Index', 'Особая квота',
       'Отдельная квота', 'Целевая квота',
       'всероссийская олимпиада школьников (ВОШ)',
       'олимпиада из перечня, утвержденного МОН РФ (ОШ)', 'Заочная',
       'Очно-заочная', 'Специалист', 'Военное уч. заведение', 'Высшее',
       'Профильная Школа', 'СПО', 'Боевые действия', 'Инвалиды',
       'Квота для иностранных граждан', 'Сироты', 'PostSoviet', 'others',
       'Код направления 1: 10', 'Код направления 1: 11',
       'Код направления 1: 27', 'Код направления 1: 29',
       'Код направления 3: 2', 'Код направления 3: 3', 'Код направления 3: 4'
]


class PredictionRequest(BaseModel):
    education_level: str
    data: list[dict]


@app.get("/")
async def root():
    return {
        "message": "Student Dropout Prediction API",
        "endpoints": {
            "test": "GET /test",
            "predict": "POST /predict"
        }
    }


@app.get("/test")
async def test_endpoint():
    return {"status": "API работает корректно", "models_loaded": True}


@app.get("/predict")
async def predict_get():
    return {
        "message": "Используйте POST запрос с JSON телом",
        "example_request": {
            "education_level": "magistr",
            "data": [{col: 0 for col in FEATURE_COLUMNS}]
        }
    }


@app.post("/predict")
async def predict(request: PredictionRequest):
    try:
        logger.debug(f"Получен запрос: education_level={request.education_level}")
        
        if request.education_level not in ['magistr', 'bak_spec']:
            raise HTTPException(
                status_code=400,
                detail="Неправильный уровень образования. Используйте 'magistr' или 'bak_spec'"
            )
        
        data = pd.DataFrame(request.data)
        logger.debug(f"Данные преобразованы в DataFrame, строк: {len(data)}")
        
        missing_cols = [col for col in FEATURE_COLUMNS if col not in data.columns]
        if missing_cols:
            logger.error(f"Отсутствуют столбцы: {missing_cols}")
            raise HTTPException(
                status_code=400,
                detail=f"Отсутствуют обязательные столбцы: {missing_cols}"
            )
        
        model = model_magistr if request.education_level == 'magistr' else model_bak_spec
        
        if hasattr(model, 'predict_proba'):
            predictions = model.predict_proba(data[FEATURE_COLUMNS])[:, 1]
        else:
            predictions = model.predict(data[FEATURE_COLUMNS]).astype(float)
        
        logger.debug(f"Предсказания сгенерированы, пример: {predictions[:5]}")
        
        return {
            "status": "success",
            "predictions": predictions.tolist(),
            "count": len(predictions)
        }
    
    except Exception as e:
        logger.error(f"Ошибка обработки запроса: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка обработки: {str(e)}"
        )

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
