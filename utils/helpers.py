# utils/helpers.py
"""
Вспомогательные функции для OnboardingBuddy
"""
import logging
import os
import json
from datetime import datetime
from typing import Any, Dict, List
from config.settings import settings


def setup_logging():
    """Настройка системы логирования"""

    # Создаем директорию для логов если её нет
    log_dir = os.path.dirname(settings.LOG_FILE)
    os.makedirs(log_dir, exist_ok=True)

    # Настройка формата логов
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # Настройка уровня логирования
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Конфигурация логирования
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.FileHandler(settings.LOG_FILE, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    # Устанавливаем уровень для библиотек
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.WARNING)


def format_datetime(dt: datetime, format_type: str = 'full') -> str:
    """Форматирование даты и времени"""
    if not dt:
        return "Не указано"

    formats = {
        'full': '%d.%m.%Y %H:%M:%S',
        'date': '%d.%m.%Y',
        'time': '%H:%M',
        'short': '%d.%m %H:%M',
        'iso': '%Y-%m-%dT%H:%M:%S'
    }

    return dt.strftime(formats.get(format_type, formats['full']))


def truncate_text(text: str, max_length: int = 50) -> str:
    """Обрезание текста с добавлением многоточия"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def escape_markdown(text: str) -> str:
    """Экранирование символов для Markdown"""
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    return text


def create_progress_bar(current: int, total: int, length: int = 10) -> str:
    """Создание прогресс-бара"""
    if total == 0:
        return "░" * length

    progress = min(current / total, 1.0)
    filled = int(progress * length)
    empty = length - filled

    return "█" * filled + "░" * empty


def format_file_size(size_bytes: int) -> str:
    """Форматирование размера файла"""
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024
        i += 1

    return f"{size_bytes:.1f} {size_names[i]}"


def validate_email(email: str) -> bool:
    """Простая валидация email"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_telegram_username(username: str) -> bool:
    """Валидация Telegram username"""
    import re
    if not username.startswith('@'):
        return False
    pattern = r'^@[a-zA-Z0-9_]{5,32}$'
    return re.match(pattern, username) is not None


def safe_int(value: Any, default: int = 0) -> int:
    """Безопасное преобразование в int"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """Безопасное преобразование в float"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def chunks(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Разбивка списка на части"""
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


def save_json(data: Dict[str, Any], filepath: str) -> bool:
    """Сохранение данных в JSON файл"""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        return True
    except Exception as e:
        logging.error(f"Ошибка сохранения JSON: {e}")
        return False


def load_json(filepath: str) -> Dict[str, Any]:
    """Загрузка данных из JSON файла"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Ошибка загрузки JSON: {e}")
        return {}


def format_user_info(user_data: Dict[str, Any]) -> str:
    """Форматирование информации о пользователе"""
    user_id = user_data.get('user_id', 'N/A')
    full_name = user_data.get('full_name', 'Не указано')
    username = user_data.get('username', 'Не указан')
    status = user_data.get('status', 'unknown')
    stage = user_data.get('stage', 0)

    username_str = f"@{username}" if username else "Не указан"

    return f"""
👤 Пользователь {user_id}
📝 Имя: {full_name}
🏷️ Username: {username_str}
📊 Статус: {status}
🎯 Этап: {stage}/10
"""


def generate_report_filename(report_type: str) -> str:
    """Генерация имени файла для отчета"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{report_type}_{timestamp}.json"


def create_backup_filename(base_name: str) -> str:
    """Создание имени файла резервной копии"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    name, ext = os.path.splitext(base_name)
    return f"{name}_backup_{timestamp}{ext}"


def sanitize_filename(filename: str) -> str:
    """Очистка имени файла от недопустимых символов"""
    import re
    # Удаляем недопустимые символы
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Ограничиваем длину
    if len(filename) > 200:
        name, ext = os.path.splitext(filename)
        filename = name[:196] + ext
    return filename


def get_user_agent_info(update) -> Dict[str, str]:
    """Получение информации о пользователе из update"""
    user = update.effective_user
    return {
        'user_id': str(user.id),
        'first_name': user.first_name or '',
        'last_name': user.last_name or '',
        'username': user.username or '',
        'full_name': user.full_name or '',
        'language_code': user.language_code or 'ru'
    }


def format_statistics(stats: Dict[str, Any]) -> str:
    """Форматирование статистики для отображения"""
    total_users = stats.get('total_users', 0)
    active_week = stats.get('active_week', 0)
    completion_rate = stats.get('completion_rate', 0)
    total_feedback = stats.get('total_feedback', 0)
    activity = active_week / total_users * 100 if total_users > 0 else 0

    return f"""
📊 Статистика OnboardingBuddy

👥 Всего пользователей: {total_users}
🔥 Активных за неделю: {active_week}
💬 Обратной связи: {total_feedback}
✅ Процент завершения: {completion_rate}%

