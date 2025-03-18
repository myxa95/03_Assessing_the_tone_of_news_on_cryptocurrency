# Прогнозирование ключевой ставки ЦБ РФ моделью Prophet.
[![Python - Version](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Prophet - Version](https://img.shields.io/badge/Prophet-1.1.5-red?style=for-the-badge&logo=prophet)](https://facebook.github.io/prophet/)

## Описание работы
Проект использует данные по ключевой ставке Банка России для прогнозирования ее значений в будущем с помощью модели Prophet. Основные шаги проекта:
- Сбор исторических данных по ключевой ставке ЦБ РФ с официального сайта.
- Предобработка данных: очистка, заполнение пропусков, преобразование в формат для модели.
- Разделение данных на обучающую и тестовую выборки.
- Обучение модели Prophet на обучающей выборке. Prophet использует аддитивную модель с трендом и сезонностью.
- Оценка качества модели на тестовой выборке по метрикам RMSE, MAE, MAPE.
- Использование лучшей модели для прогнозирования ключевой ставки на заданный период в будущем.
- Анализ полученных прогнозов, сравнение с фактическими данными и решениями ЦБ РФ по ставке
- Обучение модели Prophet на полной выборке и предсказание ставки на будущие периоды<br>

## Структура проекта
- **backend** <br> 
Создание признаков времян года, дней недели.
Парсинг датасета.
Получения метрик.
- **config** <br>
Файл конфигурации
- **data** <br>
Спарсенные курсы ключевой ставки ЦБ РФ в DataFrame.
- **frontend** <br>
Фронтенд чать проекта, steamlid
- **models** <br>
Сохраненная модель prophet с лучшими параметрами после обучения по сетке.
- **notebooks** <br> 
Jupyter ноутбуки, в которых описана техническая часть: построение моделей, обучение и тестирование
- **report** <br>
Сохраненные лучше параметры после подбора параметров при помощи Optuna, сохранение метрик.

## Команды для запуска FastAPI
-   cd backend
-   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
-   Доступ к FastAPI по адресу: http://localhost:8000/docs

- убить процесс по ID
lsof -i:8000 | Get-NetTCPConnection -LocalPort 8000 | Select-Object -Property OwningProcess
kill -9 process_id | Stop-Process -Id process_id -Force

- убить все процессы
for pid in $(ps -ef | grep "uvicorn main:app" | awk '{print $2}'); do kill -9 $pid; done
Get-Process | Where-Object { $_.ProcessName -eq "uvicorn" } | Stop-Process -Force

## Команды для запуска Streamlit
-   cd frontend
-   streamlit run main.py
-   Доступ к Streamlit осуществляется по адресу: http://localhost:8501/
-   убить все процессы
for pid in $(ps -ef | grep "streamlit run" | awk '{print $2}'); do kill -9 $pid; done
Get-Process | Where-Object { $_.ProcessName -eq "streamlit" } | Stop-Process -Force