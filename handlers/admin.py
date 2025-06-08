# handlers/admin.py
"""
Обработчики административной панели
"""
import logging
import asyncio
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes

from config.settings import settings
from database.manager import db_manager
from database.models import UserStatus
from bot.keyboards import Keyboards
from utils.helpers import format_datetime, create_progress_bar, save_json

logger = logging.getLogger(__name__)


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /admin - административная панель"""
    user_id = update.effective_user.id

    if not settings.is_admin(user_id):
        await update.message.reply_text("❌ У вас нет прав администратора.")
        db_manager.log_user_action(user_id, "admin_denied", "Попытка доступа к админ-панели")
        return

    db_manager.log_user_action(user_id, "admin_access", "Вошел в админ-панель")

    # Получаем статистику
    stats = db_manager.get_user_statistics()
    popular_actions = db_manager.get_popular_actions(days=7, limit=5)
    recent_feedback = db_manager.get_recent_feedback(limit=5)

    # Формируем текст статистики
    stats_text = f"""
📊 Административная панель OnboardingBuddy

👥 Общая статистика:
• Всего пользователей: {stats['total_users']}
• Активных за неделю: {stats['active_week']}
• Процент завершения: {stats['completion_rate']}%
• Средний прогресс: {stats['avg_progress']}/10

📈 Распределение по статусам:
"""

    # Добавляем статистику по статусам
    status_names = {
        'new': '🆕 Новые',
        'preboarding': '🔄 Пребординг',
        'preboarded': '✅ Готовы к онбордингу',
        'onboarding': '🚀 Проходят онбординг',
        'completed': '🎉 Завершили онбординг'
    }

    for status, name in status_names.items():
        count = stats['status_stats'].get(status, 0)
        percentage = (count / stats['total_users'] * 100) if stats['total_users'] > 0 else 0
        stats_text += f"{name}: {count} ({percentage:.1f}%)\n"

    # Популярные действия
    if popular_actions:
        stats_text += "\n🔥 Популярные действия (неделя):\n"
        for action_data in popular_actions:
            stats_text += f"• {action_data['action']}: {action_data['count']}\n"

    # Последняя обратная связь
    if recent_feedback:
        stats_text += "\n📝 Последние отзывы:\n"
        for feedback in recent_feedback[:3]:
            short_message = feedback['message'][:50] + '...' if len(feedback['message']) > 50 else feedback['message']
            stats_text += f"👤 {feedback['user_name']}: {short_message}\n"

    stats_text += f"\n🕐 Обновлено: {format_datetime(datetime.now(), 'short')}"

    keyboard = Keyboards.get_admin_panel()
    await update.message.reply_text(stats_text, reply_markup=keyboard)


async def admin_callback_handler(update, context):
    """Обработчик callback-ов админ-панели"""
    query = update.callback_query
    user_id = query.from_user.id

    if not settings.is_admin(user_id):
        await query.answer("❌ Нет доступа")
        return

    await query.answer()
    callback_data = query.data

    if callback_data == "admin_refresh":
        await admin_refresh_stats(query, context)
    elif callback_data == "admin_export":
        await admin_export_data(query, context)
    elif callback_data == "admin_broadcast":
        await admin_broadcast_info(query, context)
    elif callback_data == "admin_cleanup":
        await admin_cleanup_data(query, context)
    elif callback_data == "admin_analytics":
        await admin_detailed_analytics(query, context)


async def admin_refresh_stats(query, context):
    """Обновление статистики"""
    db_manager.log_user_action(query.from_user.id, "admin_refresh", "Обновил статистику")

    # Получаем свежую статистику
    stats = db_manager.get_user_statistics()

    text = f"""
🔄 Статистика обновлена

👥 Актуальные данные:
• Всего пользователей: {stats['total_users']}
• Активных за неделю: {stats['active_week']}
• Завершили онбординг: {stats['completion_rate']}%
• Общий фидбек: {stats['total_feedback']} сообщений

📊 Конверсия по этапам:
"""

    # Конверсия между этапами
    status_stats = stats['status_stats']
    total = stats['total_users']

    if total > 0:
        preboarding_rate = (status_stats.get('preboarding', 0) +
                            status_stats.get('preboarded', 0) +
                            status_stats.get('onboarding', 0) +
                            status_stats.get('completed', 0)) / total * 100

        onboarding_rate = (status_stats.get('onboarding', 0) +
                           status_stats.get('completed', 0)) / total * 100

        completion_rate = stats['completion_rate']

        text += f"• Начали пребординг: {preboarding_rate:.1f}%\n"
        text += f"• Перешли к онбордингу: {onboarding_rate:.1f}%\n"
        text += f"• Завершили адаптацию: {completion_rate:.1f}%\n"

    text += f"\n🕐 Обновлено: {format_datetime(datetime.now(), 'short')}"

    keyboard = Keyboards.get_admin_panel()
    await query.edit_message_text(text, reply_markup=keyboard)


async def admin_export_data(query, context):
    """Экспорт данных"""
    db_manager.log_user_action(query.from_user.id, "admin_export", "Запросил экспорт данных")

    try:
        # Получаем все данные
        export_data = db_manager.export_to_dict()

        # Сохраняем в файл
        filename = f"onboarding_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = f"data/exports/{filename}"

        success = save_json(export_data, filepath)

        if success:
            stats = db_manager.get_user_statistics()

            text = f"""
