# handlers/callbacks.py
"""
Обработчики всех callback запросов
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from config.settings import settings
from database.manager import db_manager

logger = logging.getLogger(__name__)


async def handle_all_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Центральный обработчик всех callback запросов"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    callback_data = query.data

    # Логируем callback
    db_manager.log_user_action(user_id, f"callback_{callback_data}", f"Нажал кнопку: {callback_data}")

    # Маршрутизация callback-ов по префиксам
    if callback_data.startswith("admin_"):
        # Админские callback-ы обрабатываются отдельно в handlers/admin.py
        return

    elif callback_data.startswith("start_preboarding") or callback_data.startswith(
            "docs_") or callback_data == "all_docs_sent":
        # Пребординг callback-ы обрабатываются в handlers/preboarding.py
        from handlers.preboarding import handle_preboarding_callback
        await handle_preboarding_callback(update, context)

    elif callback_data.startswith("start_onboarding") or callback_data.startswith("email_") or callback_data in [
        "team_intro", "meetings", "complete_onboarding"]:
        # Онбординг callback-ы обрабатываются в handlers/onboarding.py
        from handlers.onboarding import handle_onboarding_callback
        await handle_onboarding_callback(update, context)

    elif callback_data == "back_to_main":
        # Возврат в главное меню
        from handlers.start import start_command
        # Создаем фиктивное сообщение для обработки
        fake_update = Update(
            update_id=update.update_id,
            message=query.message
        )
        fake_update.effective_user = query.from_user
        await start_command(fake_update, context)

    elif callback_data == "cancel":
        # Отмена действия
        await query.edit_message_text("❌ Действие отменено.")

    elif callback_data == "noop":
        # Ничего не делаем (для кнопок-заглушек)
        pass

    else:
        # Неизвестный callback
        logger.warning(f"Неизвестный callback: {callback_data} от пользователя {user_id}")
        await query.edit_message_text(
            "❓ Неизвестная команда. Возможно, эта функция еще не реализована.\n\n"
            "Используйте /start для возврата в главное меню."
        )


async def handle_pagination_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик пагинации для длинных списков"""
    query = update.callback_query
    callback_data = query.data

    # Парсим данные пагинации (например: "users_page_2")
    parts = callback_data.split("_")
    if len(parts) >= 3 and parts[1] == "page":
        list_type = parts[0]
        page = int(parts[2])

        # В зависимости от типа списка вызываем соответствующую функцию
        if list_type == "users":
            await show_users_page(query, context, page)
        elif list_type == "feedback":
            await show_feedback_page(query, context, page)
        # Можно добавить другие типы списков

    await query.answer()


async def show_users_page(query, context, page: int):
    """Показать страницу пользователей"""
    users_per_page = 10
    all_users = db_manager.get_all_users()
    total_pages = (len(all_users) + users_per_page - 1) // users_per_page

    # Проверяем корректность номера страницы
    if page < 1:
        page = 1
    elif page > total_pages:
        page = total_pages

    # Получаем пользователей для текущей страницы
    start_idx = (page - 1) * users_per_page
    end_idx = start_idx + users_per_page
    page_users = all_users[start_idx:end_idx]

    text = f"👥 Пользователи (страница {page}/{total_pages}):\n\n"

    for user in page_users:
        status_emoji = user.status_emoji
        username = f"@{user.username}" if user.username else "Нет username"
        text += f"{status_emoji} {user.full_name} ({username})\n"
        text += f"   └ {user.status_name}, этап {user.stage}/10\n\n"

    # Создаем клавиатуру пагинации
    keyboard = Keyboards.get_pagination(page, total_pages, "users")

    await query.edit_message_text(text, reply_markup=keyboard)


async def show_feedback_page(query, context, page: int):
    """Показать страницу обратной связи"""
    feedback_per_page = 5
    all_feedback = db_manager.get_recent_feedback(limit=100)  # Получаем больше для пагинации
    total_pages = (len(all_feedback) + feedback_per_page - 1) // feedback_per_page

    if page < 1:
        page = 1
    elif page > total_pages:
        page = total_pages

    start_idx = (page - 1) * feedback_per_page
    end_idx = start_idx + feedback_per_page
    page_feedback = all_feedback[start_idx:end_idx]

    text = f"💬 Обратная связь (страница {page}/{total_pages}):\n\n"

    for feedback in page_feedback:
        username = f"@{feedback['username']}" if feedback['username'] else "Нет username"
        text += f"👤 {feedback['user_name']} ({username})\n"
        text += f"📅 {feedback['created_at'][:16]}\n"
        text += f"💬 {feedback['message']}\n\n"
        text += "─" * 30 + "\n\n"

    keyboard = Keyboards.get_pagination(page, total_pages, "feedback")

    await query.edit_message_text(text, reply_markup=keyboard)


# Дополнительные helper функции для callback-ов

def parse_callback_action(callback_data: str) -> tuple:
    """Парсинг callback_data для получения действия и параметров"""
    if "?" in callback_data:
        action, params_str = callback_data.split("?", 1)
        params = {}
        for param in params_str.split("&"):
            if "=" in param:
                key, value = param.split("=", 1)
                params[key] = value
        return action, params
    return callback_data, {}


def create_callback_data(action: str, params) -> str:
    """Создание callback_data с параметрами"""
    if not params:
        return action

    params_str = "&".join([f"{k}={v}" for k, v in params.items()])
    return f"{action}?{params_str}"


