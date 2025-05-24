# config/settings.py
"""
Конфигурация OnboardingBuddy Bot
"""
import os
from typing import List
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()


class Settings:
    """Настройки приложения"""

    # Основные настройки бота
    BOT_TOKEN: str = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
    ADMIN_IDS: List[int] = list(map(int, filter(None, os.getenv('ADMIN_IDS', '123456789').split(','))))
    DEBUG_MODE: bool = os.getenv('DEBUG_MODE', 'False').lower() == 'true'

    # База данных
    DATABASE_PATH: str = os.getenv('DATABASE_PATH', 'data/onboarding.db')

    # Логирование
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE: str = os.getenv('LOG_FILE', 'data/logs/bot.log')

    # Контакты компании
    COMPANY_NAME: str = os.getenv('COMPANY_NAME', 'АО "БигТайм АйТи"')
    HR_EMAIL: str = os.getenv('HR_EMAIL', 'hr@company.ru')
    HR_TELEGRAM: str = os.getenv('HR_TELEGRAM', '@hr_manager')
    HR_PHONE: str = os.getenv('HR_PHONE', '+7 (xxx) xxx-xx-xx')

    # Поддержка
    SUPPORT_EMAIL: str = os.getenv('SUPPORT_EMAIL', 'support@company.ru')
    SUPPORT_TELEGRAM: str = os.getenv('SUPPORT_TELEGRAM', '@tech_support')
    SUPPORT_PHONE: str = os.getenv('SUPPORT_PHONE', '+7 (xxx) xxx-xx-xx')

    # Ресурсы компании
    COMPANY_SITE: str = os.getenv('COMPANY_SITE', 'https://company-site.ru')
    TEAM_PAGE: str = os.getenv('TEAM_PAGE', 'https://company-site.ru/team')
    HANDBOOK_URL: str = os.getenv('HANDBOOK_URL', 'https://company-site.ru/handbook')
    CALENDAR_URL: str = os.getenv('CALENDAR_URL', 'https://calendar.company.ru')
    PORTAL_URL: str = os.getenv('PORTAL_URL', 'https://portal.company.ru')

    # Ссылки на встречи
    MEETING_GENERAL: str = os.getenv('MEETING_GENERAL', 'https://meet.company.ru/general')
    MEETING_IT: str = os.getenv('MEETING_IT', 'https://meet.company.ru/it')
    MEETING_MARKETING: str = os.getenv('MEETING_MARKETING', 'https://meet.company.ru/marketing')
    MEETING_HR: str = os.getenv('MEETING_HR', 'https://meet.company.ru/hr')

    # Настройки уведомлений
    NOTIFICATION_ENABLED: bool = os.getenv('NOTIFICATION_ENABLED', 'True').lower() == 'true'
    FEEDBACK_NOTIFICATION: bool = os.getenv('FEEDBACK_NOTIFICATION', 'True').lower() == 'true'

    # Настройки рассылки
    BROADCAST_DELAY: float = float(os.getenv('BROADCAST_DELAY', '0.1'))
    MAX_MESSAGE_LENGTH: int = int(os.getenv('MAX_MESSAGE_LENGTH', '4000'))

    # Настройки онбординга
    MAX_ONBOARDING_STAGES: int = int(os.getenv('MAX_ONBOARDING_STAGES', '10'))
    AUTO_REMINDERS: bool = os.getenv('AUTO_REMINDERS', 'False').lower() == 'true'
    REMINDER_INTERVAL_DAYS: int = int(os.getenv('REMINDER_INTERVAL_DAYS', '3'))

    @classmethod
    def validate(cls) -> List[str]:
        """Валидация настроек"""
        issues = []

        if cls.BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
            issues.append("❌ Не указан токен бота (BOT_TOKEN)")

        if cls.ADMIN_IDS == [123456789]:
            issues.append("⚠️ Используются ID администраторов по умолчанию")

        if cls.HR_EMAIL == 'hr@company.ru':
            issues.append("⚠️ Используется email HR по умолчанию")

        if cls.COMPANY_SITE == 'https://company-site.ru':
            issues.append("⚠️ Используется сайт компании по умолчанию")

        # Проверяем существование директорий
        os.makedirs(os.path.dirname(cls.DATABASE_PATH), exist_ok=True)
        os.makedirs(os.path.dirname(cls.LOG_FILE), exist_ok=True)

        return issues

    @classmethod
    def is_admin(cls, user_id: int) -> bool:
        """Проверка, является ли пользователь администратором"""
        return user_id in cls.ADMIN_IDS

    @classmethod
    def get_config_summary(cls) -> str:
        """Получить сводку конфигурации"""
        return f"""
🔧 Конфигурация OnboardingBuddy:
📱 Токен: {'✅ Настроен' if cls.BOT_TOKEN != 'YOUR_BOT_TOKEN_HERE' else '❌ Не настроен'}
👥 Администраторы: {len(cls.ADMIN_IDS)} чел.
🏢 Компания: {cls.COMPANY_NAME}
📧 HR: {cls.HR_EMAIL}
🌐 Сайт: {cls.COMPANY_SITE}
🗄️ БД: {cls.DATABASE_PATH}
📝 Логи: {cls.LOG_FILE}
🔔 Уведомления: {'✅' if cls.NOTIFICATION_ENABLED else '❌'}
"""


# Создаем экземпляр настроек
settings = Settings()