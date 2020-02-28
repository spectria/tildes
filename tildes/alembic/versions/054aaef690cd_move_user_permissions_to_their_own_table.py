"""Move user permissions to their own table

Revision ID: 054aaef690cd
Revises: 51a1012f4f63
Create Date: 2020-02-28 00:13:17.634015

"""
from collections import defaultdict

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from tildes.models.user import User


# revision identifiers, used by Alembic.
revision = "054aaef690cd"
down_revision = "51a1012f4f63"
branch_labels = None
depends_on = None

# minimal definition for users table to query/update
users_table = sa.sql.table(
    "users",
    sa.sql.column("user_id", sa.Integer),
    sa.sql.column("permissions", sa.dialects.postgresql.JSONB(none_as_null=True)),
)


def upgrade():
    permissions_table = op.create_table(
        "user_permissions",
        sa.Column("permission_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=True),
        sa.Column("permission", sa.Text(), nullable=False),
        sa.Column(
            "permission_type",
            postgresql.ENUM("ALLOW", "DENY", name="userpermissiontype"),
            server_default="ALLOW",
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["group_id"],
            ["groups.group_id"],
            name=op.f("fk_user_permissions_group_id_groups"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
            name=op.f("fk_user_permissions_user_id_users"),
        ),
        sa.PrimaryKeyConstraint("permission_id", name=op.f("pk_user_permissions")),
    )

    # convert existing permissions to rows in the new table
    session = sa.orm.Session(bind=op.get_bind())

    users = session.query(users_table).filter("permissions" != None).all()

    permission_rows = []
    for user in users:
        if isinstance(user.permissions, str):
            permission_rows.append(
                {"user_id": user.user_id, "permission": user.permissions}
            )
        elif isinstance(user.permissions, list):
            for permission in user.permissions:
                permission_rows.append(
                    {"user_id": user.user_id, "permission": permission}
                )

    if permission_rows:
        op.bulk_insert(permissions_table, permission_rows)

    op.drop_column("users", "permissions")


def downgrade():
    op.add_column(
        "users",
        sa.Column(
            "permissions",
            postgresql.JSONB(astext_type=sa.Text()),
            autoincrement=False,
            nullable=True,
        ),
    )

    # convert user_permissions rows back to JSONB columns in the users table
    session = sa.orm.Session(bind=op.get_bind())

    permissions_table = sa.sql.table(
        "user_permissions",
        sa.sql.column("user_id", sa.Integer),
        sa.sql.column("permission", sa.Text),
    )
    permissions_rows = session.query(permissions_table).all()

    permissions_updates = defaultdict(list)
    for permission in permissions_rows:
        permissions_updates[permission.user_id].append(permission.permission)

    for user_id, permissions in permissions_updates.items():
        session.query(users_table).filter_by(user_id=user_id).update(
            {"permissions": permissions}, synchronize_session=False
        )

    session.commit()

    op.drop_table("user_permissions")
    op.execute("drop type userpermissiontype")
