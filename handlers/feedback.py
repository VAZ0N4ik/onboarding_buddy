# handlers/feedback.py
"""
Обработчики обратной связи и прогресса
"""
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

from config.settings import settings
from database.manager import db_manager
from database.models import UserStatus, OnboardingStage
from bot.keyboards import Keyboards
from utils.helpers import format_datetime, create_progress_bar

logger = logging.getLogger(__name__)


async def handle_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик начала обратной связи"""
    user_id = update.effective_user.id
    db_manager.log_user_action(user_id, "feedback_start", "Начал оставлять обратную связь")

    text = f"""
💬 Обратная связь

Ваше мнение очень важно для нас! Мы стремимся постоянно улучшать процессы работы и создавать комфортную среду для всех сотрудников.

🎯 Что вы можете нам сообщить:

📝 Предложения по улучшению
• Процессы онбординга и адаптации
• Рабочие инструменты и системы
• Организация рабочего пространства
• Внутренние коммуникации

🔧 Проблемы и сложности
• Технические неудобства
• Организационные вопросы
• Недостаток информации
• Любые блокеры в работе

💡 Идеи и инициативы
• Новые инструменты или процессы
• Мероприятия и активности
• Обучающие программы
• Улучшения в работе команды

😊 Позитивные отзывы
• Что вам нравится в компании
• Успешные кейсы и достижения
• Благодарности коллегам
• Примеры хорошей работы

---

💌 Как оставить обратную связь:

🤖 Через этого бота (анонимно)
Просто напишите ваше сообщение следующим текстом. Оно будет передано HR-отделу и руководству.

📧 По email
{settings.HR_EMAIL} - для официальных обращений

💬 Лично
Обратитесь к HR-менеджеру: {settings.HR_TELEGRAM}

📋 Через корпоративный портал
Раздел "Обратная связь" на {settings.COMPANY_SITE}

---

🔒 Конфиденциальность:
• Обратная связь через бота передается HR анонимно
• Ваши персональные данные не разглашаются без согласия
• Конструктивная критика приветствуется
• Негативные отзывы рассматриваются как возможности для роста

📈 Что происходит с вашей обратной связью:
1. Поступление - сообщение получает HR-отдел
2. Анализ - команда изучает предложение или проблему
3. Планирование - разрабатывается план улучшений
4. Реализация - внедряются изменения
5. Отчет - результаты сообщаются всей команде

---

✍️ Напишите ваше сообщение прямо сейчас!

