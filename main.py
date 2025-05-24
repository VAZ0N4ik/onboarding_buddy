#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OnboardingBuddy - Главный файл запуска бота

Модульная архитектура для автоматизации онбординга сотрудников
"""

import logging
import sys
import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram import Update

# Добавляем текущую директорию в путь для импортов
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import settings
from database.manager import db_manager
from utils.helpers import setup_logging

# Импорт обработчиков
from handlers.start import (
    start_command, help_command, status_command,
    contacts_command, handle_main_menu
)
from handlers.preboarding import handle_preboarding_callback
from handlers.admin import (
    admin_command, admin_callback_handler, broadcast_command
)
from handlers.callbacks import handle_all_callbacks
from handlers.info import handle_info_menu
from handlers.faq import handle_faq_menu
from handlers.feedback import handle_feedback_message

logger = logging.getLogger(__name__)


async def error_handler(update: object, context):
    """Глобальный обработчик ошибок"""
    logger.error(f"Exception while handling an update: {context.error}")

    # Попытаемся отправить сообщение пользователю об ошибке
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "😔 Произошла ошибка при обработке вашего запроса.\n"
                "Пожалуйста, попробуйте еще раз или обратитесь в поддержку.\n\n"
                f"Поддержка: {settings.SUPPORT_TELEGRAM}"
            )
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение об ошибке: {e}")


def setup_handlers(application: Application):
    """Настройка обработчиков бота"""

    # Команды
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("contacts", contacts_command))
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))

    # Callback query обработчики
    application.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^admin_.*"))
    application.add_handler(
        CallbackQueryHandler(handle_preboarding_callback, pattern="^(start_preboarding|docs_.*|all_docs_sent)$"))
    application.add_handler(CallbackQueryHandler(handle_all_callbacks))

    # Текстовые сообщения
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.Regex("^(🚀|📋|📚|❓|👥|📞|💬|📊|🏠).*"),
        handle_main_menu
    ))

    # Подменю
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.Regex("^(🏢|📜|🔧|📅).*"),
        handle_info_menu
    ))

    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.Regex("^(💰|🕐|🏖️|🎓).*"),
        handle_faq_menu
    ))

    # Обратная связь (должна быть последней среди текстовых)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_feedback_message
    ))

    # Обработчик ошибок
    application.add_error_handler(error_handler)

    logger.info("Обработчики настроены")


def validate_configuration():
    """Проверка конфигурации перед запуском"""
    issues = settings.validate()

    if issues:
        logger.warning("Обнаружены проблемы конфигурации:")
        for issue in issues:
            logger.warning(f"  {issue}")

        if settings.BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
            logger.error("❌ КРИТИЧЕСКАЯ ОШИБКА: Не указан токен бота!")
            logger.error("Получите токен у @BotFather и укажите в переменной BOT_TOKEN")
            return False

    logger.info("Конфигурация проверена")
    return True


def main():
    """Главная функция запуска бота"""

    # Настройка логирования
    setup_logging()

    logger.info("🚀 Запуск OnboardingBuddy...")

    # Проверка конфигурации
    if not validate_configuration():
        sys.exit(1)

    # Вывод информации о конфигурации
    logger.info(settings.get_config_summary())

    # Инициализация базы данных
    try:
        db_manager.init_database()
        logger.info("✅ База данных готова")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БД: {e}")
        sys.exit(1)

    # Создание приложения
    application = Application.builder().token(settings.BOT_TOKEN).build()

    # Настройка обработчиков
    setup_handlers(application)

    # Статистика при запуске
    stats = db_manager.get_user_statistics()
    logger.info(f"📊 Статистика: {stats['total_users']} пользователей, "
                f"{stats['active_week']} активных за неделю")

    logger.info("🤖 OnboardingBuddy запущен и готов к работе!")
    logger.info(f"👥 Администраторы: {settings.ADMIN_IDS}")

    # Запуск бота
    try:
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
            poll_interval=2.0,
            timeout=20
        )
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        sys.exit(1)
    finally:
        logger.info("👋 OnboardingBuddy завершил работу")


if __name__ == '__main__':
    # Поддержка аргументов командной строки
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'setup':
            from utils.setup import setup_wizard

            setup_wizard()
        elif command == 'validate':
            validate_configuration()
            print("✅ Конфигурация проверена")
        elif command == 'stats':
            stats = db_manager.get_user_statistics()
            print("📊 Статистика бота:")
            print(f"  Всего пользователей: {stats['total_users']}")
            print(f"  Активных за неделю: {stats['active_week']}")
            print(f"  Завершили онбординг: {stats['completion_rate']}%")
        elif command == 'export':
            from utils.export import export_data

            export_data()
        elif command == 'cleanup':
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 90
            deleted = db_manager.cleanup_old_data(days)
            print(f"🗑️ Удалено {deleted} старых записей")
        elif command == 'validate':
            from utils.validators import get_validation_summary

            summary = get_validation_summary()
            print("🔍 Результат валидации:")
            if summary['overall_status'] == 'good':
                print("✅ Все проверки пройдены")
            else:
                print(f"⚠️ Статус: {summary['overall_status']}")
                for issue in summary['config_issues'][:5]:  # Показываем первые 5
                    print(f"  {issue}")
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 90
            deleted = db_manager.cleanup_old_data(days)
            print(f"🗑️ Удалено {deleted} старых записей")
        else:
            print("❓ Неизвестная команда")
            print("Доступные команды: setup, validate, stats, export, analytics, cleanup")
    else:
        main()