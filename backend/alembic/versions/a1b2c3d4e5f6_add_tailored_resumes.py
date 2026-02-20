"""add_tailored_resumes

Revision ID: a1b2c3d4e5f6
Revises: 5c79d8f19384
Create Date: 2026-02-20 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '5c79d8f19384'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'tailored_resumes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('resume_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('original_text', sa.Text(), nullable=False),
        sa.Column('tailored_text', sa.Text(), nullable=True),
        sa.Column('change_summary', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ats_score_before', sa.Float(), nullable=True),
        sa.Column('ats_score_after', sa.Float(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='PENDING'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id']),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_tailored_resumes_resume_id', 'tailored_resumes', ['resume_id'], unique=False)
    op.create_index('ix_tailored_resumes_job_id', 'tailored_resumes', ['job_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_tailored_resumes_job_id', table_name='tailored_resumes')
    op.drop_index('ix_tailored_resumes_resume_id', table_name='tailored_resumes')
    op.drop_table('tailored_resumes')
