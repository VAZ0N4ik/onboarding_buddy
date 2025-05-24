# utils/validators.py
"""
Валидаторы для OnboardingBuddy
"""
import re
import os
from typing import List, Optional, Tuple, Dict
from urllib.parse import urlparse


def validate_telegram_token(token: str) -> Tuple[bool, str]:
    """Валидация токена Telegram бота"""
    if not token or token == 'YOUR_BOT_TOKEN_HERE':
        return False, "Токен не указан"

    # Формат токена: 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
    pattern = r'^\d+:[A-Za-z0-9_-]{35}$'
    if not re.match(pattern, token):
        return False, "Неверный формат токена"

    return True, "Токен корректен"


def validate_admin_ids(admin_ids: str) -> Tuple[bool, str, List[int]]:
    """Валидация ID администраторов"""
    if not admin_ids:
        return False, "ID администраторов не указаны", []

    try:
        ids = [int(id_str.strip()) for id_str in admin_ids.split(',') if id_str.strip()]

        if not ids:
            return False, "Не указано ни одного ID", []

        # Проверяем что ID положительные
        for admin_id in ids:
            if admin_id <= 0:
                return False, f"ID {admin_id} должен быть положительным числом", []

            # Telegram user ID обычно больше 10000
            if admin_id < 10000:
                return False, f"ID {admin_id} слишком маленький для Telegram", []

        return True, f"Найдено {len(ids)} администратор(ов)", ids

    except ValueError:
        return False, "ID должны быть числами, разделенными запятыми", []


def validate_email(email: str) -> Tuple[bool, str]:
    """Валидация email адреса"""
    if not email:
        return False, "Email не указан"

    # Базовая проверка формата email
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Неверный формат email"

    # Проверка длины
    if len(email) > 254:
        return False, "Email слишком длинный"

    # Проверка локальной части (до @)
    local_part = email.split('@')[0]
    if len(local_part) > 64:
        return False, "Локальная часть email слишком длинная"

    return True, "Email корректен"


def validate_telegram_username(username: str) -> Tuple[bool, str]:
    """Валидация Telegram username"""
    if not username:
        return False, "Username не указан"

    # Убираем @ если есть
    if username.startswith('@'):
        username = username[1:]

    # Проверка формата: только латинские буквы, цифры и _
    pattern = r'^[a-zA-Z0-9_]{5,32}$'
    if not re.match(pattern, username):
        return False, "Username должен содержать 5-32 символа (буквы, цифры, _)"

    # Не может начинаться с цифры
    if username[0].isdigit():
        return False, "Username не может начинаться с цифры"

    # Не может заканчиваться на _
    if username.endswith('_'):
        return False, "Username не может заканчиваться на _"

    return True, "Username корректен"


def validate_url(url: str, scheme_required: bool = True) -> Tuple[bool, str]:
    """Валидация URL"""
    if not url:
        return False, "URL не указан"

    try:
        parsed = urlparse(url)

        if scheme_required and not parsed.scheme:
            return False, "URL должен содержать схему (http/https)"

        if scheme_required and parsed.scheme not in ['http', 'https']:
            return False, "URL должен использовать http или https"

        if not parsed.netloc:
            return False, "URL должен содержать домен"

        # Проверка на подозрительные символы
        suspicious_chars = ['<', '>', '"', '{', '}', '|', '^', '`']
        for char in suspicious_chars:
            if char in url:
                return False, f"URL содержит недопустимый символ: {char}"

        return True, "URL корректен"

    except Exception as e:
        return False, f"Ошибка парсинга URL: {str(e)}"


def validate_phone_number(phone: str) -> Tuple[bool, str]:
    """Валидация номера телефона"""
    if not phone:
        return False, "Номер телефона не указан"

    # Убираем все кроме цифр и +
    cleaned = re.sub(r'[^\d+]', '', phone)

    # Проверяем базовый формат
    patterns = [
        r'^\+7\d{10}$',  # +7XXXXXXXXXX
        r'^8\d{10}$',  # 8XXXXXXXXXX
        r'^\+\d{10,15}$'  # Международный формат
    ]

    for pattern in patterns:
        if re.match(pattern, cleaned):
            return True, "Номер телефона корректен"

    return False, "Неверный формат номера телефона"