📥 Экспорт данных завершен

📊 Экспортированные данные:
• Пользователи: {len(export_data['users'])}
• Обратная связь: {len(export_data['feedback'])}
• Действия пользователей: {len(export_data['actions'])}

📁 Файл: {filename}
📅 Дата экспорта: {export_data['exported_at']}

💾 Сводка по статусам:
"""

            status_counts = {}
            for user in export_data['users']:
                status = user['status']
                status_counts[status] = status_counts.get(status, 0) + 1

            for status, count in status_counts.items():
                text += f"• {status}: {count}\n"

            text += f"\n✅ Данные сохранены в папку exports/"

        else:
            text = "❌ Ошибка при экспорте данных. Проверьте логи."

        await query.edit_message_text(text)

    except Exception as e:
        logger.error(f"Ошибка экспорта данных: {e}")
        await query.edit_message_text(
            f"❌ Ошибка при экспорте данных:\n{str(e)}"
        )


async def admin_broadcast_info(query, context):
    """Информация о рассылке"""
    db_manager.log_user_action(query.from_user.id, "admin_broadcast_info", "Просмотрел информацию о рассылке")

    stats = db_manager.get_user_statistics()

    text = f"""
📢 Система рассылки сообщений

👥 Целевая аудитория:
• Всего пользователей: {stats['total_users']}
• Активных за неделю: {stats['active_week']}

📝 Как отправить рассылку:
Используйте команду:
`/broadcast [ваше сообщение]`

Пример:
`/broadcast Уважаемые коллеги! Завтра в офисе будет проходить team building. Начало в 18:00.`

⚙️ Настройки рассылки:
• Задержка между отправками: {settings.BROADCAST_DELAY} сек
• Максимальная длина сообщения: {settings.MAX_MESSAGE_LENGTH} символов
• Автоматические уведомления: {'✅' if settings.NOTIFICATION_ENABLED else '❌'}

⚠️ Важно:
• Рассылка отправляется всем зарегистрированным пользователям
• Заблокированные боты получат ошибку (это нормально)
• Результат рассылки будет показан после завершения

📊 Статистика последних рассылок:
Функция в разработке...
"""

    await query.edit_message_text(text)


async def admin_cleanup_data(query, context):
    """Очистка старых данных"""
    db_manager.log_user_action(query.from_user.id, "admin_cleanup", "Запросил очистку данных")

    try:
        # Очищаем данные старше 90 дней
        deleted_count = db_manager.cleanup_old_data(days=90)

        text = f"""
🗑️ Очистка данных завершена

📊 Результат:
• Удалено записей действий: {deleted_count}
• Период очистки: старше 90 дней
• Дата очистки: {format_datetime(datetime.now())}

💾 Что очищено:
• Логи действий пользователей (user_actions)
• Временные файлы
• Устаревшие сессии

🔒 Что сохранено:
• Данные пользователей (users)
• Обратная связь (feedback)
• Записи последних 90 дней

✅ База данных оптимизирована!
"""

        await query.edit_message_text(text)

    except Exception as e:
        logger.error(f"Ошибка очистки данных: {e}")
        await query.edit_message_text(f"❌ Ошибка при очистке данных:\n{str(e)}")


async def admin_detailed_analytics(query, context):
    """Подробная аналитика"""
    db_manager.log_user_action(query.from_user.id, "admin_analytics", "Просмотрел подробную аналитику")

    try:
        # Получаем данные за последние 30 дней
        daily_activity = db_manager.get_daily_activity(days=30)
        stats = db_manager.get_user_statistics()
        popular_actions = db_manager.get_popular_actions(days=30, limit=10)

        text = f"""
📈 Подробная аналитика (30 дней)

👥 Пользователи:
• Всего: {stats['total_users']}
• Новых за месяц: {len([d for d in daily_activity if d['unique_users'] > 0])} дней с активностью
• Средняя активность: {sum(d['unique_users'] for d in daily_activity) / len(daily_activity) if daily_activity else 0:.1f} польз/день

