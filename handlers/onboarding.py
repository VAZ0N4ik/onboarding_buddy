# handlers/onboarding.py
"""
Обработчики онбординга
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from config.settings import settings
from database.manager import db_manager
from database.models import UserStatus, OnboardingStage
from bot.keyboards import Keyboards
from datetime import datetime
from utils.helpers import format_datetime

logger = logging.getLogger(__name__)


async def handle_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главный обработчик онбординга"""
    user_id = update.effective_user.id
    user = db_manager.get_user(user_id)

    if not user:
        await update.message.reply_text(
            "⚠️ Пользователь не найден. Используйте /start для регистрации."
        )
        return

    db_manager.log_user_action(user_id, "onboarding_access", "Обратился к разделу онбординга")

    # Проверяем статус пользователя
    if user.status == UserStatus.NEW:
        text = """
⚠️ Для начала онбординга необходимо завершить пребординг

Пожалуйста, сначала пройдите раздел "🚀 Пребординг" для подготовки документов.

📋 Что включает пребординг:
• Подготовка необходимых документов
• Отправка сканов HR-менеджеру  
• Получение подписанных документов

После завершения пребординга вы сможете перейти к онбордингу.
"""
        await update.message.reply_text(text)
        return

    elif user.status == UserStatus.PREBOARDING:
        text = """
🔄 Пребординг в процессе

Сначала завершите отправку документов в разделе "🚀 Пребординг".

📧 Не забудьте:
• Отправить все документы на {settings.HR_EMAIL}
• Дождаться подтверждения от HR-менеджера
• Получить подписанные документы

После этого онбординг станет доступен.
"""
        await update.message.reply_text(text)
        return

    elif user.status == UserStatus.COMPLETED:
        text = """
🎉 Онбординг уже завершен!

Поздравляем! Вы успешно прошли все этапы адаптации.

📚 Что доступно:
• ❓ FAQ - ответы на вопросы
• 👥 Контакты сотрудников
• 📞 Поддержка
• 💬 Обратная связь

Если нужна помощь, обращайтесь к коллегам или в поддержку!
"""
        await update.message.reply_text(text)
        return

    # Основной онбординг для статусов PREBOARDED и ONBOARDING
    if user.status == UserStatus.PREBOARDED:
        # Переводим в статус онбординга
        db_manager.update_user_stage(user_id, OnboardingStage.ONBOARDING_START, UserStatus.ONBOARDING)

        text = f"""
🎉 Отлично! Добро пожаловать в команду {settings.COMPANY_NAME}!

Поздравляем с официальным зачислением в штат! 

📋 Что включает онбординг:
• Получение корпоративных доступов
• Знакомство с командой и процессами
• Ознакомление с рабочими инструментами
• Информация о планерках и встречах

⏱️ Примерное время: 20-30 минут

🎯 Цель онбординга:
Помочь вам быстро адаптироваться и стать полноценным членом команды.

Готовы начать знакомство с компанией?
"""
    else:
        # Пользователь уже в процессе онбординга
        progress_bar = Keyboards.get_progress_visualization(user.stage)

        text = f"""
🚀 Продолжаем онбординг

📊 Ваш прогресс: {user.stage}/10 этапов
{progress_bar}

🎯 Текущий этап: {OnboardingStage.get_stage_name(user.stage)}

Продолжим с того места, где остановились?
"""

    keyboard = Keyboards.get_start_onboarding()
    await update.message.reply_text(text, reply_markup=keyboard)


async def handle_onboarding_callback(update, context):
    """Обработчик callback-ов онбординга"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    callback_data = query.data

    if callback_data == "start_onboarding":
        await start_onboarding_process(query, context)
    elif callback_data == "email_received":
        await handle_email_received(query, context)
    elif callback_data == "email_not_received":
        await handle_email_not_received(query, context)
    elif callback_data == "team_intro":
        await handle_team_intro(query, context)
    elif callback_data == "meetings":
        await handle_meetings_info(query, context)
    elif callback_data == "complete_onboarding":
        await complete_onboarding(query, context)


async def start_onboarding_process(query, context):
    """Начать процесс онбординга"""
    user_id = query.from_user.id
    user = db_manager.get_user(user_id)

    # Обновляем этап если нужно
    if user.stage < OnboardingStage.EMAIL_ACCESS:
        db_manager.update_user_stage(user_id, OnboardingStage.EMAIL_ACCESS)

    db_manager.log_user_action(user_id, "onboarding_start", "Начал процесс онбординга")

    text = f"""
🎉 Начинаем онбординг!

