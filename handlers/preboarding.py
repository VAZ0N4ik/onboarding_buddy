# handlers/preboarding.py
"""
Обработчики пребординга
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from config.settings import settings
from database.manager import db_manager
from database.models import UserStatus, OnboardingStage
from bot.keyboards import Keyboards

logger = logging.getLogger(__name__)


async def handle_preboarding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главный обработчик пребординга"""
    user_id = update.effective_user.id
    user = db_manager.get_user(user_id)

    if not user:
        await update.message.reply_text(
            "⚠️ Пользователь не найден. Используйте /start для регистрации."
        )
        return

    # Обновляем статус на пребординг если пользователь новый
    if user.status == UserStatus.NEW:
        db_manager.update_user_stage(user_id, OnboardingStage.REGISTRATION, UserStatus.PREBOARDING)

    db_manager.log_user_action(user_id, "preboarding_start", "Начал пребординг")

    # Проверяем текущий статус
    if user.status == UserStatus.COMPLETED:
        text = """
🎉 Вы уже завершили весь процесс адаптации!

Если нужно что-то уточнить, обращайтесь к разделам:
• ❓ FAQ - ответы на вопросы
• 👥 Контакты сотрудников
• 📞 Поддержка
"""
        await update.message.reply_text(text)
        return

    elif user.status in [UserStatus.PREBOARDED, UserStatus.ONBOARDING]:
        text = """
✅ Пребординг уже завершен!

Вы можете перейти к разделу "📋 Онбординг" для продолжения адаптации.
"""
        await update.message.reply_text(text)
        return

    # Основной текст пребординга
    text = f"""
🎊 Привет, {update.effective_user.first_name}! 

Мы рады, что вы приняли решение присоединиться к нашей команде {settings.COMPANY_NAME}!

🏢 **О нашей команде:**
Мы состоим из талантливых профессионалов, которые создают инновационные IT-решения. Каждый сотрудник важен для нас, и мы стремимся создать максимально комфортную рабочую атмосферу.

📋 **Что включает пребординг:**
• Подготовка и отправка необходимых документов
• Ознакомление с процедурами оформления
• Подготовка к следующему этапу - онбордингу

⏱️ **Примерное время:** 15-30 минут

Готовы начать оформление?
"""

    keyboard = Keyboards.get_preboarding_start()
    await update.message.reply_text(text, reply_markup=keyboard)


async def handle_preboarding_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback-ов пребординга"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    callback_data = query.data

    if callback_data == "start_preboarding":
        await start_preboarding_process(query, context)
    elif callback_data == "docs_main":
        await show_main_documents(query, context)
    elif callback_data == "docs_tk":
        await show_tk_documents(query, context)
    elif callback_data == "docs_main_sent":
        await handle_docs_main_sent(query, context)
    elif callback_data == "docs_tk_sent":
        await handle_docs_tk_sent(query, context)
    elif callback_data == "all_docs_sent":
        await handle_all_docs_sent(query, context)


async def start_preboarding_process(query, context):
    """Начать процесс пребординга"""
    user_id = query.from_user.id

    db_manager.update_user_stage(user_id, OnboardingStage.DOCUMENTS_INTRO)
    db_manager.log_user_action(user_id, "preboarding_docs", "Начал процесс подготовки документов")

    text = f"""
📋 **Документы для оформления на работу**

Для успешного оформления в {settings.COMPANY_NAME} нам потребуются следующие документы.

📧 **Email для отправки:** {settings.HR_EMAIL}

⚡ **Важно:**
• Отправляйте сканы или качественные фотографии
• Все документы должны быть четко читаемыми
• При возникновении вопросов обращайтесь: {settings.HR_TELEGRAM}

📑 **Документы разделены на две категории:**
• Основные (обязательные для всех)
• По Трудовому кодексу РФ (при наличии)

Выберите категорию для ознакомления:
"""

    keyboard = Keyboards.get_document_categories()
    await query.edit_message_text(text, reply_markup=keyboard)


async def show_main_documents(query, context):
    """Показать основные документы"""
    user_id = query.from_user.id
    db_manager.log_user_action(user_id, "docs_main_view", "Просмотрел список основных документов")

    text = f"""
📄 **Основные документы (обязательные)**

Отправьте на email: {settings.HR_EMAIL}

**Список документов:**

1️⃣ **Паспорт** 
   • Главная страница (фото + ФИО)
   • Страница с пропиской

2️⃣ **ИНН** (справка или свидетельство)

3️⃣ **СНИЛС** (зеленая карточка или справка)

4️⃣ **Адрес фактического проживания**
   • Если отличается от прописки в паспорте
   • Можно указать текстом в письме

5️⃣ **Банковские реквизиты**
   • Номер карты или расчетного счета
   • Желательно Сбербанк (для быстрых переводов)

⚠️ **Обратите внимание:**
• Все документы должны быть действующими
• Фото должны быть четкими и читаемыми
• В теме письма укажите: "Документы - [Ваше ФИО]"
"""

    keyboard = Keyboards.get_docs_main_menu()
    await query.edit_message_text(text, reply_markup=keyboard)