Для отмены используйте /start для возврата в главное меню.
"""

    # Устанавливаем флаг ожидания обратной связи
    context.user_data['waiting_feedback'] = True

    await update.message.reply_text(text)


async def handle_feedback_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик сообщений обратной связи"""
    user_id = update.effective_user.id

    # Проверяем, ждем ли мы обратную связь от этого пользователя
    if not context.user_data.get('waiting_feedback', False):
        # Это не обратная связь, обрабатываем как обычное сообщение
        from handlers.start import handle_main_menu
        await handle_main_menu(update, context)
        return

    # Получаем текст сообщения
    feedback_text = update.message.text

    # Проверяем, не является ли это командой
    if feedback_text.startswith('/'):
        context.user_data['waiting_feedback'] = False
        await update.message.reply_text(
            "❌ Отправка обратной связи отменена.\n"
            "Используйте команды или кнопки меню для навигации."
        )
        return

    # Сохраняем обратную связь
    try:
        feedback = db_manager.save_feedback(user_id, feedback_text)
        db_manager.log_user_action(
            user_id,
            "feedback_sent",
            f"Отправил обратную связь: {feedback_text[:50]}..."
        )

        # Получаем информацию о пользователе для уведомления админов
        user = db_manager.get_user(user_id)
        user_name = user.full_name if user else "Неизвестный пользователь"
        username = f"@{update.effective_user.username}" if update.effective_user.username else "Нет username"

        # Уведомляем администраторов о новой обратной связи
        if settings.FEEDBACK_NOTIFICATION:
            admin_message = f"""
🔔 Новая обратная связь

👤 От пользователя: {user_name} ({username})
📅 Время: {format_datetime(datetime.now())}
📊 Статус пользователя: {user.status_name if user else 'Неизвестно'}

💬 Сообщение:
{feedback_text}

---
💡 *Ответить пользователю можно через {settings.HR_TELEGRAM}*
"""

            # Отправляем уведомление всем администраторам
            for admin_id in settings.ADMIN_IDS:
                try:
                    await context.bot.send_message(chat_id=admin_id, text=admin_message)
                except Exception as e:
                    logger.error(f"Не удалось отправить уведомление администратору {admin_id}: {e}")

        # Убираем флаг ожидания обратной связи
        context.user_data['waiting_feedback'] = False

        # Отправляем подтверждение пользователю
        success_message = f"""
✅ Спасибо за обратную связь!

Ваше сообщение успешно передано HR-отделу и руководству компании.

📋 Что дальше:
• Ваше предложение будет рассмотрено в течение 3 рабочих дней
• При необходимости с вами свяжется HR-менеджер
• Результаты рассмотрения будут сообщены всей команде

💡 Важно:
Мы ценим каждое мнение и стремимся постоянно улучшать рабочие процессы. Ваша обратная связь помогает нам становиться лучше!

📞 Контакты для дополнительных вопросов:
• HR-отдел: {settings.HR_EMAIL}
• Telegram: {settings.HR_TELEGRAM}

---
Для возврата в главное меню используйте /start
"""

        await update.message.reply_text(success_message)

    except Exception as e:
        logger.error(f"Ошибка сохранения обратной связи от пользователя {user_id}: {e}")

        # Убираем флаг ожидания обратной связи даже при ошибке
        context.user_data['waiting_feedback'] = False

        await update.message.reply_text(
            "😔 Произошла ошибка при отправке обратной связи.\n"
            f"Пожалуйста, обратитесь напрямую в HR-отдел: {settings.HR_TELEGRAM}\n\n"
            "Для возврата в главное меню используйте /start"
        )


async def handle_progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик просмотра прогресса пользователя"""
    user_id = update.effective_user.id
    user = db_manager.get_user(user_id)

    db_manager.log_user_action(user_id, "progress_check", "Проверил свой прогресс")

    if not user:
        await update.message.reply_text(
            "❓ Данные о прогрессе не найдены.\n"
            "Используйте /start для регистрации."
        )
        return

    # Создаем прогресс-бар
    progress_bar = create_progress_bar(user.stage, 10, 20)
    progress_percentage = user.progress_percentage

    # Определяем статус и следующие шаги
    status_emoji = user.status_emoji
    status_name = user.status_name

    # Получаем информацию о следующем этапе
    next_step = get_next_step_description(user)

    # Время с момента регистрации
    time_since_start = ""
    if user.created_at:
        time_diff = datetime.now() - user.created_at
        days = time_diff.days
        hours = time_diff.seconds // 3600

        if days > 0:
            time_since_start = f"{days} дн."
            if hours > 0:
                time_since_start += f" {hours} ч."
        elif hours > 0:
            time_since_start = f"{hours} ч."
        else:
            time_since_start = "меньше часа"

    # Последняя активность
    recent_actions = db_manager.get_user_actions(user_id, limit=3)
    last_activity = ""
    if recent_actions:
        last_action = recent_actions[0]
        last_activity = f"{last_action.action} - {format_datetime(last_action.created_at, 'short')}"

    text = f"""
📊 Ваш прогресс в {settings.COMPANY_NAME}

👤 Информация о профиле:
• Имя: {user.full_name or 'Не указано'}
• Username: @{update.effective_user.username or 'Не указан'}
• Должность: {user.position or 'Не указана'}

---

🎯 Текущий статус:
{status_emoji} {status_name}

📈 Прогресс адаптации:
Этап {user.stage} из 10 ({progress_percentage:.0f}%)

{progress_bar}

Текущий этап: {OnboardingStage.get_stage_name(user.stage)}

---

🎯 Следующие шаги:
{next_step}

---

📅 Временная статистика:
• Дата регистрации: {format_datetime(user.created_at, 'date') if user.created_at else 'Неизвестно'}
• Время в системе: {time_since_start}
• Последнее обновление: {format_datetime(user.updated_at, 'short') if user.updated_at else 'Неизвестно'}

