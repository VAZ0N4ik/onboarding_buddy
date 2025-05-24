# handlers/start.py
"""
Обработчики команд старта и главного меню
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from config.settings import settings
from database.manager import db_manager
from database.models import User, UserStatus
from bot.keyboards import Keyboards

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user

    # Получаем или создаем пользователя
    db_user = db_manager.get_user(user.id)

    if not db_user:
        # Создаем нового пользователя
        db_user = db_manager.create_user(
            user_id=user.id,
            username=user.username,
            full_name=user.full_name
        )
        db_manager.log_user_action(user.id, "start", "Первый запуск бота")

        welcome_text = f"""
🎉 Добро пожаловать в OnboardingBuddy, {user.first_name}!

Я ваш виртуальный помощник в компании {settings.COMPANY_NAME}. 
Помогу вам с адаптацией и отвечу на любые вопросы.

🚀 Для начала работы выберите нужный раздел в меню ниже.
"""
    else:
        db_manager.log_user_action(user.id, "start", "Возврат в главное меню")

        # Персонализированное приветствие в зависимости от статуса
        status_messages = {
            UserStatus.NEW: "Начните с раздела 'Пребординг' для подготовки документов.",
            UserStatus.PREBOARDING: "Продолжите процесс пребординга.",
            UserStatus.PREBOARDED: "Вы можете перейти к разделу 'Онбординг'.",
            UserStatus.ONBOARDING: "Продолжите процесс адаптации в разделе 'Онбординг'.",
            UserStatus.COMPLETED: "Добро пожаловать! Все этапы адаптации пройдены."
        }

        status_hint = status_messages.get(db_user.status, "")

        welcome_text = f"""
👋 Добро пожаловать обратно, {user.first_name}!

{db_user.status_emoji} Ваш статус: {db_user.status_name}
📊 Прогресс: {db_user.stage}/10 этапов

{status_hint}

Выберите нужный раздел:
"""

    await update.message.reply_text(
        welcome_text,
        reply_markup=Keyboards.get_main_menu()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда помощи"""
    user_id = update.effective_user.id
    db_manager.log_user_action(user_id, "help", "Запросил справку")

    help_text = f"""
🤖 OnboardingBuddy - Справка

Добро пожаловать в корпоративного бота {settings.COMPANY_NAME}!

📋 Основные разделы:
🚀 **Пребординг** - Подготовка документов перед оформлением на работу
📋 **Онбординг** - Пошаговый процесс адаптации в компании
📚 **Полезная информация** - Вся информация о компании и ресурсах
❓ **FAQ** - Ответы на самые частые вопросы сотрудников
👥 **Контакты** - Контакты сотрудников и отделов
📞 **Поддержка** - Техническая поддержка и экстренные контакты
💬 **Обратная связь** - Отправить сообщение HR-отделу
📊 **Мой прогресс** - Ваш текущий прогресс адаптации

🔧 Доступные команды:
/start - Главное меню и перезапуск бота
/help - Эта справка
/status - Краткая информация о вашем статусе
/contacts - Быстрый доступ к контактам
/admin - Панель администратора (только для админов)

💡 Как пользоваться:
• Используйте кнопки меню для навигации
• Следуйте инструкциям бота поэтапно
• При возникновении проблем обращайтесь в поддержку
• Все ваши действия сохраняются для отслеживания прогресса

📞 Техподдержка бота: {settings.SUPPORT_TELEGRAM}
📧 HR-отдел: {settings.HR_EMAIL}
"""

    await update.message.reply_text(help_text)


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Быстрая проверка статуса"""
    user_id = update.effective_user.id
    db_user = db_manager.get_user(user_id)

    if not db_user:
        await update.message.reply_text(
            "❓ Пользователь не найден. Используйте /start для регистрации."
        )
        return

    db_manager.log_user_action(user_id, "status_check", "Проверил статус через команду")

    progress_bar = Keyboards.get_progress_visualization(db_user.stage)

    status_text = f"""
📊 Ваш статус

{db_user.status_emoji} **Статус:** {db_user.status_name}
📈 **Прогресс:** {db_user.stage}/10 этапов
{progress_bar}

