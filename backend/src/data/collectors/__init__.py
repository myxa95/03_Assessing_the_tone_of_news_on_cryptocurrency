"""
Модуль для сборщиков данных из различных источников:
- Новости криптовалют
- Цены криптовалют
- Торговые индикаторы
"""

from .crypto_news_parser import CryptoNewsParser

__all__ = ['CryptoNewsParser'] 