"""Update attachments table to store binary file data

Revision ID: 0002_update_attachments
Revises: 0001_init_defects
Create Date: 2025-01-23 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0002_update_attachments'
down_revision: Union[str, None] = '0001_init_defects'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Обновление таблицы attachments для хранения файлов в БД"""

    # Удаляем старое поле file_url
    op.drop_column('attachments', 'file_url')

    # Добавляем новые поля для хранения бинарных данных
    op.add_column('attachments', sa.Column('file_data', sa.LargeBinary(), nullable=False))
    op.add_column('attachments', sa.Column('file_size', sa.Integer(), nullable=False))
    op.add_column('attachments', sa.Column('content_type', sa.String(length=100), nullable=False))


def downgrade() -> None:
    """Откат изменений"""

    # Удаляем новые поля
    op.drop_column('attachments', 'content_type')
    op.drop_column('attachments', 'file_size')
    op.drop_column('attachments', 'file_data')

    # Восстанавливаем старое поле
    op.add_column('attachments', sa.Column('file_url', sa.String(length=1024), nullable=False))