🎯 **Следующий шаг:** {_get_next_step_hint(db_user)}

📅 **Дата регистрации:** {db_user.created_at.strftime('%d.%m.%Y') if db_user.created_at else 'Неизвестно'}
🔄 **Последнее обновление:** {db_user.updated_at.strftime('%d.%m.%Y %H:%M') if db_user.updated_at else 'Неизвестно'}
"""

    await update.message.reply_text(status_text)


async def contacts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Быстрый доступ к контактам"""
    user_id = update.effective_user.id
    db_manager.log_user_action(user_id, "contacts_quick", "Быстрый доступ к контактам")

    contacts_text = f"""
📞 Быстрые контакты

🏢 **HR-отдел:**
👤 Федосеенко С. М.
📧 {settings.HR_EMAIL}
📱 {settings.HR_TELEGRAM}
📞 {settings.HR_PHONE}

💻 **IT-поддержка:**
📧 {settings.SUPPORT_EMAIL}
📱 {settings.SUPPORT_TELEGRAM}
📞 {settings.SUPPORT_PHONE}

🔥 **Экстренные случаи:**
📱 {settings.SUPPORT_TELEGRAM}

⏰ **Время работы поддержки:**
Пн-Пт: 9:00 - 18:00
Выходные: по срочным вопросам

Для полного списка контактов используйте раздел "👥 Контакты сотрудников"
"""

    await update.message.reply_text(contacts_text)


async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопок главного меню"""
    text = update.message.text
    user_id = update.effective_user.id

    # Импортируем обработчики других разделов
    from handlers.preboarding import handle_preboarding
    from handlers.onboarding import handle_onboarding
    from handlers.info import handle_useful_info
    from handlers.faq import handle_faq
    from handlers.contacts import handle_contacts, handle_support
    from handlers.feedback import handle_feedback, handle_progress

    # Маршрутизация по кнопкам главного меню
    if text == "🚀 Пребординг":
        await handle_preboarding(update, context)
    elif text == "📋 Онбординг":
        await handle_onboarding(update, context)
    elif text == "📚 Полезная информация":
        await handle_useful_info(update, context)
    elif text == "❓ FAQ":
        await handle_faq(update, context)
    elif text == "👥 Контакты сотрудников":
        await handle_contacts(update, context)
    elif text == "📞 Поддержка":
        await handle_support(update, context)
    elif text == "💬 Обратная связь":
        await handle_feedback(update, context)
    elif text == "📊 Мой прогресс":
        await handle_progress(update, context)
    elif text == "🏠 Главное меню":
        await start_command(update, context)
    else:
        # Неизвестная команда
        db_manager.log_user_action(user_id, "unknown_command", f"Неизвестная команда: {text}")
        await update.message.reply_text(
            "❓ Не понял вашу команду.\n\n"
            "Используйте кнопки меню для навигации или /help для справки."
        )


def _get_next_step_hint(user: User) -> str:
    """Получить подсказку о следующем шаге"""
    hints = {
        0: "Начните с раздела '🚀 Пребординг'",
        1: "Ознакомьтесь с требуемыми документами",
        2: "Отправьте основные документы",
        3: "Отправьте документы по ТК РФ",
        4: "Дождитесь обработки документов",
        5: "Переходите к разделу '📋 Онбординг'",
        6: "Получите доступ к корпоративной почте",
        7: "Изучите информацию о команде",
        8: "Ознакомьтесь с планерками",
        9: "Завершите онбординг",
        10: "Все этапы пройдены! 🎉"
    }

    return hints.get(user.stage, "Продолжайте процесс адаптации")


# Функция для проверки завершенности регистрации
def is_user_registered(user_id: int) -> bool:
    """Проверить, зарегистрирован ли пользователь"""
    user = db_manager.get_user(user_id)
    return user is not None


# Декоратор для проверки регистрации
def require_registration(func):
    """Декоратор для проверки регистрации пользователя"""

    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id

        if not is_user_registered(user_id):
            await update.message.reply_text(
                "⚠️ Сначала необходимо зарегистрироваться.\n"
                "Используйте команду /start"
            )
            return

        return await func(update, context)

    return wrapper