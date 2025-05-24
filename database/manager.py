# database/manager.py
"""
Менеджер базы данных для OnboardingBuddy
"""
import sqlite3
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from contextlib import contextmanager

from config.settings import settings
from database.models import User, Feedback, UserAction, UserStatus, DatabaseSchema

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Менеджер для работы с базой данных"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.DATABASE_PATH
        self.init_database()

    @contextmanager
    def get_connection(self):
        """Контекстный менеджер для работы с соединением"""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def init_database(self):
        """Инициализация базы данных"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Создаем таблицы
            cursor.execute(DatabaseSchema.CREATE_USERS_TABLE)
            cursor.execute(DatabaseSchema.CREATE_FEEDBACK_TABLE)
            cursor.execute(DatabaseSchema.CREATE_USER_ACTIONS_TABLE)

            # Создаем индексы
            for index_sql in DatabaseSchema.CREATE_INDEXES:
                cursor.execute(index_sql)

            conn.commit()
            logger.info("База данных инициализирована")

    # МЕТОДЫ ДЛЯ РАБОТЫ С ПОЛЬЗОВАТЕЛЯМИ

    def get_user(self, user_id: int) -> Optional[User]:
        """Получить пользователя по ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            return User.from_db_row(row) if row else None

    def create_user(self, user_id: int, username: str = None, full_name: str = None) -> User:
        """Создать нового пользователя"""
        user = User(
            user_id=user_id,
            username=username,
            full_name=full_name,
            status=UserStatus.NEW,
            stage=0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO users 
                (user_id, username, full_name, position, status, stage, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user.user_id, user.username, user.full_name, user.position,
                user.status.value, user.stage, user.created_at, user.updated_at
            ))
            conn.commit()

        logger.info(f"Пользователь {user_id} создан")
        return user

    def update_user(self, user: User) -> bool:
        """Обновить данные пользователя"""
        user.updated_at = datetime.now()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET 
                username = ?, full_name = ?, position = ?, 
                status = ?, stage = ?, updated_at = ?
                WHERE user_id = ?
            ''', (
                user.username, user.full_name, user.position,
                user.status.value, user.stage, user.updated_at,
                user.user_id
            ))
            conn.commit()
            success = cursor.rowcount > 0

        if success:
            logger.info(f"Пользователь {user.user_id} обновлен")
        return success

    def update_user_stage(self, user_id: int, stage: int, status: UserStatus = None) -> bool:
        """Обновить этап пользователя"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            if status:
                cursor.execute('''
                    UPDATE users SET stage = ?, status = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE user_id = ?
                ''', (stage, status.value, user_id))
            else:
                cursor.execute('''
                    UPDATE users SET stage = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE user_id = ?
                ''', (stage, user_id))

            conn.commit()
            success = cursor.rowcount > 0

        if success:
            logger.info(f"Этап пользователя {user_id} обновлен: stage={stage}, status={status}")
        return success

    def get_users_by_status(self, status: UserStatus) -> List[User]:
        """Получить пользователей по статусу"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE status = ?', (status.value,))
            rows = cursor.fetchall()
            return [User.from_db_row(row) for row in rows]

    def get_all_users(self) -> List[User]:
        """Получить всех пользователей"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users ORDER BY created_at DESC')
            rows = cursor.fetchall()
            return [User.from_db_row(row) for row in rows]

    # МЕТОДЫ ДЛЯ РАБОТЫ С ОБРАТНОЙ СВЯЗЬЮ

    def save_feedback(self, user_id: int, message: str) -> Feedback:
        """Сохранить обратную связь"""
        feedback = Feedback(
            user_id=user_id,
            message=message,
            created_at=datetime.now()
        )

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO feedback (user_id, message, created_at)
                VALUES (?, ?, ?)
            ''', (feedback.user_id, feedback.message, feedback.created_at))
            feedback.id = cursor.lastrowid
            conn.commit()

        logger.info(f"Обратная связь от пользователя {user_id} сохранена")
        return feedback

    def get_recent_feedback(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получить недавнюю обратную связь"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT f.id, f.user_id, f.message, f.created_at,
                       u.full_name, u.username
                FROM feedback f
                JOIN users u ON f.user_id = u.user_id
                ORDER BY f.created_at DESC
                LIMIT ?
            ''', (limit,))

            rows = cursor.fetchall()
            return [
                {
                    'id': row[0],
                    'user_id': row[1],
                    'message': row[2],
                    'created_at': row[3],
                    'user_name': row[4],
                    'username': row[5]
                }
                for row in rows
            ]

    # МЕТОДЫ ДЛЯ РАБОТЫ С ДЕЙСТВИЯМИ ПОЛЬЗОВАТЕЛЕЙ

    def log_user_action(self, user_id: int, action: str, details: str = "") -> UserAction:
        """Логировать действие пользователя"""
        user_action = UserAction(
            user_id=user_id,
            action=action,
            details=details,
            created_at=datetime.now()
        )

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO user_actions (user_id, action, details, created_at)
                VALUES (?, ?, ?, ?)
            ''', (user_action.user_id, user_action.action, user_action.details, user_action.created_at))
            user_action.id = cursor.lastrowid
            conn.commit()

        return user_action

    def get_user_actions(self, user_id: int, limit: int = 50) -> List[UserAction]:
        """Получить действия пользователя"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM user_actions 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (user_id, limit))

            rows = cursor.fetchall()
            return [UserAction.from_db_row(row) for row in rows]

    def get_popular_actions(self, days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """Получить популярные действия за период"""
        since_date = datetime.now() - timedelta(days=days)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT action, COUNT(*) as count
                FROM user_actions 
                WHERE created_at >= ?
                GROUP BY action 
                ORDER BY count DESC 
                LIMIT ?
            ''', (since_date, limit))

            rows = cursor.fetchall()
            return [{'action': row[0], 'count': row[1]} for row in rows]

    # АНАЛИТИЧЕСКИЕ МЕТОДЫ

    def get_user_statistics(self) -> Dict[str, Any]:
        """Получить статистику пользователей"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Общее количество пользователей
            cursor.execute('SELECT COUNT(*) FROM users')
            total_users = cursor.fetchone()[0]

            # Статистика по статусам
            cursor.execute('''
                SELECT status, COUNT(*) as count 
                FROM users 
                GROUP BY status
            ''')
            status_stats = dict(cursor.fetchall())

            # Активные пользователи за неделю
            week_ago = datetime.now() - timedelta(days=7)
            cursor.execute('''
                SELECT COUNT(DISTINCT user_id) 
                FROM user_actions 
                WHERE created_at >= ?
            ''', (week_ago,))
            active_week = cursor.fetchone()[0]

            # Количество обратной связи
            cursor.execute('SELECT COUNT(*) FROM feedback')
            total_feedback = cursor.fetchone()[0]

            # Средний прогресс
            cursor.execute('SELECT AVG(stage) FROM users')
            avg_progress = cursor.fetchone()[0] or 0

            return {
                'total_users': total_users,
                'status_stats': status_stats,
                'active_week': active_week,
                'total_feedback': total_feedback,
                'avg_progress': round(avg_progress, 2),
                'completion_rate': round(
                    (status_stats.get('completed', 0) / total_users * 100) if total_users > 0 else 0,
                    2
                )
            }

    def get_daily_activity(self, days: int = 30) -> List[Dict[str, Any]]:
        """Получить ежедневную активность"""
        since_date = datetime.now() - timedelta(days=days)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    DATE(created_at) as date,
                    COUNT(DISTINCT user_id) as unique_users,
                    COUNT(*) as total_actions
                FROM user_actions 
                WHERE created_at >= ?
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            ''', (since_date,))

            rows = cursor.fetchall()
            return [
                {
                    'date': row[0],
                    'unique_users': row[1],
                    'total_actions': row[2]
                }
                for row in rows
            ]

    def cleanup_old_data(self, days: int = 90) -> int:
        """Очистка старых данных"""
        cutoff_date = datetime.now() - timedelta(days=days)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM user_actions 
                WHERE created_at < ?
            ''', (cutoff_date,))
            deleted_count = cursor.rowcount
            conn.commit()

        logger.info(f"Удалено {deleted_count} старых записей действий")
        return deleted_count

    def export_to_dict(self) -> Dict[str, List[Dict[str, Any]]]:
        """Экспорт всех данных в словарь"""
        users = [user.to_dict() for user in self.get_all_users()]

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Экспорт обратной связи
            cursor.execute('SELECT * FROM feedback ORDER BY created_at DESC')
            feedback_rows = cursor.fetchall()
            feedback = [Feedback.from_db_row(row).to_dict() for row in feedback_rows]

            # Экспорт действий (последние 1000)
            cursor.execute('''
                SELECT * FROM user_actions 
                ORDER BY created_at DESC 
                LIMIT 1000
            ''')
            action_rows = cursor.fetchall()
            actions = [UserAction.from_db_row(row).to_dict() for row in action_rows]

        return {
            'users': users,
            'feedback': feedback,
            'actions': actions,
            'exported_at': datetime.now().isoformat()
        }


# Создаем глобальный экземпляр менеджера БД
db_manager = DatabaseManager()