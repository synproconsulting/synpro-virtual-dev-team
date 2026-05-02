"""Add orchestrator_states table for crash recovery

Revision ID: 004
Revises: 003
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create orchestrator_states table."""
    op.create_table(
        'orchestrator_states',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('sprint_id', sa.Integer(), nullable=False),
        sa.Column('sprint_name', sa.String(length=255), nullable=False),
        sa.Column('jira_project_key', sa.String(length=50), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'RUNNING', 'PAUSED', 'COMPLETED', 'FAILED', 'CANCELLED', name='orchestratorstatus'), nullable=False),
        sa.Column('ticket_queue', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('completed_tickets', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('failed_tickets', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('current_ticket', sa.String(length=50), nullable=True),
        sa.Column('total_tickets', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_checkpoint_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    
    # Create indexes for efficient queries
    op.create_index('ix_orchestrator_states_sprint_id', 'orchestrator_states', ['sprint_id'])
    op.create_index('ix_orchestrator_states_status', 'orchestrator_states', ['status'])
    op.create_index('ix_orchestrator_states_jira_project_key', 'orchestrator_states', ['jira_project_key'])
    op.create_index('ix_orchestrator_states_updated_at', 'orchestrator_states', ['updated_at'])


def downgrade() -> None:
    """Drop orchestrator_states table."""
    op.drop_index('ix_orchestrator_states_updated_at', table_name='orchestrator_states')
    op.drop_index('ix_orchestrator_states_jira_project_key', table_name='orchestrator_states')
    op.drop_index('ix_orchestrator_states_status', table_name='orchestrator_states')
    op.drop_index('ix_orchestrator_states_sprint_id', table_name='orchestrator_states')
    op.drop_table('orchestrator_states')
    op.execute('DROP TYPE orchestratorstatus')
