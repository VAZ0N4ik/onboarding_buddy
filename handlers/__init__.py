# handlers/__init__.py
"""
Модуль обработчиков команд и сообщений
"""

from .start import start_command, help_command, status_command, contacts_command
from .preboarding import handle_preboarding
from .onboarding import handle_onboarding
from .info import handle_useful_info
from .faq import handle_faq
from .contacts import handle_contacts, handle_support
from .feedback import handle_feedback, handle_progress
from .admin import admin_command, broadcast_command
from .callbacks import handle_all_callbacks

__all__ = [
    'start_command', 'help_command', 'status_command', 'contacts_command',
    'handle_preboarding', 'handle_onboarding', 'handle_useful_info',
    'handle_faq', 'handle_contacts', 'handle_support', 'handle_feedback',
    'handle_progress', 'admin_command', 'broadcast_command', 'handle_all_callbacks'
]