def validate_company_name(name: str) -> Tuple[bool, str]:
    """Валидация названия компании"""
    if not name:
        return False, "Название компании не указано"

    if len(name) < 2:
        return False, "Название компании слишком короткое"

    if len(name) > 100:
        return False, "Название компании слишком длинное"

    # Проверяем что не содержит только пробелы
    if not name.strip():
        return False, "Название компании не может состоять только из пробелов"

    return True, "Название компании корректно"


def validate_file_path(path: str, must_exist: bool = False) -> Tuple[bool, str]:
    """Валидация пути к файлу"""
    if not path:
        return False, "Путь к файлу не указан"

    # Проверяем что путь не содержит опасные символы
    dangerous_chars = ['..', '<', '>', '|', '?', '*']
    for char in dangerous_chars:
        if char in path:
            return False, f"Путь содержит недопустимый символ: {char}"

    if must_exist and not os.path.exists(path):
        return False, "Файл не существует"

    # Проверяем что директория существует или может быть создана
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        try:
            os.makedirs(directory, exist_ok=True)
        except OSError:
            return False, "Не удается создать директорию"

    return True, "Путь к файлу корректен"


def validate_positive_integer(value: str, min_value: int = 1, max_value: int = None) -> Tuple[bool, str, int]:
    """Валидация положительного целого числа"""
    try:
        num = int(value)

        if num < min_value:
            return False, f"Значение должно быть не менее {min_value}", 0

        if max_value and num > max_value:
            return False, f"Значение должно быть не более {max_value}", 0

        return True, "Число корректно", num

    except ValueError:
        return False, "Значение должно быть числом", 0


def validate_boolean_string(value: str) -> Tuple[bool, str, bool]:
    """Валидация строки boolean значения"""
    if not value:
        return False, "Значение не указано", False

    true_values = ['true', '1', 'yes', 'y', 'on', 'enable', 'enabled']
    false_values = ['false', '0', 'no', 'n', 'off', 'disable', 'disabled']

    value_lower = value.lower().strip()

    if value_lower in true_values:
        return True, "Значение корректно", True
    elif value_lower in false_values:
        return True, "Значение корректно", False
    else:
        return False, "Значение должно быть true/false, yes/no, 1/0", False


def validate_log_level(level: str) -> Tuple[bool, str]:
    """Валидация уровня логирования"""
    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']

    if not level:
        return False, "Уровень логирования не указан"

    if level.upper() not in valid_levels:
        return False, f"Уровень должен быть одним из: {', '.join(valid_levels)}"

    return True, "Уровень логирования корректен"


def validate_delay_value(value: str) -> Tuple[bool, str, float]:
    """Валидация значения задержки (в секундах)"""
    try:
        delay = float(value)

        if delay < 0:
            return False, "Задержка не может быть отрицательной", 0.0

        if delay > 10:
            return False, "Задержка слишком большая (максимум 10 сек)", 0.0

        return True, "Задержка корректна", delay

    except ValueError:
        return False, "Задержка должна быть числом", 0.0


def validate_message_length(length: str) -> Tuple[bool, str, int]:
    """Валидация максимальной длины сообщения"""
    try:
        max_length = int(length)

        if max_length < 100:
            return False, "Минимальная длина сообщения: 100 символов", 0

        if max_length > 10000:
            return False, "Максимальная длина сообщения: 10000 символов", 0

        return True, "Длина сообщения корректна", max_length

    except ValueError:
        return False, "Длина должна быть числом", 0