📧 Шаг 1: Корпоративная почта

Первым делом вам нужно получить доступ к корпоративной системе.

Что должно произойти:
• HR-менеджер отправляет данные для входа на вашу личную почту
• Вы получаете логин и пароль для корпоративной почты
• Через корпоративную почту открывается доступ ко всем ресурсам

📧 Проверьте почту! 
Письмо должно прийти от: {settings.HR_EMAIL}

В письме будут:
• Логин и пароль
• Ссылки на корпоративные ресурсы
• Инструкции по первому входу

❓ Получили ли вы доступ к корпоративной почте?
"""

    keyboard = Keyboards.get_email_access()
    await query.edit_message_text(text, reply_markup=keyboard)


async def handle_email_received(query, context):
    """Обработка получения доступа к почте"""
    user_id = query.from_user.id

    db_manager.update_user_stage(user_id, OnboardingStage.TEAM_INTRO)
    db_manager.log_user_action(user_id, "email_access_confirmed", "Подтвердил получение доступа к почте")

    text = f"""
🎉 Отлично! Доступ к корпоративной системе получен!

✅ Что теперь доступно:

📧 Корпоративная почта - основной канал коммуникации
💬 Корпоративные чаты - общение с командой
📅 Календарь - встречи и события
📁 Облачное хранилище - рабочие документы
🔧 Рабочие инструменты - системы управления проектами

Важные ресурсы:
• Портал сотрудника: {settings.PORTAL_URL if hasattr(settings, 'PORTAL_URL') else settings.COMPANY_SITE}
• Календарь событий: {settings.CALENDAR_URL if hasattr(settings, 'CALENDAR_URL') else 'В корпоративной почте'}
• Техподдержка: {settings.SUPPORT_EMAIL}

🎯 Что дальше?
Давайте познакомимся с командой и узнаем о рабочих процессах!
"""

    keyboard = Keyboards.get_onboarding_next()
    await query.edit_message_text(text, reply_markup=keyboard)


async def handle_email_not_received(query, context):
    """Обработка отсутствия доступа к почте"""
    user_id = query.from_user.id
    db_manager.log_user_action(user_id, "email_access_issue", "Не получил доступ к корпоративной почте")

    text = f"""
😔 Не получили доступ? Решим эту проблему!

🔧 Возможные причины:
• Письмо попало в спам
• Указана неверная почта при оформлении
• Техническая задержка в системе

📞 Немедленно обратитесь к HR-менеджеру:

👤 Федосеенко С. М.
📧 Email: {settings.HR_EMAIL}
📱 Telegram: {settings.HR_TELEGRAM}
📞 Телефон: {settings.HR_PHONE if hasattr(settings, 'HR_PHONE') else '+7 (xxx) xxx-xx-xx'}

💬 Что сообщить HR:
"Не получил доступ к корпоративной почте для онбординга. Мой ID в боте: {user_id}"

⏰ Время работы HR: Пн-Пт 9:00-18:00

После получения доступа возвращайтесь сюда для продолжения онбординга.
"""

    keyboard = Keyboards.get_email_retry()
    await query.edit_message_text(text, reply_markup=keyboard)


async def handle_team_intro(query, context):
    """Знакомство с командой"""
    user_id = query.from_user.id

    db_manager.update_user_stage(user_id, OnboardingStage.MEETINGS)
    db_manager.log_user_action(user_id, "team_intro", "Изучил информацию о команде")

    text = f"""
👥 Знакомство с командой {settings.COMPANY_NAME}

🌐 Корпоративный сайт с командой:
{settings.TEAM_PAGE}

📊 Что вы найдете на сайте:
• Организационная структура - кто за что отвечает
• Профили сотрудников - фото, должности, навыки
• Контактная информация - кто к кому обращаться
• Структура отделов - как организована работа

👤 Ваш непосредственный руководитель:
• Информация будет отправлена на корпоративную почту
• Он свяжется с вами в первые дни работы
• Подготовит план адаптации и задачи

📖 Справочник сотрудника:
{settings.HANDBOOK_URL}

В справочнике:
• Правила и процедуры компании
• Организационные моменты
• Контакты всех отделов
• Инструкции по работе с системами
• Корпоративные стандарты

💡 Совет: Изучите эти ресурсы в свободное время - это поможет быстрее влиться в команду!
"""

    keyboard = Keyboards.get_team_intro_next()
    await query.edit_message_text(text, reply_markup=keyboard)


async def handle_meetings_info(query, context):
    """Информация о планерках и встречах"""
    user_id = query.from_user.id

    db_manager.update_user_stage(user_id, OnboardingStage.COMPLETE)
    db_manager.log_user_action(user_id, "meetings_info", "Изучил информацию о планерках")

    text = f"""
