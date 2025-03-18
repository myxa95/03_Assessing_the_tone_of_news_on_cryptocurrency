import os
import requests
import pandas as pd
import json
from datetime import datetime
import time
from pathlib import Path
import yaml
import pprint

class CryptoNewsParser:
    def __init__(self, api_key=None, config_path=None):
        """
        Инициализация парсера новостей CoinMarketCap.
        
        Args:
            api_key: API ключ для CoinMarketCap (опционально)
            config_path: Путь к файлу конфигурации (опционально)
        """
        self.api_key = api_key
        
        # Загрузка ключа API из конфигурационного файла, если не указан
        if self.api_key is None and config_path is not None:
            self.api_key = self._load_api_key_from_config(config_path)
            
        self.base_url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
        self.news_url = "https://api.coinmarketcap.com/content/v3/news"
        
    def _load_api_key_from_config(self, config_path):
        """Загрузка API ключа из конфигурационного файла."""
        try:
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
                return config.get('parsing', {}).get('API')
        except Exception as e:
            print(f"Ошибка при загрузке конфигурационного файла: {e}")
            return None
        
    def get_latest_news(self, limit=50, page=1):
        """
        Получение последних новостей о криптовалютах.
        
        Args:
            limit: Количество новостей для получения
            page: Номер страницы
            
        Returns:
            DataFrame с новостями или None в случае ошибки
        """
        try:
            params = {
                'page': page,
                'size': limit
            }
            
            # Выполнение запроса к API
            response = requests.get(self.news_url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                # Вывод содержимого ответа для диагностики
                print(f"Структура ответа API: {list(data.keys())}")
                
                # Извлечение списка новостей
                news_items = data.get('data', [])
                
                if not news_items:
                    print("Нет доступных новостей.")
                    return None
                
                print(f"Получено {len(news_items)} новостей из API")
                
                # Вывод структуры первой новости для диагностики
                if news_items:
                    first_news = news_items[0]
                    print(f"Пример структуры новости: {list(first_news.keys())}")
                    if 'meta' in first_news:
                        print(f"Структура meta: {list(first_news['meta'].keys())}")
                
                # Обработка новостей
                processed_news = []
                for i, news in enumerate(news_items):
                    # Основные данные находятся в поле 'meta'
                    meta = news.get('meta', {})
                    
                    # Создаем уникальный ID если он отсутствует
                    news_id = meta.get('id')
                    if not news_id:
                        news_id = f"generated-{i}-{hash(meta.get('sourceUrl', ''))}"
                    
                    # Извлекаем информацию о связанных криптовалютах
                    coin_names = []
                    if 'assets' in news and isinstance(news['assets'], list):
                        for asset in news['assets']:
                            coin_name = asset.get('name', '')
                            if coin_name:
                                coin_names.append(coin_name)
                    
                    # Формируем данные новости с правильными полями из meta
                    news_item = {
                        'id': news_id,
                        'title': meta.get('title', ''),
                        'description': meta.get('subtitle', ''),  # subtitle используется как описание
                        'content': meta.get('content', ''),  # полный HTML-контент новости (может быть не у всех)
                        'published_at': meta.get('releasedAt', ''),  # дата публикации
                        'url': meta.get('sourceUrl', ''),
                        'source': meta.get('sourceName', ''),
                        'category': news.get('category', ''),
                        'tags': ', '.join([tag.get('name', '') for tag in news.get('tags', [])]),
                        'coins': ', '.join(coin_names),
                        'cover_image': news.get('cover', '')  # URL изображения
                    }
                    
                    # Проверка на пустой URL
                    if news_item['url']:
                        processed_news.append(news_item)
                    else:
                        print(f"Пропущена новость без URL (ID: {news_id})")
                
                print(f"Обработано {len(processed_news)} новостей с непустыми URL")
                
                # Создаем DataFrame
                news_df = pd.DataFrame(processed_news)
                
                # Проверка на пустые значения в важных полях
                for column in ['title', 'description', 'published_at', 'url', 'content']:
                    if column in news_df.columns:
                        null_count = news_df[column].isnull().sum()
                        empty_count = (news_df[column] == '').sum()
                        print(f"Поле '{column}': {null_count} NULL значений, {empty_count} пустых строк")
                
                # Дополнительная информация по контенту (если он есть)
                if 'content' in news_df.columns:
                    non_empty_content = (news_df['content'] != '').sum()
                    print(f"Новости с непустым контентом: {non_empty_content} из {len(news_df)}")
                    
                    # Пример первой новости с непустым контентом
                    if non_empty_content > 0:
                        sample_content = news_df[news_df['content'] != '']['content'].iloc[0]
                        content_preview = sample_content[:200] + '...' if len(sample_content) > 200 else sample_content
                        print(f"Пример контента: {content_preview}")
                
                return news_df
            else:
                print(f"Ошибка при получении данных: {response.status_code}")
                print(response.text)
                return None
        except Exception as e:
            print(f"Произошла ошибка при получении новостей: {e}")
            print(f"Тип ошибки: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            return None
            
    def save_news(self, output_path, limit=100, pages=20, filename="crypto_news.csv"):
        """
        Получение и сохранение новостей в единый CSV файл с проверкой на дубликаты.
        
        Args:
            output_path: Путь для сохранения файла
            limit: Количество новостей на страницу
            pages: Количество страниц для получения
            filename: Имя файла для сохранения (по умолчанию crypto_news.csv)
            
        Returns:
            Path: Путь к сохраненному файлу
        """
        # Создание директории, если не существует
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Полный путь к файлу
        file_path = output_dir / filename
        
        # Загрузка существующих новостей, если файл существует
        existing_news = pd.DataFrame()
        if file_path.exists():
            print(f"Найден существующий файл {file_path}. Загружаем данные...")
            try:
                existing_news = pd.read_csv(file_path)
                print(f"Загружено {len(existing_news)} существующих новостей.")
                
                # Проверка наличия колонки 'url' для определения дубликатов
                if 'url' in existing_news.columns:
                    print(f"Колонка 'url' найдена в существующих данных.")
                    # Проверка на уникальность url
                    duplicate_urls = existing_news['url'].duplicated().sum()
                    if duplicate_urls > 0:
                        print(f"ВНИМАНИЕ: Найдено {duplicate_urls} дубликатов URL в существующем файле!")
                else:
                    print("ВНИМАНИЕ: Колонка 'url' отсутствует в существующих данных!")
            except Exception as e:
                print(f"Ошибка при чтении существующего файла: {e}")
                print("Создаем новый файл.")
                existing_news = pd.DataFrame()
        
        # Получение новых новостей
        all_news = []
        for page in range(1, pages + 1):
            print(f"Получение страницы {page} из {pages}...")
            news_df = self.get_latest_news(limit=limit, page=page)
            
            if news_df is not None and not news_df.empty:
                all_news.append(news_df)
                # Небольшая задержка, чтобы не перегружать API
                time.sleep(1)
            else:
                break
                
        if not all_news:
            print("Не удалось получить новые новости.")
            return None
            
        # Объединение всех новых новостей
        new_news = pd.concat(all_news)
        print(f"Получено {len(new_news)} новых новостей.")
        
        # Проверка наличия колонки url в новых данных
        if 'url' in new_news.columns:
            print(f"Колонка 'url' найдена в новых данных.")
            # Проверка на наличие пустых url
            null_urls = new_news['url'].isnull().sum()
            if null_urls > 0:
                print(f"ВНИМАНИЕ: {null_urls} новостей с пустыми URL!")
            
            # Удаление строк с пустыми URL
            if null_urls > 0:
                new_news = new_news.dropna(subset=['url'])
                print(f"Удалено {null_urls} строк с пустыми URL. Осталось {len(new_news)} новостей.")
            
            # Проверка на уникальность url в новых данных
            duplicate_urls = new_news['url'].duplicated().sum()
            if duplicate_urls > 0:
                print(f"ВНИМАНИЕ: Найдено {duplicate_urls} дубликатов URL в новых данных!")
                # Удаление дубликатов URL в новых данных
                new_news = new_news.drop_duplicates(subset=['url'], keep='first')
                print(f"Удалены дубликаты URL в новых данных. Осталось {len(new_news)} уникальных новостей.")
        else:
            print("ОШИБКА: Колонка 'url' отсутствует в новых данных!")
            return None
        
        # Объединение с существующими и удаление дубликатов
        if not existing_news.empty:
            print("Анализ дубликатов:")
            if 'url' in existing_news.columns and 'url' in new_news.columns:
                # Получим список url новостей до удаления дубликатов
                existing_urls = set(existing_news['url'].dropna().tolist())
                new_urls = set(new_news['url'].dropna().tolist())
                print(f"Уникальных URL в существующих данных: {len(existing_urls)}")
                print(f"Уникальных URL в новых данных: {len(new_urls)}")
                
                # Сколько дубликатов между наборами
                duplicates = existing_urls.intersection(new_urls)
                print(f"Найдено {len(duplicates)} пересечений URL между существующими и новыми данными.")
            
            # Объединение наборов
            combined_news = pd.concat([existing_news, new_news])
            
            # Проверка перед удалением дубликатов
            print(f"Всего строк после объединения: {len(combined_news)}")
            
            # Удаление дубликатов сохраняя первое вхождение (используем URL вместо ID)
            before_drop = len(combined_news)
            combined_news = combined_news.drop_duplicates(subset=['url'], keep='first')
            after_drop = len(combined_news)
            
            print(f"Удалено {before_drop - after_drop} дубликатов.")
            
            # Подсчет новых уникальных новостей
            new_count = len(combined_news) - len(existing_news)
            print(f"Добавлено {new_count} новых уникальных новостей.")
        else:
            combined_news = new_news
            print(f"Добавлено {len(new_news)} новых новостей.")
        
        # Сортировка по дате публикации (от новых к старым)
        if 'published_at' in combined_news.columns:
            try:
                combined_news['published_at'] = pd.to_datetime(combined_news['published_at'])
                combined_news.sort_values(by='published_at', ascending=False, inplace=True)
            except Exception as e:
                print(f"Ошибка при сортировке по дате: {e}")
        
        # Сохранение в CSV
        combined_news.to_csv(file_path, index=False)
        print(f"Всего новостей в файле: {len(combined_news)}")
        print(f"Новости сохранены в {file_path}")
        
        return file_path

    def analyze_api_response(self, limit=10, page=1, save_to_file=True):
        """
        Анализирует ответ API и сохраняет его в JSON-файл для изучения доступных полей.
        
        Args:
            limit: Количество новостей
            page: Номер страницы
            save_to_file: Сохранять ли результат в файл
            
        Returns:
            dict: Полный ответ API
        """
        try:
            params = {
                'page': page,
                'size': limit
            }
            
            print(f"Выполняю тестовый запрос к API с параметрами: {params}")
            response = requests.get(self.news_url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"\n{'='*50}")
                print("АНАЛИЗ СТРУКТУРЫ ОТВЕТА API")
                print(f"{'='*50}")
                
                # Анализ верхнего уровня
                print(f"\n1. Верхний уровень ответа API:")
                print(f"   Доступные ключи: {list(data.keys())}")
                
                # Анализ массива новостей
                if 'data' in data and isinstance(data['data'], list):
                    news_count = len(data['data'])
                    print(f"\n2. Найдено {news_count} новостей в ответе")
                    
                    if news_count > 0:
                        # Анализ первой новости
                        first_news = data['data'][0]
                        print(f"\n3. Структура первой новости:")
                        print(f"   Доступные ключи: {list(first_news.keys())}")
                        
                        # Подробное изучение каждого ключа первой новости
                        print(f"\n4. Подробная структура полей первой новости:")
                        for key, value in first_news.items():
                            if isinstance(value, dict):
                                print(f"   {key}: {type(value).__name__} с ключами {list(value.keys())}")
                            elif isinstance(value, list):
                                if value:
                                    if isinstance(value[0], dict):
                                        print(f"   {key}: Список из {len(value)} {type(value[0]).__name__} с ключами {list(value[0].keys())}")
                                    else:
                                        print(f"   {key}: Список из {len(value)} {type(value[0]).__name__}")
                                else:
                                    print(f"   {key}: Пустой список")
                            else:
                                print(f"   {key}: {type(value).__name__} = {value}")
                        
                        # Подробный анализ конкретных полей, которые нас интересуют
                        if 'meta' in first_news:
                            print(f"\n5. Содержимое поля 'meta':")
                            for key, value in first_news['meta'].items():
                                print(f"   {key}: {type(value).__name__} = {value}")
                        
                        # Печать полного JSON первой новости для детального анализа
                        print(f"\n6. Полное содержимое первой новости (JSON):")
                        print(json.dumps(first_news, indent=2))
                    
                # Сохранение полного ответа API в файл
                if save_to_file:
                    output_dir = Path("D:/Drive/Develop/03_Assessing_the_tone_of_news_on_cryptocurrency/data")
                    output_dir.mkdir(parents=True, exist_ok=True)
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    file_path = output_dir / f"api_response_{timestamp}.json"
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    
                    print(f"\nПолный ответ API сохранен в файл: {file_path}")
                    print(f"Откройте этот файл для изучения полной структуры данных.")
                
                return data
            else:
                print(f"Ошибка при получении данных: {response.status_code}")
                print(response.text)
                return None
        except Exception as e:
            print(f"Произошла ошибка при анализе API: {e}")
            import traceback
            traceback.print_exc()
            return None

def main():
    # Исправленный путь к конфигурационному файлу
    base_dir = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
    config_path = base_dir / "config" / "params.yml"
    
    print(f"Используется конфигурационный файл: {config_path}")
    
    # Путь для сохранения новостей
    output_path = "D:/Drive/Develop/03_Assessing_the_tone_of_news_on_cryptocurrency/data"
    
    # Создание экземпляра парсера
    try:
        parser = CryptoNewsParser(config_path=config_path)
        
        # Альтернативный вариант - использование жестко закодированного API-ключа,
        # если есть проблемы с чтением из файла
        if parser.api_key is None:
            print("API ключ не найден в конфигурационном файле.")
            api_key = "9d65e924-9563-4576-8a9f-4174f34ea698"  # Используем ключ из params.yml
            parser = CryptoNewsParser(api_key=api_key)
            print("Используется жестко закодированный API ключ.")
        
        # Получение и сохранение новостей в единый файл с проверкой на дубликаты
        parser.save_news(output_path, limit=200, pages=25, filename="crypto_news.csv")
        
        print("\n---- Загрузка дополнительных новостей для более полного покрытия ----")
        
        # Получаем еще 5 страниц с большим количеством новостей на страницу
        parser.save_news(output_path, limit=300, pages=5, filename="crypto_news.csv")
    except Exception as e:
        print(f"Ошибка при выполнении парсера: {e}")

if __name__ == "__main__":
    main()
