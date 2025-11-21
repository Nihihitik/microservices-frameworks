from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001_init_projects"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=True),
        sa.Column("address", sa.String(length=255), nullable=False),
        sa.Column("customer_name", sa.String(length=255), nullable=False),
        sa.Column(
            "stage",
            sa.Enum("DESIGN", "CONSTRUCTION", "FINISHING", "COMPLETED", name="project_stage"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("ACTIVE", "ON_HOLD", "CLOSED", name="project_status"),
            nullable=False,
        ),
        sa.Column("manager_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_projects_manager_id", "projects", ["manager_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_projects_manager_id", table_name="projects")
    op.drop_table("projects")
    op.execute("DROP TYPE IF EXISTS project_stage")
    op.execute("DROP TYPE IF EXISTS project_status")
