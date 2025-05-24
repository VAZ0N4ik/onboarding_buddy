# utils/setup.py
"""
Мастер первоначальной настройки OnboardingBuddy
"""
import os
import sys
from pathlib import Path


def setup_wizard():
    """Интерактивный мастер настройки"""
    print("🚀 Добро пожаловать в мастер настройки OnboardingBuddy!")
    print("=" * 60)

    # Проверяем существование .env файла
    env_file = Path('.env')

    if env_file.exists():
        response = input("📁 Файл .env уже существует. Перезаписать? (y/N): ")
        if response.lower() != 'y':
            print("❌ Настройка отменена.")
            return

    print("\n📋 Пожалуйста, предоставьте следующую информацию:")
    print("-" * 40)

    # Собираем основную информацию
    config = {}

    # Токен бота
    print("\n🤖 1. Токен Telegram бота")
    print("   Получите токен у @BotFather в Telegram")
    config['BOT_TOKEN'] = input("   Введите токен бота: ").strip()

    if not config['BOT_TOKEN']:
        print("❌ Токен бота обязателен!")
        return

    # Администраторы
    print("\n👥 2. Администраторы бота")
    print("   Получите ваш ID, написав /start боту @userinfobot")
    admin_ids = input("   Введите ID администраторов через запятую: ").strip()
    config['ADMIN_IDS'] = admin_ids if admin_ids else "123456789"

    # Информация о компании
    print("\n🏢 3. Информация о компании")
    config['COMPANY_NAME'] = input("   Название компании: ").strip() or 'АО "БигТайм АйТи"'

    # HR контакты
    print("\n📧 4. Контакты HR-отдела")
    config['HR_EMAIL'] = input("   Email HR-отдела: ").strip() or "hr@company.ru"
    config['HR_TELEGRAM'] = input("   Telegram HR (@username): ").strip() or "@hr_manager"
    config['HR_PHONE'] = input("   Телефон HR: ").strip() or "+7 (xxx) xxx-xx-xx"

    # Техподдержка
    print("\n🔧 5. Техническая поддержка")
    config['SUPPORT_EMAIL'] = input("   Email техподдержки: ").strip() or "support@company.ru"
    config['SUPPORT_TELEGRAM'] = input("   Telegram техподдержки: ").strip() or "@tech_support"
    config['SUPPORT_PHONE'] = input("   Телефон техподдержки: ").strip() or "+7 (xxx) xxx-xx-xx"

    # Ресурсы компании
    print("\n🌐 6. Ресурсы компании")
    config['COMPANY_SITE'] = input("   Сайт компании: ").strip() or "https://company-site.ru"
    config['TEAM_PAGE'] = input("   Страница команды: ").strip() or f"{config['COMPANY_SITE']}/team"
    config['HANDBOOK_URL'] = input("   Справочник сотрудника: ").strip() or f"{config['COMPANY_SITE']}/handbook"

    # Встречи
    print("\n📅 7. Ссылки на встречи")
    default_meeting = "https://meet.company.ru"
    config['MEETING_GENERAL'] = input(
        f"   Общая планерка [{default_meeting}/general]: ").strip() or f"{default_meeting}/general"
    config['MEETING_IT'] = input(f"   IT планерка [{default_meeting}/it]: ").strip() or f"{default_meeting}/it"
    config['MEETING_MARKETING'] = input(
        f"   Маркетинг планерка [{default_meeting}/marketing]: ").strip() or f"{default_meeting}/marketing"

    # Дополнительные настройки
    print("\n⚙️ 8. Дополнительные настройки")

    debug_mode = input("   Режим отладки (y/N): ").strip().lower()
    config['DEBUG_MODE'] = 'True' if debug_mode == 'y' else 'False'

    notifications = input("   Включить уведомления (Y/n): ").strip().lower()
    config['NOTIFICATION_ENABLED'] = 'False' if notifications == 'n' else 'True'

    # Создаем .env файл
    print("\n💾 Создание файла конфигурации...")

    env_content = f"""# Конфигурация OnboardingBuddy Bot
# Создано мастером настройки {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# ========================================
# ОСНОВНЫЕ НАСТРОЙКИ БОТА
# ========================================

BOT_TOKEN={config['BOT_TOKEN']}
ADMIN_IDS={config['ADMIN_IDS']}
DEBUG_MODE={config['DEBUG_MODE']}

# ========================================
# БАЗА ДАННЫХ И ЛОГИРОВАНИЕ
# ========================================

DATABASE_PATH=data/onboarding.db
LOG_LEVEL=INFO
LOG_FILE=data/logs/bot.log

# ========================================
# ИНФОРМАЦИЯ О КОМПАНИИ
# ========================================

COMPANY_NAME={config['COMPANY_NAME']}

# HR отдел
HR_EMAIL={config['HR_EMAIL']}
HR_TELEGRAM={config['HR_TELEGRAM']}
HR_PHONE={config['HR_PHONE']}

# Техническая поддержка
SUPPORT_EMAIL={config['SUPPORT_EMAIL']}
SUPPORT_TELEGRAM={config['SUPPORT_TELEGRAM']}
SUPPORT_PHONE={config['SUPPORT_PHONE']}

# ========================================
# РЕСУРСЫ И ССЫЛКИ КОМПАНИИ
# ========================================

COMPANY_SITE={config['COMPANY_SITE']}
TEAM_PAGE={config['TEAM_PAGE']}
HANDBOOK_URL={config['HANDBOOK_URL']}
CALENDAR_URL=https://calendar.company.ru
PORTAL_URL=https://portal.company.ru

# ========================================
# ССЫЛКИ НА ВСТРЕЧИ И ПЛАНЕРКИ
# ========================================

MEETING_GENERAL={config['MEETING_GENERAL']}
MEETING_IT={config['MEETING_IT']}
MEETING_MARKETING={config['MEETING_MARKETING']}
MEETING_HR=https://meet.company.ru/hr

# ========================================
# НАСТРОЙКИ УВЕДОМЛЕНИЙ
# ========================================

NOTIFICATION_ENABLED={config['NOTIFICATION_ENABLED']}
FEEDBACK_NOTIFICATION=True

# ========================================
# НАСТРОЙКИ РАССЫЛКИ
# ========================================

BROADCAST_DELAY=0.1
MAX_MESSAGE_LENGTH=4000

# ========================================
# НАСТРОЙКИ ОНБОРДИНГА
# ========================================

MAX_ONBOARDING_STAGES=10
AUTO_REMINDERS=False
REMINDER_INTERVAL_DAYS=3
"""

    try:
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)

        print("✅ Файл .env успешно создан!")

        # Создаем структуру директорий
        print("\n📁 Создание структуры директорий...")
        create_directory_structure()

        print("\n🎉 Настройка завершена!")
        print("\n📋 Следующие шаги:")
        print("1. Проверьте настройки в файле .env")
        print("2. Установите зависимости: pip install -r requirements.txt")
        print("3. Запустите бота: python main.py")
        print("\n📞 При возникновении проблем обращайтесь в техподдержку.")

    except Exception as e:
        print(f"❌ Ошибка создания файла .env: {e}")


