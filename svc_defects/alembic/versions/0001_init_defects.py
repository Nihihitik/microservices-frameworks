from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001_init_defects"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enums
    defect_priority = sa.Enum("LOW", "MEDIUM", "HIGH", "CRITICAL", name="defect_priority")
    defect_status = sa.Enum(
        "NEW",
        "IN_PROGRESS",
        "ON_REVIEW",
        "CLOSED",
        "CANCELED",
        name="defect_status",
    )
    defect_priority.create(op.get_bind(), checkfirst=True)
    defect_status.create(op.get_bind(), checkfirst=True)

    # defects
    op.create_table(
        "defects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("priority", defect_priority, nullable=False),
        sa.Column("status", defect_status, nullable=False),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assignee_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_defects_project_id", "defects", ["project_id"], unique=False)
    op.create_index("ix_defects_author_id", "defects", ["author_id"], unique=False)
    op.create_index("ix_defects_assignee_id", "defects", ["assignee_id"], unique=False)

    # comments
    op.create_table(
        "comments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("defect_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["defect_id"], ["defects.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_comments_defect_id", "comments", ["defect_id"], unique=False)

    # attachments
    op.create_table(
        "attachments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("defect_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_url", sa.String(length=1024), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("uploaded_by_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["defect_id"], ["defects.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_attachments_defect_id", "attachments", ["defect_id"], unique=False)

    # defect_history
    op.create_table(
        "defect_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("defect_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("changed_by_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("field_name", sa.String(length=100), nullable=False),
        sa.Column("old_value", sa.String(length=255), nullable=True),
        sa.Column("new_value", sa.String(length=255), nullable=True),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["defect_id"], ["defects.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_defect_history_defect_id", "defect_history", ["defect_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_defect_history_defect_id", table_name="defect_history")
    op.drop_table("defect_history")

    op.drop_index("ix_attachments_defect_id", table_name="attachments")
    op.drop_table("attachments")

    op.drop_index("ix_comments_defect_id", table_name="comments")
    op.drop_table("comments")

    op.drop_index("ix_defects_assignee_id", table_name="defects")
    op.drop_index("ix_defects_author_id", table_name="defects")
    op.drop_index("ix_defects_project_id", table_name="defects")
    op.drop_table("defects")

    op.execute("DROP TYPE IF EXISTS defect_priority")
    op.execute("DROP TYPE IF EXISTS defect_status")