📋 Последняя активность:
{last_activity or 'Нет данных'}

---

{get_progress_recommendations(user)}

📞 Нужна помощь?
• HR-отдел: {settings.HR_TELEGRAM}
• Техподдержка: {settings.SUPPORT_TELEGRAM}
• Обратная связь: используйте раздел "💬 Обратная связь"
"""

    await update.message.reply_text(text)


def get_next_step_description(user) -> str:
    """Получить описание следующего шага для пользователя"""
    if user.status == UserStatus.NEW:
        return "• Начните с раздела '🚀 Пребординг' для подготовки документов"

    elif user.status == UserStatus.PREBOARDING:
        if user.stage < OnboardingStage.DOCUMENTS_MAIN:
            return "• Ознакомьтесь с требуемыми документами и отправьте их"
        elif user.stage < OnboardingStage.DOCUMENTS_COMPLETE:
            return "• Завершите отправку всех необходимых документов"
        else:
            return "• Дождитесь обработки документов HR-менеджером"

    elif user.status == UserStatus.PREBOARDED:
        return "• Переходите к разделу '📋 Онбординг' для продолжения адаптации"

    elif user.status == UserStatus.ONBOARDING:
        if user.stage < OnboardingStage.EMAIL_ACCESS:
            return "• Получите доступ к корпоративной почте"
        elif user.stage < OnboardingStage.TEAM_INTRO:
            return "• Изучите информацию о команде и структуре компании"
        elif user.stage < OnboardingStage.MEETINGS:
            return "• Ознакомьтесь с планерками и рабочими процессами"
        else:
            return "• Завершите онбординг в соответствующем разделе"

    elif user.status == UserStatus.COMPLETED:
        return "• 🎉 Все этапы пройдены! Добро пожаловать в команду!\n• Используйте бота для получения справочной информации"

    return "• Продолжайте процесс адаптации согласно инструкциям"


def get_progress_recommendations(user) -> str:
    """Получить рекомендации на основе прогресса пользователя"""
    if user.status == UserStatus.NEW:
        return """
🎯 Рекомендации:
• Начните с пребординга - это займет 15-20 минут
• Подготовьте сканы документов заранее
• При вопросах обращайтесь в HR-отдел
"""

    elif user.status == UserStatus.PREBOARDING:
        return """
🎯 Рекомендации:
• Отправляйте документы качественными сканами или фото
• Проверьте папку "Спам" в почте для писем от HR
• В ожидании обработки изучите раздел "Полезная информация"
"""

    elif user.status == UserStatus.PREBOARDED:
        return """
🎯 Рекомендации:
• Проверьте корпоративную почту для получения доступов
• Изучите корпоративный сайт и структуру команды
• Подготовьтесь к первому рабочему дню
"""

    elif user.status == UserStatus.ONBOARDING:
        return """
🎯 Рекомендации:
• Активно участвуйте в планерках отдела
• Знакомьтесь с коллегами и задавайте вопросы
• Изучайте корпоративные инструменты и процессы
"""

    elif user.status == UserStatus.COMPLETED:
        return """
🎉 Поздравляем с завершением адаптации!
• Вы успешно интегрировались в команду
• Продолжайте использовать бота для справочной информации
• Делитесь обратной связью для улучшения процессов
"""

    return ""


async def get_user_progress_stats(user_id: int) -> dict:
    """Получить статистику прогресса пользователя"""
    user = db_manager.get_user(user_id)
    actions = db_manager.get_user_actions(user_id, limit=100)

    if not user:
        return {}

    # Подсчитываем активность по дням
    activity_by_day = {}
    for action in actions:
        day = action.created_at.date().isoformat()
        activity_by_day[day] = activity_by_day.get(day, 0) + 1

    # Время на прохождение этапов
    time_to_complete = None
    if user.status == UserStatus.COMPLETED and user.created_at:
        time_diff = user.updated_at - user.created_at
        time_to_complete = time_diff.total_seconds() / 3600  # в часах

    return {
        'user': user.to_dict(),
        'total_actions': len(actions),
        'activity_by_day': activity_by_day,
        'time_to_complete_hours': time_to_complete,
        'current_stage': user.stage,
        'progress_percentage': user.progress_percentage
    }