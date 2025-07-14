"""Initial migration to create all tables.

Revision ID: 24d507e55555
Revises: 
Create Date: 2024-02-23 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = '24d507e55555'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create builds table
    op.create_table('builds',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_name', sa.String(), nullable=False),
        sa.Column('build_number', sa.Integer(), nullable=False),
        sa.Column('result', sa.String(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('duration', sa.Integer(), nullable=True),
        sa.Column('parameters', sa.JSON(), nullable=True),
        sa.Column('url', sa.String(), nullable=True),
        sa.Column('console_log', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_builds_job_name'), 'builds', ['job_name'], unique=False)

    # Create patterns table
    op.create_table('patterns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_name', sa.String(), nullable=False),
        sa.Column('pattern', sa.String(), nullable=False),
        sa.Column('frequency', sa.Integer(), nullable=False),
        sa.Column('last_seen', sa.DateTime(), nullable=False),
        sa.Column('solution', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_patterns_job_name'), 'patterns', ['job_name'], unique=False)

    # Create analyses table
    op.create_table('analyses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('build_id', sa.Integer(), nullable=False),
        sa.Column('last_success_id', sa.Integer(), nullable=True),
        sa.Column('error_patterns', sa.JSON(), nullable=False),
        sa.Column('differences', sa.JSON(), nullable=False),
        sa.Column('recommendations', sa.JSON(), nullable=False),
        sa.Column('severity', sa.String(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['build_id'], ['builds.id'], ),
        sa.ForeignKeyConstraint(['last_success_id'], ['builds.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('build_id')
    )

    # Create actions table
    op.create_table('actions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('build_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('pattern_id', sa.Integer(), nullable=True),
        sa.Column('result', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['build_id'], ['builds.id'], ),
        sa.ForeignKeyConstraint(['pattern_id'], ['patterns.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    # Drop tables in reverse order to avoid foreign key constraint violations
    op.drop_table('actions')
    op.drop_table('analyses')
    op.drop_table('patterns')
    op.drop_table('builds')
