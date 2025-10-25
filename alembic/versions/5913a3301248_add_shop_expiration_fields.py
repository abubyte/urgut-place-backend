"""add_shop_expiration_fields

Revision ID: 5913a3301248
Revises: 
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from datetime import datetime
from dateutil.relativedelta import relativedelta

# revision identifiers, used by Alembic.
revision: str = '5913a3301248'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Add columns as NULLABLE first
    op.add_column('shop', sa.Column('expiration_months', sa.Integer(), nullable=True))
    op.add_column('shop', sa.Column('expires_at', sa.DateTime(), nullable=True))
    op.add_column('shop', sa.Column('is_active', sa.Boolean(), nullable=True))
    
    # Step 2: Set default values for existing rows
    # Get connection to execute SQL
    connection = op.get_bind()
    
    # Update existing shops with default values
    connection.execute(
        sa.text("""
            UPDATE shop 
            SET 
                expiration_months = 12,
                expires_at = created_at + INTERVAL '12 months',
                is_active = TRUE
            WHERE expiration_months IS NULL
        """)
    )
    
    # Step 3: Make expiration_months and is_active NOT NULL (expires_at stays nullable)
    op.alter_column('shop', 'expiration_months', nullable=False)
    op.alter_column('shop', 'is_active', nullable=False)


def downgrade() -> None:
    op.drop_column('shop', 'is_active')
    op.drop_column('shop', 'expires_at')
    op.drop_column('shop', 'expiration_months')