def validate_config_file(config_path: str = '.env') -> List[str]:
    """Комплексная валидация конфигурационного файла"""
    issues = []

    if not os.path.exists(config_path):
        return ["❌ Файл конфигурации не найден"]

    try:
        # Читаем файл конфигурации
        config_vars = {}
        with open(config_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config_vars[key.strip()] = value.strip()

        # Валидируем обязательные параметры
        required_params = {
            'BOT_TOKEN': validate_telegram_token,
            'ADMIN_IDS': lambda x: validate_admin_ids(x)[:2],  # Берем только первые 2 элемента
            'COMPANY_NAME': validate_company_name,
            'HR_EMAIL': validate_email,
            'SUPPORT_EMAIL': validate_email
        }

        for param, validator in required_params.items():
            if param not in config_vars:
                issues.append(f"❌ Отсутствует обязательный параметр: {param}")
            else:
                is_valid, message = validator(config_vars[param])
                if not is_valid:
                    issues.append(f"❌ {param}: {message}")

        # Валидируем опциональные параметры
        optional_params = {
            'HR_TELEGRAM': validate_telegram_username,
            'SUPPORT_TELEGRAM': validate_telegram_username,
            'HR_PHONE': validate_phone_number,
            'SUPPORT_PHONE': validate_phone_number,
            'COMPANY_SITE': lambda x: validate_url(x, True),
            'TEAM_PAGE': lambda x: validate_url(x, True),
            'HANDBOOK_URL': lambda x: validate_url(x, True),
            'MEETING_GENERAL': lambda x: validate_url(x, True),
            'MEETING_IT': lambda x: validate_url(x, True),
            'MEETING_MARKETING': lambda x: validate_url(x, True),
            'DEBUG_MODE': lambda x: validate_boolean_string(x)[:2],
            'NOTIFICATION_ENABLED': lambda x: validate_boolean_string(x)[:2],
            'LOG_LEVEL': validate_log_level,
            'BROADCAST_DELAY': lambda x: validate_delay_value(x)[:2],
            'MAX_MESSAGE_LENGTH': lambda x: validate_message_length(x)[:2]
        }

        for param, validator in optional_params.items():
            if param in config_vars and config_vars[param]:
                is_valid, message = validator(config_vars[param])
                if not is_valid:
                    issues.append(f"⚠️ {param}: {message}")

        # Проверяем файловые пути
        file_paths = ['DATABASE_PATH', 'LOG_FILE']
        for param in file_paths:
            if param in config_vars:
                is_valid, message = validate_file_path(config_vars[param])
                if not is_valid:
                    issues.append(f"⚠️ {param}: {message}")

    except Exception as e:
        issues.append(f"❌ Ошибка чтения конфигурации: {str(e)}")

    return issues


def validate_database_connection(db_path: str) -> Tuple[bool, str]:
    """Валидация подключения к базе данных"""
    try:
        import sqlite3

        # Проверяем что можем создать/открыть БД
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Проверяем что можем выполнить простой запрос
        cursor.execute('SELECT 1')
        result = cursor.fetchone()

        conn.close()

        if result and result[0] == 1:
            return True, "Подключение к базе данных успешно"
        else:
            return False, "Ошибка выполнения тестового запроса"

    except Exception as e:
        return False, f"Ошибка подключения к БД: {str(e)}"


def validate_telegram_bot_token_online(token: str) -> Tuple[bool, str]:
    """Онлайн валидация токена через Telegram API"""
    try:
        import requests

        # Проверяем локальный формат сначала
        is_valid, message = validate_telegram_token(token)
        if not is_valid:
            return False, message

        # Делаем запрос к Telegram API
        url = f"https://api.telegram.org/bot{token}/getMe"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data.get('result', {})
                bot_name = bot_info.get('username', 'неизвестно')
                return True, f"Токен валиден. Бот: @{bot_name}"
            else:
                return False, "Токен отклонен Telegram API"
        else:
            return False, f"Ошибка API: {response.status_code}"

    except ImportError:
        return True, "Токен корректен (requests не установлен для онлайн проверки)"
    except Exception as e:
        return True, f"Токен корректен (ошибка онлайн проверки: {str(e)})"


def validate_system_requirements() -> List[str]:
    """Проверка системных требований"""
    issues = []

    # Проверяем версию Python
    import sys
    if sys.version_info < (3, 8):
        issues.append(f"❌ Требуется Python 3.8+, текущая версия: {sys.version}")

    # Проверяем доступность места на диске
    import shutil
    try:
        free_space = shutil.disk_usage('.').free / (1024 ** 3)  # GB
        if free_space < 1:
            issues.append(f"⚠️ Мало места на диске: {free_space:.1f} GB")
    except:
        pass

    # Проверяем необходимые модули
    required_modules = [
        'telegram',
        'sqlite3'
    ]

    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            issues.append(f"❌ Отсутствует модуль: {module}")

    # Проверяем права на запись
    try:
        test_file = 'test_write_permissions.tmp'
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
    except:
        issues.append("❌ Нет прав на запись в текущей директории")

    return issues


def validate_network_connectivity() -> Tuple[bool, str]:
    """Проверка сетевого подключения"""
    try:
        import socket

        # Проверяем подключение к Telegram
        socket.create_connection(("api.telegram.org", 443), timeout=10)
        return True, "Сетевое подключение в порядке"

    except ImportError:
        return True, "Проверка сети пропущена (socket недоступен)"
    except Exception as e:
        return False, f"Проблемы с сетевым подключением: {str(e)}"


def get_validation_summary(config_path: str = '.env') -> Dict[str, any]:
    """Получить полную сводку валидации"""
    summary = {
        'timestamp': datetime.now().isoformat(),
        'config_file': config_path,
        'config_issues': [],
        'system_issues': [],
        'database_status': {'valid': False, 'message': ''},
        'network_status': {'valid': False, 'message': ''},
        'overall_status': 'unknown'
    }

    # Валидация конфигурации
    summary['config_issues'] = validate_config_file(config_path)

    # Валидация системы
    summary['system_issues'] = validate_system_requirements()

    # Валидация базы данных
    from config.settings import settings
    db_valid, db_message = validate_database_connection(settings.DATABASE_PATH)
    summary['database_status'] = {'valid': db_valid, 'message': db_message}

    # Валидация сети
    net_valid, net_message = validate_network_connectivity()
    summary['network_status'] = {'valid': net_valid, 'message': net_message}

    # Общий статус
    total_issues = len(summary['config_issues']) + len(summary['system_issues'])
    critical_issues = len([issue for issue in summary['config_issues'] if issue.startswith('❌')])

    if critical_issues > 0:
        summary['overall_status'] = 'critical'
    elif total_issues > 0:
        summary['overall_status'] = 'warning'
    elif db_valid and net_valid:
        summary['overall_status'] = 'good'
    else:
        summary['overall_status'] = 'partial'

    return summary


if __name__ == '__main__':
    # Тестирование валидаторов
    import sys
    from datetime import datetime

    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        print("🧪 Тестирование валидаторов...")

        # Тест валидации токена
        print("\nТест токена:")
        print(validate_telegram_token("123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"))
        print(validate_telegram_token("invalid"))

        # Тест валидации email
        print("\nТест email:")
        print(validate_email("test@example.com"))
        print(validate_email("invalid-email"))

        # Тест валидации username
        print("\nТест username:")
        print(validate_telegram_username("@valid_username"))
        print(validate_telegram_username("@123invalid"))

        print("\n✅ Тестирование завершено")

    else:
        # Полная валидация
        summary = get_validation_summary()

        print("🔍 Результат валидации OnboardingBuddy:")
        print("=" * 50)

        print(f"📅 Время проверки: {summary['timestamp']}")
        print(f"📄 Конфигурация: {summary['config_file']}")
        print(f"🎯 Общий статус: {summary['overall_status'].upper()}")

        if summary['config_issues']:
            print(f"\n⚙️ Проблемы конфигурации ({len(summary['config_issues'])}):")
            for issue in summary['config_issues']:
                print(f"  {issue}")

        if summary['system_issues']:
            print(f"\n💻 Системные проблемы ({len(summary['system_issues'])}):")
            for issue in summary['system_issues']:
                print(f"  {issue}")

        print(f"\n🗄️ База данных: {summary['database_status']['message']}")
        print(f"🌐 Сеть: {summary['network_status']['message']}")

        if summary['overall_status'] == 'good':
            print("\n🎉 Все проверки пройдены! Бот готов к запуску.")
        elif summary['overall_status'] == 'critical':
            print("\n💥 Критические ошибки! Бот не может быть запущен.")
        else:
            print("\n⚠️ Есть предупреждения, но бот может работать.")