async def show_tk_documents(query, context):
    """Показать документы по ТК РФ"""
    user_id = query.from_user.id
    db_manager.log_user_action(user_id, "docs_tk_view", "Просмотрел список документов по ТК РФ")

    text = f"""
📑 **Документы по Трудовому кодексу РФ**

Отправьте на email: {settings.HR_EMAIL}

**Список документов (при наличии):**

6️⃣ **Трудовая книжка** 
   • Если есть физическая книжка
   • Или справка с предыдущего места работы
   • Для оформления трудового договора

7️⃣ **Диплом об образовании**
   • Если имеется высшее/среднее профессиональное образование
   • Для записи в трудовую книжку

8️⃣ **Свидетельство о браке**
   • Если состоите в браке
   • Для оформления льгот и отпусков

9️⃣ **Свидетельства о рождении детей**
   • Если есть несовершеннолетние дети
   • Для оформления детских пособий и льгот

🔟 **Фото для корпоративного сайта**
   • Деловое фото (предпочтительно)
   • Для размещения в команде на сайте

💡 **Примечание:** Документы 6-9 предоставляются только при их наличии.
"""

    keyboard = Keyboards.get_docs_tk_menu()
    await query.edit_message_text(text, reply_markup=keyboard)


async def handle_docs_main_sent(query, context):
    """Обработка отправки основных документов"""
    user_id = query.from_user.id
    user = db_manager.get_user(user_id)

    # Обновляем этап только если текущий этап меньше
    new_stage = max(user.stage, OnboardingStage.DOCUMENTS_MAIN)
    db_manager.update_user_stage(user_id, new_stage)
    db_manager.log_user_action(user_id, "docs_main_sent", "Подтвердил отправку основных документов")

    text = """
✅ **Основные документы отмечены как отправленные**

🎯 **Что дальше:**
• Если у вас есть документы по ТК РФ - отправьте их тоже
• Если все документы готовы - переходите к завершению

📧 **Не забудьте:**
Проверьте, что письмо с документами отправлено на {settings.HR_EMAIL}
"""

    keyboard = Keyboards.get_docs_completion_menu()
    await query.edit_message_text(text, reply_markup=keyboard)


async def handle_docs_tk_sent(query, context):
    """Обработка отправки документов по ТК РФ"""
    user_id = query.from_user.id
    user = db_manager.get_user(user_id)

    # Обновляем этап только если текущий этап меньше
    new_stage = max(user.stage, OnboardingStage.DOCUMENTS_TK)
    db_manager.update_user_stage(user_id, new_stage)
    db_manager.log_user_action(user_id, "docs_tk_sent", "Подтвердил отправку документов по ТК РФ")

    text = """
✅ **Документы по ТК РФ отмечены как отправленные**

🎯 **Что дальше:**
• Если основные документы тоже готовы - завершайте пребординг
• Если не отправляли основные документы - обязательно отправьте их

📧 **Напоминание:**
Убедитесь, что все документы отправлены на {settings.HR_EMAIL}
"""

    keyboard = Keyboards.get_docs_completion_menu()
    await query.edit_message_text(text, reply_markup=keyboard)


async def handle_all_docs_sent(query, context):
    """Завершение отправки всех документов"""
    user_id = query.from_user.id

    db_manager.update_user_stage(user_id, OnboardingStage.DOCUMENTS_COMPLETE, UserStatus.PREBOARDED)
    db_manager.log_user_action(user_id, "preboarding_complete", "Завершил пребординг")

    text = f"""
🎉 **Отлично! Пребординг завершен!**

✅ **Что сделано:**
• Все необходимые документы отправлены
• Ваша заявка поступила в HR-отдел

⏳ **Что происходит дальше:**
1. HR-менеджер проверит ваши документы (1-2 рабочих дня)
2. Будут подготовлены документы для подписания (ТД, NDA и др.)
3. Вы получите их на email для ознакомления и подписания

📧 **Контакт HR-менеджера:**
{settings.HR_TELEGRAM} - для срочных вопросов

📚 **В ожидании можете:**
• Изучить раздел "📚 Полезная информация"
• Ознакомиться с "❓ FAQ"
• Посмотреть контакты будущих коллег

🎯 **Следующий шаг:** 
После получения подписанных документов от HR-менеджера вы сможете перейти к этапу **онбординга**.

Нажмите кнопку ниже, когда получите подписанные документы:
"""

    keyboard = Keyboards.get_documents_received()
    await query.edit_message_text(text, reply_markup=keyboard)


async def get_preboarding_status(user_id: int) -> str:
    """Получить статус пребординга для пользователя"""
    user = db_manager.get_user(user_id)

    if not user:
        return "Пользователь не найден"

    if user.status == UserStatus.NEW:
        return "Не начат"
    elif user.status == UserStatus.PREBOARDING:
        stage_status = {
            OnboardingStage.REGISTRATION: "Регистрация",
            OnboardingStage.DOCUMENTS_INTRO: "Изучение требований",
            OnboardingStage.DOCUMENTS_MAIN: "Отправка основных документов",
            OnboardingStage.DOCUMENTS_TK: "Отправка документов по ТК РФ",
        }
        return stage_status.get(user.stage, f"Этап {user.stage}")
    elif user.status == UserStatus.PREBOARDED:
        return "Завершен ✅"
    else:
        return "Пройден"