📈 Активность: {activity:.1f}%
"""


def calculate_completion_time(start_date: datetime, end_date: datetime = None) -> str:
    """Расчет времени завершения процесса"""
    if not end_date:
        end_date = datetime.now()

    delta = end_date - start_date

    if delta.days > 0:
        return f"{delta.days} дн. {delta.seconds // 3600} ч."
    elif delta.seconds > 3600:
        return f"{delta.seconds // 3600} ч. {(delta.seconds % 3600) // 60} мин."
    else:
        return f"{(delta.seconds % 3600) // 60} мин."


def mask_sensitive_data(text: str) -> str:
    """Маскировка чувствительных данных в логах"""
    import re

    # Маскируем email
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                  lambda m: m.group(0)[:3] + '*' * (len(m.group(0)) - 6) + m.group(0)[-3:], text)

    # Маскируем номера телефонов
    text = re.sub(r'\b\+?[0-9]{1,3}[-.\s]?\(?[0-9]{3,4}\)?[-.\s]?[0-9]{3,4}[-.\s]?[0-9]{2,4}\b',
                  lambda m: m.group(0)[:3] + '*' * (len(m.group(0)) - 6) + m.group(0)[-3:], text)

    return text


def generate_unique_id() -> str:
    """Генерация уникального ID"""
    import uuid
    return str(uuid.uuid4())


def is_working_hours() -> bool:
    """Проверка рабочего времени"""
    now = datetime.now()
    # Рабочие часы: понедельник-пятница 9:00-18:00
    if now.weekday() >= 5:  # Суббота, воскресенье
        return False
    return 9 <= now.hour <= 18


def get_greeting_by_time() -> str:
    """Получение приветствия в зависимости от времени"""
    hour = datetime.now().hour

    if 5 <= hour < 12:
        return "Доброе утро"
    elif 12 <= hour < 17:
        return "Добрый день"
    elif 17 <= hour < 23:
        return "Добрый вечер"
    else:
        return "Доброй ночи"


def create_status_emoji_map() -> Dict[str, str]:
    """Карта эмодзи для статусов"""
    return {
        'new': '🆕',
        'preboarding': '🔄',
        'preboarded': '✅',
        'onboarding': '🚀',
        'completed': '🎉',
        'error': '❌',
        'warning': '⚠️',
        'info': 'ℹ️',
        'success': '✅'
    }


def format_callback_data(action: str, kwargs) -> str:
    """Форматирование callback_data с параметрами"""
    if not kwargs:
        return action

    params = '&'.join([f"{k}={v}" for k, v in kwargs.items()])
    return f"{action}?{params}"


def parse_callback_data(callback_data: str) -> tuple:
    """Парсинг callback_data"""
    if '?' not in callback_data:
        return callback_data, {}

    action, params_str = callback_data.split('?', 1)
    params = {}

    for param in params_str.split('&'):
        if '=' in param:
            key, value = param.split('=', 1)
            params[key] = value

    return action, params


class RateLimiter:
    """Простой rate limiter для предотвращения спама"""

    def __init__(self, max_requests: int = 10, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = {}

    def is_allowed(self, user_id: int) -> bool:
        """Проверка, разрешен ли запрос"""
        now = datetime.now().timestamp()

        if user_id not in self.requests:
            self.requests[user_id] = []

        # Удаляем старые запросы
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if now - req_time < self.time_window
        ]

        # Проверяем лимит
        if len(self.requests[user_id]) >= self.max_requests:
            return False

        # Добавляем новый запрос
        self.requests[user_id].append(now)
        return True


# Глобальный rate limiter
rate_limiter = RateLimiter()


def rate_limit_check(user_id: int) -> bool:
    """Проверка rate limit для пользователя"""
    return rate_limiter.is_allowed(user_id)


def create_data_directory_structure():
    """Создание структуры директорий для данных"""
    directories = [
        'data',
        'data/logs',
        'data/exports',
        'data/backups',
        'data/temp'
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)


def cleanup_temp_files(max_age_hours: int = 24):
    """Очистка временных файлов"""
    temp_dir = 'data/temp'
    if not os.path.exists(temp_dir):
        return

    now = datetime.now().timestamp()
    max_age_seconds = max_age_hours * 3600

    for filename in os.listdir(temp_dir):
        filepath = os.path.join(temp_dir, filename)
        if os.path.isfile(filepath):
            file_age = now - os.path.getmtime(filepath)
            if file_age > max_age_seconds:
                try:
                    os.remove(filepath)
                    logging.info(f"Удален временный файл: {filename}")
                except Exception as e:
                    logging.error(f"Ошибка удаления файла {filename}: {e}")


def get_system_info() -> Dict[str, Any]:
    """Получение информации о системе"""
    import platform
    import psutil

    return {
        'platform': platform.platform(),
        'python_version': platform.python_version(),
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_usage': psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:').percent
    }