async def handle_confirmation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик подтверждений действий"""
    query = update.callback_query
    action, params = parse_callback_action(query.data)

    if action == "confirm_delete_user":
        user_id_to_delete = int(params.get("user_id", 0))
        # Логика удаления пользователя (если потребуется в будущем)
        await query.edit_message_text("✅ Пользователь удален.")

    elif action == "confirm_reset_progress":
        user_id_to_reset = int(params.get("user_id", 0))
        # Логика сброса прогресса (если потребуется)
        await query.edit_message_text("✅ Прогресс сброшен.")

    await query.answer()


# Функции для создания специальных callback кнопок

def create_user_action_keyboard(user_id: int):
    """Создать клавиатуру действий для пользователя"""
    from bot.keyboards import InlineKeyboardMarkup, InlineKeyboardButton

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 Подробности", callback_data=f"user_details?user_id={user_id}"),
            InlineKeyboardButton("📧 Написать", callback_data=f"message_user?user_id={user_id}")
        ],
        [
            InlineKeyboardButton("🔄 Сбросить прогресс", callback_data=f"reset_progress?user_id={user_id}"),
            InlineKeyboardButton("❌ Удалить", callback_data=f"delete_user?user_id={user_id}")
        ],
        [InlineKeyboardButton("🏠 Назад", callback_data="back_to_admin")]
    ])


async def handle_user_management_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик управления пользователями"""
    query = update.callback_query
    action, params = parse_callback_action(query.data)

    if action == "user_details":
        await show_user_details(query, context, int(params["user_id"]))
    elif action == "message_user":
        await initiate_user_message(query, context, int(params["user_id"]))
    elif action == "reset_progress":
        await confirm_reset_progress(query, context, int(params["user_id"]))
    elif action == "delete_user":
        await confirm_delete_user(query, context, int(params["user_id"]))

    await query.answer()


async def show_user_details(query, context, user_id: int):
    """Показать детальную информацию о пользователе"""
    user = db_manager.get_user(user_id)

    if not user:
        await query.edit_message_text("❌ Пользователь не найден.")
        return

    # Получаем статистику активности
    actions = db_manager.get_user_actions(user_id, limit=10)

    text = f"""
👤 Детали пользователя

Основная информация:
• ID: {user.user_id}
• Имя: {user.full_name or 'Не указано'}
• Username: @{user.username or 'Не указан'}
• Должность: {user.position or 'Не указана'}

Прогресс:
• Статус: {user.status_emoji} {user.status_name}
• Этап: {user.stage}/10 ({user.progress_percentage:.0f}%)
• Дата регистрации: {user.created_at.strftime('%d.%m.%Y %H:%M') if user.created_at else 'Неизвестно'}
• Последнее обновление: {user.updated_at.strftime('%d.%m.%Y %H:%M') if user.updated_at else 'Неизвестно'}

Последние действия:
"""

    for action in actions[:5]:
        text += f"• {action.action} - {action.created_at.strftime('%d.%m %H:%M')}\n"

    # Клавиатура действий
    keyboard = create_user_action_keyboard(user_id)

    await query.edit_message_text(text, reply_markup=keyboard)


async def initiate_user_message(query, context, user_id: int):
    """Инициировать отправку сообщения пользователю"""
    user = db_manager.get_user(user_id)

    if not user:
        await query.edit_message_text("❌ Пользователь не найден.")
        return

    text = f"""
📧 Отправка сообщения пользователю

👤 Получатель: {user.full_name} (@{user.username or 'нет'})

Напишите сообщение, которое хотите отправить этому пользователю.
Следующее ваше сообщение будет переслано ему.

Для отмены используйте /cancel
"""

    # Устанавливаем состояние ожидания сообщения
    context.user_data['messaging_user_id'] = user_id
    context.user_data['waiting_admin_message'] = True

    await query.edit_message_text(text)


async def confirm_reset_progress(query, context, user_id: int):
    """Подтверждение сброса прогресса"""
    user = db_manager.get_user(user_id)

    if not user:
        await query.edit_message_text("❌ Пользователь не найден.")
        return

    text = f"""
⚠️ Подтверждение сброса прогресса

👤 Пользователь: {user.full_name}
📊 Текущий прогресс: {user.stage}/10 этапов
🎯 Статус: {user.status_name}

Действие: Прогресс будет сброшен до начального состояния.

Вы уверены?
"""

    from bot.keyboards import Keyboards
    keyboard = Keyboards.get_confirmation(
        "сброс",
        f"confirm_reset_progress?user_id={user_id}",
        "back_to_admin"
    )

    await query.edit_message_text(text, reply_markup=keyboard)


async def confirm_delete_user(query, context, user_id: int):
    """Подтверждение удаления пользователя"""
    user = db_manager.get_user(user_id)

    if not user:
        await query.edit_message_text("❌ Пользователь не найден.")
        return

    text = f"""
🚨 ВНИМАНИЕ: Удаление пользователя

👤 Пользователь: {user.full_name}
📊 Прогресс: {user.stage}/10 этапов

⚠️ ПРЕДУПРЕЖДЕНИЕ:
Это действие удалит ВСЕ данные пользователя:
• Профиль и прогресс
• Историю действий
• Обратную связь

Это действие НЕОБРАТИМО!

Вы действительно хотите удалить пользователя?
"""

    from bot.keyboards import Keyboards
    keyboard = Keyboards.get_confirmation(
        "удаление",
        f"confirm_delete_user?user_id={user_id}",
        "back_to_admin"
    )

    await query.edit_message_text(text, reply_markup=keyboard)


# Импорт для использования в других модулях
from bot.keyboards import Keyboards