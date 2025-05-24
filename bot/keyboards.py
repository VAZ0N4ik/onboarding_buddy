# bot/keyboards.py
"""
Клавиатуры и меню для OnboardingBuddy
"""
from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from typing import List


class Keyboards:
    """Класс для управления клавиатурами бота"""

    # Основные меню
    MAIN_MENU = [
        ["🚀 Пребординг", "📋 Онбординг"],
        ["📚 Полезная информация", "❓ FAQ"],
        ["👥 Контакты сотрудников", "📞 Поддержка"],
        ["💬 Обратная связь", "📊 Мой прогресс"]
    ]

    INFO_MENU = [
        ["🏢 О компании", "📜 Корпоративная культура"],
        ["🔧 Инструменты и ресурсы", "📅 Календарь мероприятий"],
        ["🏠 Главное меню"]
    ]

    FAQ_MENU = [
        ["💰 Зарплата и льготы", "🕐 Рабочее время"],
        ["🏖️ Отпуска и больничные", "🎓 Обучение"],
        ["🏠 Главное меню"]
    ]

    @staticmethod
    def get_main_menu() -> ReplyKeyboardMarkup:
        """Получить главное меню"""
        return ReplyKeyboardMarkup(
            Keyboards.MAIN_MENU,
            resize_keyboard=True,
            one_time_keyboard=False
        )

    @staticmethod
    def get_info_menu() -> ReplyKeyboardMarkup:
        """Получить меню полезной информации"""
        return ReplyKeyboardMarkup(
            Keyboards.INFO_MENU,
            resize_keyboard=True,
            one_time_keyboard=False
        )

    @staticmethod
    def get_faq_menu() -> ReplyKeyboardMarkup:
        """Получить FAQ меню"""
        return ReplyKeyboardMarkup(
            Keyboards.FAQ_MENU,
            resize_keyboard=True,
            one_time_keyboard=False
        )

    @staticmethod
    def get_preboarding_start() -> InlineKeyboardMarkup:
        """Кнопка начала пребординга"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Готов начать!", callback_data="start_preboarding")]
        ])

    @staticmethod
    def get_document_categories() -> InlineKeyboardMarkup:
        """Категории документов"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("📄 Основные документы (1-5)", callback_data="docs_main")],
            [InlineKeyboardButton("📑 Документы по ТК РФ (6-9)", callback_data="docs_tk")]
        ])

    @staticmethod
    def get_docs_main_menu() -> InlineKeyboardMarkup:
        """Меню основных документов"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Документы отправлены", callback_data="docs_main_sent")],
            [InlineKeyboardButton("📑 Документы по ТК РФ", callback_data="docs_tk")],
            [InlineKeyboardButton("◀️ Назад", callback_data="start_preboarding")]
        ])

    @staticmethod
    def get_docs_tk_menu() -> InlineKeyboardMarkup:
        """Меню документов по ТК РФ"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Документы отправлены", callback_data="docs_tk_sent")],
            [InlineKeyboardButton("📄 Основные документы", callback_data="docs_main")],
            [InlineKeyboardButton("◀️ Назад", callback_data="start_preboarding")]
        ])

    @staticmethod
    def get_docs_completion_menu() -> InlineKeyboardMarkup:
        """Меню завершения отправки документов"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("📄 Основные документы", callback_data="docs_main")],
            [InlineKeyboardButton("📑 Документы по ТК РФ", callback_data="docs_tk")],
            [InlineKeyboardButton("✅ Все документы отправлены", callback_data="all_docs_sent")]
        ])

    @staticmethod
    def get_start_onboarding() -> InlineKeyboardMarkup:
        """Кнопка начала онбординга"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 Начать онбординг", callback_data="start_onboarding")]
        ])

    @staticmethod
    def get_documents_received() -> InlineKeyboardMarkup:
        """Кнопка получения документов"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("📄 Получил подписанные документы", callback_data="start_onboarding")]
        ])

    @staticmethod
    def get_email_access() -> InlineKeyboardMarkup:
        """Проверка доступа к почте"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Получил доступ", callback_data="email_received")],
            [InlineKeyboardButton("❌ Не получил доступ", callback_data="email_not_received")]
        ])

    @staticmethod
    def get_email_retry() -> InlineKeyboardMarkup:
        """Повторная проверка доступа к почте"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Получил доступ", callback_data="email_received")],
            [InlineKeyboardButton("🔄 Проверить еще раз", callback_data="start_onboarding")]
        ])

    @staticmethod
    def get_onboarding_next() -> InlineKeyboardMarkup:
        """Следующие шаги онбординга"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("👥 Знакомство с командой", callback_data="team_intro")],
            [InlineKeyboardButton("📅 Планерки отделов", callback_data="meetings")]
        ])

    @staticmethod
    def get_team_intro_next() -> InlineKeyboardMarkup:
        """После знакомства с командой"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("📅 Планерки отделов", callback_data="meetings")],
            [InlineKeyboardButton("✅ Завершить онбординг", callback_data="complete_onboarding")]
        ])

    @staticmethod
    def get_meetings_next() -> InlineKeyboardMarkup:
        """После ознакомления с планерками"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("👥 Знакомство с командой", callback_data="team_intro")],
            [InlineKeyboardButton("✅ Завершить онбординг", callback_data="complete_onboarding")]
        ])

    @staticmethod
    def get_admin_panel() -> InlineKeyboardMarkup:
        """Административная панель"""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📊 Экспорт данных", callback_data="admin_export"),
                InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast")
            ],
            [
                InlineKeyboardButton("🔄 Обновить статистику", callback_data="admin_refresh"),
                InlineKeyboardButton("🗑️ Очистка данных", callback_data="admin_cleanup")
            ],
            [
                InlineKeyboardButton("📈 Подробная аналитика", callback_data="admin_analytics")
            ]
        ])

    @staticmethod
    def get_user_status_filter() -> InlineKeyboardMarkup:
        """Фильтр пользователей по статусу"""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🆕 Новые", callback_data="filter_new"),
                InlineKeyboardButton("🔄 Пребординг", callback_data="filter_preboarding")
            ],
            [
                InlineKeyboardButton("✅ Готовы к онбордингу", callback_data="filter_preboarded"),
                InlineKeyboardButton("🚀 Онбординг", callback_data="filter_onboarding")
            ],
            [
                InlineKeyboardButton("🎉 Завершили", callback_data="filter_completed"),
                InlineKeyboardButton("📊 Все", callback_data="filter_all")
            ]
        ])

    @staticmethod
    def get_confirmation(action: str, confirm_data: str, cancel_data: str = "cancel") -> InlineKeyboardMarkup:
        """Клавиатура подтверждения действия"""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton(f"✅ Подтвердить {action}", callback_data=confirm_data),
                InlineKeyboardButton("❌ Отмена", callback_data=cancel_data)
            ]
        ])

    @staticmethod
    def get_pagination(page: int, total_pages: int, prefix: str) -> InlineKeyboardMarkup:
        """Пагинация для списков"""
        buttons = []

        # Кнопки навигации
        nav_buttons = []
        if page > 1:
            nav_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"{prefix}_page_{page - 1}"))

        nav_buttons.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="noop"))

        if page < total_pages:
            nav_buttons.append(InlineKeyboardButton("➡️", callback_data=f"{prefix}_page_{page + 1}"))

        if nav_buttons:
            buttons.append(nav_buttons)

        # Кнопка возврата
        buttons.append([InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_main")])

        return InlineKeyboardMarkup(buttons)

    @staticmethod
    def get_progress_visualization(stage: int, max_stage: int = 10) -> str:
        """Визуализация прогресса"""
        progress = min(stage / max_stage, 1.0)
        filled = int(progress * 10)
        empty = 10 - filled

        return f"{'█' * filled}{'░' * empty} {progress * 100:.0f}%"

    @staticmethod
    def create_url_keyboard(buttons: List[tuple]) -> InlineKeyboardMarkup:
        """Создать клавиатуру с URL кнопками

        Args:
            buttons: Список кортежей (text, url)
        """
        keyboard = []
        for text, url in buttons:
            keyboard.append([InlineKeyboardButton(text, url=url)])

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def create_callback_keyboard(buttons: List[tuple], columns: int = 2) -> InlineKeyboardMarkup:
        """Создать клавиатуру с callback кнопками

        Args:
            buttons: Список кортежей (text, callback_data)
            columns: Количество кнопок в ряду
        """
        keyboard = []
        row = []

        for i, (text, callback_data) in enumerate(buttons):
            row.append(InlineKeyboardButton(text, callback_data=callback_data))

            if len(row) == columns or i == len(buttons) - 1:
                keyboard.append(row)
                row = []

        return InlineKeyboardMarkup(keyboard)