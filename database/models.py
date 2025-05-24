# database/models.py
"""
Модели данных для OnboardingBuddy
"""
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum


class UserStatus(Enum):
    """Статусы пользователей"""
    NEW = "new"
    PREBOARDING = "preboarding"
    PREBOARDED = "preboarded"
    ONBOARDING = "onboarding"
    COMPLETED = "completed"


@dataclass
class User:
    """Модель пользователя"""
    user_id: int
    username: Optional[str] = None
    full_name: Optional[str] = None
    position: Optional[str] = None
    status: UserStatus = UserStatus.NEW
    stage: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_db_row(cls, row: tuple) -> 'User':
        """Создать объект User из строки БД"""
        if not row:
            return None

        return cls(
            user_id=row[0],
            username=row[1],
            full_name=row[2],
            position=row[3],
            status=UserStatus(row[4]) if row[4] else UserStatus.NEW,
            stage=row[5] or 0,
            created_at=datetime.fromisoformat(row[6]) if row[6] else None,
            updated_at=datetime.fromisoformat(row[7]) if row[7] else None
        )

    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать в словарь"""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'full_name': self.full_name,
            'position': self.position,
            'status': self.status.value,
            'stage': self.stage,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @property
    def progress_percentage(self) -> float:
        """Прогресс в процентах"""
        max_stage = 10
        return min(100, (self.stage / max_stage) * 100)

    @property
    def status_emoji(self) -> str:
        """Эмодзи статуса"""
        emoji_map = {
            UserStatus.NEW: "🆕",
            UserStatus.PREBOARDING: "🔄",
            UserStatus.PREBOARDED: "✅",
            UserStatus.ONBOARDING: "🚀",
            UserStatus.COMPLETED: "🎉"
        }
        return emoji_map.get(self.status, "❓")

    @property
    def status_name(self) -> str:
        """Человекочитаемое название статуса"""
        name_map = {
            UserStatus.NEW: "Новый пользователь",
            UserStatus.PREBOARDING: "Пребординг в процессе",
            UserStatus.PREBOARDED: "Пребординг завершен",
            UserStatus.ONBOARDING: "Онбординг в процессе",
            UserStatus.COMPLETED: "Онбординг завершен"
        }
        return name_map.get(self.status, "Неизвестно")


@dataclass
class Feedback:
    """Модель обратной связи"""
    id: Optional[int] = None
    user_id: int = 0
    message: str = ""
    created_at: Optional[datetime] = None

    @classmethod
    def from_db_row(cls, row: tuple) -> 'Feedback':
        """Создать объект Feedback из строки БД"""
        if not row:
            return None

        return cls(
            id=row[0],
            user_id=row[1],
            message=row[2],
            created_at=datetime.fromisoformat(row[3]) if row[3] else None
        )

    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать в словарь"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'message': self.message,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class UserAction:
    """Модель действия пользователя"""
    id: Optional[int] = None
    user_id: int = 0
    action: str = ""
    details: str = ""
    created_at: Optional[datetime] = None

    @classmethod
    def from_db_row(cls, row: tuple) -> 'UserAction':
        """Создать объект UserAction из строки БД"""
        if not row:
            return None

        return cls(
            id=row[0],
            user_id=row[1],
            action=row[2],
            details=row[3],
            created_at=datetime.fromisoformat(row[4]) if row[4] else None
        )

    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать в словарь"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'details': self.details,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class OnboardingStage:
    """Этапы онбординга"""

    # Пребординг
    REGISTRATION = 1
    DOCUMENTS_INTRO = 2
    DOCUMENTS_MAIN = 3
    DOCUMENTS_TK = 4
    DOCUMENTS_COMPLETE = 5

    # Онбординг
    ONBOARDING_START = 6
    EMAIL_ACCESS = 7
    TEAM_INTRO = 8
    MEETINGS = 9
    COMPLETE = 10

    @classmethod
    def get_stage_name(cls, stage: int) -> str:
        """Получить название этапа"""
        stage_names = {
            1: "Регистрация",
            2: "Знакомство с документами",
            3: "Основные документы",
            4: "Документы по ТК РФ",
            5: "Завершение пребординга",
            6: "Начало онбординга",
            7: "Получение доступов",
            8: "Знакомство с командой",
            9: "Планерки и встречи",
            10: "Завершение онбординга"
        }
        return stage_names.get(stage, f"Этап {stage}")

    @classmethod
    def get_next_stage_description(cls, current_stage: int) -> str:
        """Получить описание следующего этапа"""
        next_stage_descriptions = {
            0: "Начните с раздела 'Пребординг'",
            1: "Ознакомьтесь с требуемыми документами",
            2: "Отправьте основные документы",
            3: "Отправьте документы по ТК РФ",
            4: "Дождитесь обработки документов",
            5: "Переходите к разделу 'Онбординг'",
            6: "Получите доступ к корпоративной почте",
            7: "Изучите информацию о команде",
            8: "Ознакомьтесь с планерками",
            9: "Завершите онбординг",
            10: "Все этапы пройдены! 🎉"
        }
        return next_stage_descriptions.get(current_stage, "Продолжайте процесс адаптации")


class DatabaseSchema:
    """Схема базы данных"""

    CREATE_USERS_TABLE = '''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            position TEXT,
            status TEXT DEFAULT 'new',
            stage INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    '''

    CREATE_FEEDBACK_TABLE = '''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    '''

    CREATE_USER_ACTIONS_TABLE = '''
        CREATE TABLE IF NOT EXISTS user_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    '''

    # Индексы для оптимизации
    CREATE_INDEXES = [
        'CREATE INDEX IF NOT EXISTS idx_users_status ON users(status)',
        'CREATE INDEX IF NOT EXISTS idx_users_stage ON users(stage)',
        'CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON feedback(user_id)',
        'CREATE INDEX IF NOT EXISTS idx_actions_user_id ON user_actions(user_id)',
        'CREATE INDEX IF NOT EXISTS idx_actions_created_at ON user_actions(created_at)'
    ]