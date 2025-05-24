# utils/export.py
"""
Утилиты для экспорта данных OnboardingBuddy
"""
import csv
import json
import os
from datetime import datetime
from typing import Dict, List, Any

from database.manager import db_manager
from utils.helpers import save_json, create_data_directory_structure


def export_data():
    """Основная функция экспорта данных"""
    print("📤 Начинаем экспорт данных OnboardingBuddy...")

    # Создаем директории если нужно
    create_data_directory_structure()

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    try:
        # Экспорт в JSON
        json_success = export_to_json(timestamp)

        # Экспорт в CSV
        csv_success = export_to_csv(timestamp)

        # Создаем сводный отчет
        create_export_report(timestamp, json_success, csv_success)

        print("✅ Экспорт данных завершен успешно!")
        print(f"📁 Файлы сохранены в папке: data/exports/")

    except Exception as e:
        print(f"❌ Ошибка при экспорте данных: {e}")


def export_to_json(timestamp: str) -> bool:
    """Экспорт всех данных в JSON"""
    print("📄 Экспорт в JSON формат...")

    try:
        # Получаем все данные
        export_data = db_manager.export_to_dict()

        # Добавляем метаданные
        export_data['export_info'] = {
            'timestamp': timestamp,
            'format': 'json',
            'version': '1.0',
            'total_users': len(export_data['users']),
            'total_feedback': len(export_data['feedback']),
            'total_actions': len(export_data['actions'])
        }

        # Сохраняем
        filename = f"data/exports/onboarding_full_export_{timestamp}.json"
        success = save_json(export_data, filename)

        if success:
            print(f"✅ JSON экспорт сохранен: {filename}")
        else:
            print("❌ Ошибка сохранения JSON")

        return success

    except Exception as e:
        print(f"❌ Ошибка JSON экспорта: {e}")
        return False


def export_to_csv(timestamp: str) -> bool:
    """Экспорт данных в CSV файлы"""
    print("📊 Экспорт в CSV формат...")

    try:
        # Экспорт пользователей
        users_success = export_users_csv(timestamp)

        # Экспорт обратной связи
        feedback_success = export_feedback_csv(timestamp)

        # Экспорт действий пользователей
        actions_success = export_actions_csv(timestamp)

        # Экспорт статистики
        stats_success = export_statistics_csv(timestamp)

        all_success = all([users_success, feedback_success, actions_success, stats_success])

        if all_success:
            print("✅ Все CSV файлы созданы успешно")
        else:
            print("⚠️ Некоторые CSV файлы не удалось создать")

        return all_success

    except Exception as e:
        print(f"❌ Ошибка CSV экспорта: {e}")
        return False


def export_users_csv(timestamp: str) -> bool:
    """Экспорт пользователей в CSV"""
    try:
        users = db_manager.get_all_users()
        filename = f"data/exports/users_{timestamp}.csv"

        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            # Заголовки
            writer.writerow([
                'user_id', 'username', 'full_name', 'position',
                'status', 'stage', 'progress_percentage',
                'created_at', 'updated_at'
            ])

            # Данные
            for user in users:
                writer.writerow([
                    user.user_id,
                    user.username or '',
                    user.full_name or '',
                    user.position or '',
                    user.status.value,
                    user.stage,
                    f"{user.progress_percentage:.1f}%",
                    user.created_at.isoformat() if user.created_at else '',
                    user.updated_at.isoformat() if user.updated_at else ''
                ])

        print(f"✅ Пользователи: {filename} ({len(users)} записей)")
        return True

    except Exception as e:
        print(f"❌ Ошибка экспорта пользователей: {e}")
        return False


def export_feedback_csv(timestamp: str) -> bool:
    """Экспорт обратной связи в CSV"""
    try:
        feedback_list = db_manager.get_recent_feedback(limit=1000)  # Все фидбеки
        filename = f"data/exports/feedback_{timestamp}.csv"

        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            # Заголовки
            writer.writerow([
                'id', 'user_id', 'user_name', 'username',
                'message', 'created_at'
            ])

            # Данные
            for feedback in feedback_list:
                writer.writerow([
                    feedback['id'],
                    feedback['user_id'],
                    feedback['user_name'],
                    feedback['username'] or '',
                    feedback['message'],
                    feedback['created_at']
                ])

        print(f"✅ Обратная связь: {filename} ({len(feedback_list)} записей)")
        return True

    except Exception as e:
        print(f"❌ Ошибка экспорта обратной связи: {e}")
        return False