📊 Конверсия воронки:
"""

        # Анализ воронки
        status_stats = stats['status_stats']
        total = stats['total_users']

        if total > 0:
            funnel_stages = [
                ('Зарегистрировались', total, 100),
                ('Начали пребординг',
                 sum(status_stats.get(s, 0) for s in ['preboarding', 'preboarded', 'onboarding', 'completed']), 0),
                ('Завершили пребординг', sum(status_stats.get(s, 0) for s in ['preboarded', 'onboarding', 'completed']),
                 0),
                ('Начали онбординг', sum(status_stats.get(s, 0) for s in ['onboarding', 'completed']), 0),
                ('Завершили онбординг', status_stats.get('completed', 0), 0)
            ]

            for i, (stage, count, percentage) in enumerate(funnel_stages):
                if i > 0:
                    percentage = count / total * 100
                funnel_stages[i] = (stage, count, percentage)
                text += f"• {stage}: {count} ({percentage:.1f}%)\n"

        # Топ действий
        text += f"\n🔥 Популярные действия:\n"
        for action_data in popular_actions[:5]:
            text += f"• {action_data['action']}: {action_data['count']}\n"

        # Активность по дням (последние 7 дней)
        text += f"\n📅 Активность (последние 7 дней):\n"
        recent_activity = daily_activity[-7:] if len(daily_activity) >= 7 else daily_activity
        for day_data in recent_activity:
            date_str = datetime.fromisoformat(day_data['date']).strftime('%d.%m')
            text += f"• {date_str}: {day_data['unique_users']} польз, {day_data['total_actions']} действий\n"

        # Прогноз
        if len(daily_activity) >= 7:
            recent_avg = sum(d['unique_users'] for d in recent_activity) / len(recent_activity)
            total_avg = sum(d['unique_users'] for d in daily_activity) / len(daily_activity)
            trend = "📈 Растет" if recent_avg > total_avg else "📉 Снижается" if recent_avg < total_avg else "➡️ Стабильно"
            text += f"\n📊 Тренд активности: {trend}"

        await query.edit_message_text(text)

    except Exception as e:
        logger.error(f"Ошибка получения аналитики: {e}")
        await query.edit_message_text(f"❌ Ошибка при получении аналитики:\n{str(e)}")


async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда рассылки сообщений"""
    user_id = update.effective_user.id

    if not settings.is_admin(user_id):
        await update.message.reply_text("❌ У вас нет прав для рассылки.")
        return

    if not context.args:
        await update.message.reply_text(
            "❌ Укажите текст сообщения после команды /broadcast\n\n"
            "Пример:\n"
            "/broadcast Уважаемые коллеги! Завтра в офисе будет проходить team building."
        )
        return

    message_text = " ".join(context.args)

    if len(message_text) > settings.MAX_MESSAGE_LENGTH:
        await update.message.reply_text(
            f"❌ Сообщение слишком длинное ({len(message_text)} символов).\n"
            f"Максимум: {settings.MAX_MESSAGE_LENGTH} символов."
        )
        return

    db_manager.log_user_action(user_id, "broadcast_start", f"Начал рассылку: {message_text[:50]}...")

    # Получаем всех пользователей
    all_users = db_manager.get_all_users()

    sent_count = 0
    failed_count = 0

    broadcast_text = f"""
📢 Сообщение от администрации {settings.COMPANY_NAME}:

{message_text}

---
_Это автоматическое сообщение от OnboardingBuddy._
_Для отключения уведомлений обратитесь в HR._
"""

    # Отправляем статус начала рассылки
    status_message = await update.message.reply_text(
        f"📤 Начинаю рассылку сообщения {len(all_users)} пользователям...\n"
        f"📝 Текст: {message_text[:100]}{'...' if len(message_text) > 100 else ''}"
    )

    # Рассылка с задержкой
    for i, user in enumerate(all_users):
        try:
            await context.bot.send_message(chat_id=user.user_id, text=broadcast_text)
            sent_count += 1

            # Обновляем статус каждые 10 отправок
            if (i + 1) % 10 == 0:
                progress = (i + 1) / len(all_users) * 100
                await status_message.edit_text(
                    f"📤 Рассылка в процессе...\n"
                    f"📊 Прогресс: {i + 1}/{len(all_users)} ({progress:.0f}%)\n"
                    f"✅ Отправлено: {sent_count}\n"
                    f"❌ Ошибок: {failed_count}"
                )

            # Задержка между отправками
            await asyncio.sleep(settings.BROADCAST_DELAY)

        except Exception as e:
            failed_count += 1
            logger.error(f"Не удалось отправить сообщение пользователю {user.user_id}: {e}")

    # Финальный отчет
    result_text = f"""
📊 Результат рассылки:

✅ Успешно отправлено: {sent_count}
❌ Не удалось отправить: {failed_count}
📈 Процент доставки: {(sent_count / len(all_users) * 100):.1f}%

📝 Текст сообщения:
{message_text}

🕐 Время завершения: {format_datetime(datetime.now())}
"""

    await status_message.edit_text(result_text)

    db_manager.log_user_action(
        user_id,
        "broadcast_complete",
        f"Завершил рассылку: {sent_count} отправлено, {failed_count} ошибок"
    )


async def get_admin_users_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить список пользователей (скрытая admin команда)"""
    user_id = update.effective_user.id

    if not settings.is_admin(user_id):
        return

    users = db_manager.get_all_users()

    text = f"👥 Список пользователей ({len(users)}):\n\n"

    for user in users[-20:]:  # Последние 20 пользователей
        status_emoji = user.status_emoji
        text += f"{status_emoji} {user.full_name} (@{user.username or 'нет'}) - {user.status_name}\n"

    if len(users) > 20:
        text += f"\n... и еще {len(users) - 20} пользователей"

    await update.message.reply_text(text)