📅 Планерки и встречи команды

🔗 Регулярные встречи:

🏢 Общая планерка
• Ссылка: {settings.MEETING_GENERAL}
• Время: Понедельник, 10:00
• Участники: Вся команда
• Цель: Обсуждение планов на неделю

💻 IT-отдел
• Ссылка: {settings.MEETING_IT}  
• Время: Среда, 11:00
• Участники: Техническая команда
• Цель: Технические вопросы и задачи

📈 Маркетинг
• Ссылка: {settings.MEETING_MARKETING}
• Время: Пятница, 14:00
• Участники: Отдел маркетинга
• Цель: Продвижение и реклама

👥 HR-встречи
• Ссылка: {settings.MEETING_HR if hasattr(settings, 'MEETING_HR') else 'В корпоративном календаре'}
• Время: Первая пятница месяца, 15:00
• Участники: Вся команда
• Цель: HR-вопросы, адаптация, feedback

📧 Важно:
• Все приглашения приходят на корпоративную почту
• Обязательно участвуйте в планерках вашего отдела
• При невозможности участия - предупреждайте заранее

📝 Первая неделя:
• Посетите общую планерку для знакомства
• Участвуйте в планерке вашего отдела
• Руководитель проведет индивидуальную встречу
"""

    keyboard = Keyboards.get_meetings_next()
    await query.edit_message_text(text, reply_markup=keyboard)


async def complete_onboarding(query, context):
    """Завершение онбординга"""
    user_id = query.from_user.id

    db_manager.update_user_stage(user_id, 10, UserStatus.COMPLETED)
    db_manager.log_user_action(user_id, "onboarding_completed", "Успешно завершил онбординг")

    # Уведомляем администраторов о завершении
    user = db_manager.get_user(user_id)
    admin_message = f"""
🎉 Онбординг завершен!

👤 Сотрудник: {user.full_name} (@{query.from_user.username})
📊 Статус: Онбординг завершен
📅 Дата завершения: {format_datetime(datetime.now())}
🎯 Этапов пройдено: 10/10

Новый сотрудник готов к работе!
"""

    # Отправляем уведомление администраторам
    for admin_id in settings.ADMIN_IDS:
        try:
            await context.bot.send_message(chat_id=admin_id, text=admin_message)
        except Exception as e:
            logger.error(f"Не удалось отправить уведомление администратору {admin_id}: {e}")

    text = f"""
🎉🎊 ПОЗДРАВЛЯЕМ! 🎊🎉

Онбординг успешно завершен!

Теперь вы полноправный член команды {settings.COMPANY_NAME}!

✅ Что вы прошли:
• Пребординг и подготовка документов
• Получение корпоративных доступов  
• Знакомство с командой и процессами
• Информация о планерках и встречах

🎯 Что дальше:
• Активно участвуйте в планерках вашего отдела
• Изучайте корпоративные ресурсы и документацию
• Общайтесь с коллегами и задавайте вопросы
• Развивайтесь профессионально с поддержкой команды

📞 Если нужна помощь:
• ❓ FAQ - ответы на частые вопросы
• 👥 Контакты - связь с коллегами
• 📞 Поддержка - техническая помощь
• 💬 Обратная связь - поделиться мнением

🚀 Добро пожаловать в команду!
Желаем успехов в работе и профессиональном росте!

---
*Этот бот всегда доступен для справок и помощи.*
"""

    await query.edit_message_text(text)


async def get_onboarding_status(user_id: int) -> str:
    """Получить статус онбординга для пользователя"""
    user = db_manager.get_user(user_id)

    if not user:
        return "Пользователь не найден"

    if user.status in [UserStatus.NEW, UserStatus.PREBOARDING]:
        return "Не доступен (завершите пребординг)"
    elif user.status == UserStatus.PREBOARDED:
        return "Готов к началу"
    elif user.status == UserStatus.ONBOARDING:
        stage_status = {
            OnboardingStage.ONBOARDING_START: "Начало процесса",
            OnboardingStage.EMAIL_ACCESS: "Получение доступов",
            OnboardingStage.TEAM_INTRO: "Знакомство с командой",
            OnboardingStage.MEETINGS: "Изучение планерок",
        }
        return stage_status.get(user.stage, f"Этап {user.stage}")
    elif user.status == UserStatus.COMPLETED:
        return "Завершен ✅"
    else:
        return "Неизвестный статус"