def export_actions_csv(timestamp: str) -> bool:
    """Экспорт действий пользователей в CSV"""
    try:
        # Получаем действия за последние 30 дней
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=30)

        # Это упрощенная версия, в реальности нужен метод для получения действий по дате
        filename = f"data/exports/user_actions_{timestamp}.csv"

        # Получаем популярные действия как пример
        popular_actions = db_manager.get_popular_actions(days=30, limit=100)

        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            # Заголовки
            writer.writerow(['action', 'count', 'period'])

            # Данные
            for action in popular_actions:
                writer.writerow([
                    action['action'],
                    action['count'],
                    '30 days'
                ])

        print(f"✅ Действия пользователей: {filename} ({len(popular_actions)} записей)")
        return True

    except Exception as e:
        print(f"❌ Ошибка экспорта действий: {e}")
        return False


def export_statistics_csv(timestamp: str) -> bool:
    """Экспорт статистики в CSV"""
    try:
        stats = db_manager.get_user_statistics()
        daily_activity = db_manager.get_daily_activity(days=30)

        # Общая статистика
        stats_filename = f"data/exports/statistics_{timestamp}.csv"
        with open(stats_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            writer.writerow(['metric', 'value'])
            writer.writerow(['total_users', stats['total_users']])
            writer.writerow(['active_week', stats['active_week']])
            writer.writerow(['completion_rate', f"{stats['completion_rate']}%"])
            writer.writerow(['avg_progress', stats['avg_progress']])
            writer.writerow(['total_feedback', stats['total_feedback']])

            # Статистика по статусам
            for status, count in stats['status_stats'].items():
                writer.writerow([f'status_{status}', count])

        # Дневная активность
        activity_filename = f"data/exports/daily_activity_{timestamp}.csv"
        with open(activity_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            writer.writerow(['date', 'unique_users', 'total_actions'])
            for day in daily_activity:
                writer.writerow([
                    day['date'],
                    day['unique_users'],
                    day['total_actions']
                ])

        print(f"✅ Статистика: {stats_filename}")
        print(f"✅ Дневная активность: {activity_filename}")
        return True

    except Exception as e:
        print(f"❌ Ошибка экспорта статистики: {e}")
        return False


def create_export_report(timestamp: str, json_success: bool, csv_success: bool):
    """Создание отчета об экспорте"""
    try:
        report_filename = f"data/exports/export_report_{timestamp}.txt"

        stats = db_manager.get_user_statistics()

        report_content = f"""
OnboardingBuddy - Отчет об экспорте данных
==========================================

Дата и время экспорта: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Timestamp: {timestamp}

СТАТИСТИКА ЭКСПОРТИРОВАННЫХ ДАННЫХ:
----------------------------------
Всего пользователей: {stats['total_users']}
Активных за неделю: {stats['active_week']}
Процент завершения онбординга: {stats['completion_rate']}%
Средний прогресс: {stats['avg_progress']:.1f}/10
Всего обратной связи: {stats['total_feedback']}

РАСПРЕДЕЛЕНИЕ ПО СТАТУСАМ:
-------------------------
"""

        status_names = {
            'new': 'Новые пользователи',
            'preboarding': 'Пребординг в процессе',
            'preboarded': 'Готовы к онбордингу',
            'onboarding': 'Проходят онбординг',
            'completed': 'Завершили онбординг'
        }

        for status, count in stats['status_stats'].items():
            name = status_names.get(status, status)
            percentage = (count / stats['total_users'] * 100) if stats['total_users'] > 0 else 0
            report_content += f"{name}: {count} ({percentage:.1f}%)\n"

        report_content += f"""
РЕЗУЛЬТАТ ЭКСПОРТА:
------------------
JSON экспорт: {'✅ Успешно' if json_success else '❌ Ошибка'}
CSV экспорт: {'✅ Успешно' if csv_success else '❌ Ошибка'}

СОЗДАННЫЕ ФАЙЛЫ:
---------------
"""

        if json_success:
            report_content += f"- onboarding_full_export_{timestamp}.json\n"

        if csv_success:
            report_content += f"- users_{timestamp}.csv\n"
            report_content += f"- feedback_{timestamp}.csv\n"
            report_content += f"- user_actions_{timestamp}.csv\n"
            report_content += f"- statistics_{timestamp}.csv\n"
            report_content += f"- daily_activity_{timestamp}.csv\n"

        report_content += f"""
ОПИСАНИЕ ФАЙЛОВ:
---------------
JSON файл: Полный экспорт всех данных в JSON формате
CSV файлы: Отдельные таблицы для анализа в Excel/Google Sheets
- users.csv: Информация о всех пользователях
- feedback.csv: Вся обратная связь от пользователей
- user_actions.csv: Популярные действия пользователей
- statistics.csv: Общая статистика системы
- daily_activity.csv: Ежедневная активность пользователей

РЕКОМЕНДАЦИИ:
------------
1. Регулярно создавайте резервные копии данных
2. Анализируйте статистику для улучшения процессов
3. Обратите внимание на пользователей, застрявших на этапах
4. Используйте обратную связь для развития системы

Экспорт завершен: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report_content)

        print(f"✅ Отчет об экспорте: {report_filename}")

    except Exception as e:
        print(f"❌ Ошибка создания отчета: {e}")


def export_user_data(user_id: int) -> Dict[str, Any]:
    """Экспорт данных конкретного пользователя"""
    try:
        user = db_manager.get_user(user_id)
        if not user:
            return {}

        actions = db_manager.get_user_actions(user_id, limit=100)

        user_data = {
            'user_info': user.to_dict(),
            'actions': [action.to_dict() for action in actions],
            'export_timestamp': datetime.now().isoformat()
        }

        return user_data

    except Exception as e:
        print(f"❌ Ошибка экспорта данных пользователя {user_id}: {e}")
        return {}


def export_analytics_report() -> bool:
    """Создание аналитического отчета"""
    try:
        print("📈 Создание аналитического отчета...")

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"data/exports/analytics_report_{timestamp}.json"

        stats = db_manager.get_user_statistics()
        daily_activity = db_manager.get_daily_activity(days=30)
        popular_actions = db_manager.get_popular_actions(days=30, limit=20)

        # Анализ конверсии
        total_users = stats['total_users']
        status_stats = stats['status_stats']

        conversion_funnel = {}
        if total_users > 0:
            conversion_funnel = {
                'registration_to_preboarding': (
                        sum(status_stats.get(s, 0) for s in ['preboarding', 'preboarded', 'onboarding', 'completed'])
                        / total_users * 100
                ),
                'preboarding_to_onboarding': (
                        sum(status_stats.get(s, 0) for s in ['onboarding', 'completed'])
                        / total_users * 100
                ),
                'onboarding_to_completion': (
                        status_stats.get('completed', 0) / total_users * 100
                )
            }

        # Активность по дням недели
        weekday_activity = {}
        for day_data in daily_activity:
            try:
                date_obj = datetime.fromisoformat(day_data['date'])
                weekday = date_obj.strftime('%A')
                if weekday not in weekday_activity:
                    weekday_activity[weekday] = {'users': 0, 'actions': 0, 'days': 0}
                weekday_activity[weekday]['users'] += day_data['unique_users']
                weekday_activity[weekday]['actions'] += day_data['total_actions']
                weekday_activity[weekday]['days'] += 1
            except:
                continue

        # Средние значения по дням недели
        for day in weekday_activity:
            if weekday_activity[day]['days'] > 0:
                weekday_activity[day]['avg_users'] = round(
                    weekday_activity[day]['users'] / weekday_activity[day]['days'], 1
                )
                weekday_activity[day]['avg_actions'] = round(
                    weekday_activity[day]['actions'] / weekday_activity[day]['days'], 1
                )

        analytics_data = {
            'report_info': {
                'timestamp': timestamp,
                'period_days': 30,
                'generated_at': datetime.now().isoformat()
            },
            'summary': stats,
            'conversion_funnel': conversion_funnel,
            'daily_activity': daily_activity,
            'weekday_activity': weekday_activity,
            'popular_actions': popular_actions
        }

        success = save_json(analytics_data, filename)

        if success:
            print(f"✅ Аналитический отчет: {filename}")

        return success

    except Exception as e:
        print(f"❌ Ошибка создания аналитического отчета: {e}")
        return False


if __name__ == '__main__':
    export_data()