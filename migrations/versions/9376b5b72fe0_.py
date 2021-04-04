"""empty message

Revision ID: 9376b5b72fe0
Revises: 876bc92c61c8
Create Date: 2021-04-03 21:32:00.653093

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9376b5b72fe0'
down_revision = '876bc92c61c8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    conn = op.get_bind()
    schemas = conn.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name NOT IN ('information_schema', 'pg_catalog','pg_toast', 'pg_temp_1', 'pg_toast_temp_1','public')").fetchall()
    schemas = [ str(x[0]) for x in schemas]
    for schema in schemas:
        print("Executing on schema {}".format(schema))
        op.execute("SET search_path TO {}".format(schema))
        op.create_table('ledger',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('date', sa.Date(), nullable=False),
            sa.Column('account_id', sa.Integer(), nullable=False),
            sa.Column('journal_id', sa.Integer(), nullable=False),
            sa.Column('txn_type', sa.String(), nullable=False),
            sa.Column('amount', sa.Float(), nullable=False),
            sa.Column('post_balance', sa.Float(), nullable=False),
            sa.Column('updated_on', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ),
            sa.ForeignKeyConstraint(['journal_id'], ['journals.id'], ),
            sa.PrimaryKeyConstraint('id')
            )
        op.execute("SET search_path TO default")
    op.execute("SET search_path TO default")
    
    
    
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    conn = op.get_bind()
    schemas = conn.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name NOT IN ('information_schema', 'pg_catalog','pg_toast', 'pg_temp_1', 'pg_toast_temp_1','public')").fetchall()
    schemas = [ str(x[0]) for x in schemas]
    for schema in schemas:
        print("Executing on schema {}".format(schema))
        op.execute("SET search_path TO {}".format(schema))
        op.drop_table('ledger')
        op.execute("SET search_path TO default")
    op.execute("SET search_path TO default")
    