def create_directory_structure():
    """Создание структуры директорий"""
    directories = [
        'data',
        'data/logs',
        'data/exports',
        'data/backups',
        'data/temp',
        'config',
        'bot',
        'handlers',
        'database',
        'utils',
        'services'
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)

        # Создаем __init__.py файлы для Python пакетов
        if directory in ['config', 'bot', 'handlers', 'database', 'utils', 'services']:
            init_file = os.path.join(directory, '__init__.py')
            if not os.path.exists(init_file):
                with open(init_file, 'w') as f:
                    f.write(f'"""\n{directory.title()} модуль OnboardingBuddy\n"""\n')

    print("✅ Структура директорий создана!")


def validate_setup():
    """Валидация настройки"""
    issues = []

    # Проверяем .env файл
    if not os.path.exists('.env'):
        issues.append("❌ Файл .env не найден")

    # Проверяем директории
    required_dirs = ['data', 'data/logs']
    for directory in required_dirs:
        if not os.path.exists(directory):
            issues.append(f"❌ Директория {directory} не найдена")

    # Проверяем requirements.txt
    if not os.path.exists('requirements.txt'):
        issues.append("❌ Файл requirements.txt не найден")

    if issues:
        print("⚠️ Обнаружены проблемы:")
        for issue in issues:
            print(f"  {issue}")
        return False
    else:
        print("✅ Настройка выглядит корректно!")
        return True


def create_systemd_service():
    """Создание systemd сервиса для Linux"""
    if os.name != 'posix':
        print("❌ Systemd доступен только в Linux")
        return

    current_dir = os.path.abspath('.')
    user = os.getenv('USER', 'ubuntu')

    service_content = f"""[Unit]
Description=OnboardingBuddy Telegram Bot
After=network.target

[Service]
Type=simple
User={user}
WorkingDirectory={current_dir}
ExecStart=/usr/bin/python3 {current_dir}/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""

    service_file = 'onboarding-buddy.service'

    try:
        with open(service_file, 'w') as f:
            f.write(service_content)

        print(f"✅ Systemd сервис создан: {service_file}")
        print("\nДля установки выполните:")
        print(f"sudo cp {service_file} /etc/systemd/system/")
        print("sudo systemctl daemon-reload")
        print("sudo systemctl enable onboarding-buddy")
        print("sudo systemctl start onboarding-buddy")

    except Exception as e:
        print(f"❌ Ошибка создания systemd сервиса: {e}")


if __name__ == '__main__':
    from datetime import datetime

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'wizard':
            setup_wizard()
        elif command == 'validate':
            validate_setup()
        elif command == 'systemd':
            create_systemd_service()
        elif command == 'dirs':
            create_directory_structure()
        else:
            print("❓ Неизвестная команда")
            print("Доступные команды: wizard, validate, systemd, dirs")
    else:
        setup_wizard()