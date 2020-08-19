"""empty message

Revision ID: 9b15148ab464
Revises: 
Create Date: 2020-08-19 04:30:00.175678

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9b15148ab464'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('accounts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('account_name', sa.String(), nullable=False),
    sa.Column('account_category', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    schema='tenant'
    )
    op.create_table('coupons',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('coupon_qty', sa.Float(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    schema='tenant'
    )
    op.create_table('customers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('contact_person', sa.String(), nullable=True),
    sa.Column('phone_number', sa.String(), nullable=True),
    sa.Column('account_type', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    schema='tenant'
    )
    op.create_table('lube_products',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('cost_price', sa.Float(), nullable=False),
    sa.Column('selling_price', sa.Float(), nullable=False),
    sa.Column('mls', sa.Float(), nullable=False),
    sa.Column('qty', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name'),
    schema='tenant'
    )
    op.create_table('products',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('product_type', sa.String(), nullable=False),
    sa.Column('price', sa.Float(), nullable=False),
    sa.Column('qty', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    schema='tenant'
    )
    op.create_table('shift',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('daytime', sa.String(), nullable=True),
    sa.Column('prepared_by', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    schema='tenant'
    )
    op.create_table('shift_underway',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('state', sa.Boolean(), nullable=False),
    sa.Column('current_shift', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    schema='tenant'
    )
    op.create_table('cash_up',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('shift_id', sa.Integer(), nullable=False),
    sa.Column('sales_amount', sa.Integer(), nullable=False),
    sa.Column('expected_amount', sa.Integer(), nullable=False),
    sa.Column('actual_amount', sa.Integer(), nullable=False),
    sa.Column('variance', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['shift_id'], ['tenant.shift.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='tenant'
    )
    op.create_table('coupon_sales',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('shift_id', sa.Integer(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=False),
    sa.Column('coupon_id', sa.Integer(), nullable=False),
    sa.Column('qty', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['coupon_id'], ['tenant.coupons.id'], ),
    sa.ForeignKeyConstraint(['product_id'], ['tenant.products.id'], ),
    sa.ForeignKeyConstraint(['shift_id'], ['tenant.shift.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='tenant'
    )
    op.create_table('customer_payments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('customer_id', sa.Integer(), nullable=False),
    sa.Column('amount', sa.Float(), nullable=False),
    sa.Column('ref', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['customer_id'], ['tenant.customers.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='tenant'
    )
    op.create_table('invoices',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('shift_id', sa.Integer(), nullable=False),
    sa.Column('customer_id', sa.Integer(), nullable=False),
    sa.Column('qty', sa.Float(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=False),
    sa.Column('price', sa.Float(), nullable=False),
    sa.Column('vehicle_number', sa.String(), nullable=True),
    sa.Column('driver_name', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['customer_id'], ['tenant.customers.id'], ),
    sa.ForeignKeyConstraint(['product_id'], ['tenant.products.id'], ),
    sa.ForeignKeyConstraint(['shift_id'], ['tenant.shift.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='tenant'
    )
    op.create_table('lube_qty',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('shift_id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('qty', sa.Float(), nullable=False),
    sa.Column('delivery_qty', sa.Float(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['product_id'], ['tenant.lube_products.id'], ),
    sa.ForeignKeyConstraint(['shift_id'], ['tenant.shift.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='tenant'
    )
    op.create_table('lubes_cash_up',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('shift_id', sa.Integer(), nullable=False),
    sa.Column('sales_amount', sa.Integer(), nullable=False),
    sa.Column('expected_amount', sa.Integer(), nullable=False),
    sa.Column('actual_amount', sa.Integer(), nullable=False),
    sa.Column('variance', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['shift_id'], ['tenant.shift.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='tenant'
    )
    op.create_table('payouts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('shift_id', sa.Integer(), nullable=False),
    sa.Column('amount', sa.Integer(), nullable=False),
    sa.Column('source_account', sa.Integer(), nullable=False),
    sa.Column('pay_out_account', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['pay_out_account'], ['tenant.accounts.id'], ),
    sa.ForeignKeyConstraint(['shift_id'], ['tenant.shift.id'], ),
    sa.ForeignKeyConstraint(['source_account'], ['tenant.accounts.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='tenant'
    )
    op.create_table('prices',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('shift_id', sa.Integer(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=False),
    sa.Column('cost_price', sa.Float(), nullable=False),
    sa.Column('selling_price', sa.Float(), nullable=False),
    sa.ForeignKeyConstraint(['product_id'], ['tenant.products.id'], ),
    sa.ForeignKeyConstraint(['shift_id'], ['tenant.shift.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='tenant'
    )
    op.create_table('sales_receipts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('shift_id', sa.Integer(), nullable=False),
    sa.Column('account_id', sa.Integer(), nullable=False),
    sa.Column('amount', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['account_id'], ['tenant.accounts.id'], ),
    sa.ForeignKeyConstraint(['shift_id'], ['tenant.shift.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='tenant'
    )
    op.create_table('tanks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=False),
    sa.Column('dip', sa.Float(), nullable=False),
    sa.ForeignKeyConstraint(['product_id'], ['tenant.products.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='tenant'
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(), nullable=False),
    sa.Column('password', sa.String(), nullable=False),
    sa.Column('role_id', sa.Integer(), nullable=False),
    sa.Column('tenant_id', sa.Integer(), nullable=False),
    sa.Column('schema', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['role_id'], ['public.roles.id'], ),
    sa.ForeignKeyConstraint(['tenant_id'], ['public.tenants.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('username'),
    schema='tenant'
    )
    op.create_table('fuel_delivery',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('shift_id', sa.Integer(), nullable=False),
    sa.Column('tank_id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('qty', sa.Float(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=True),
    sa.Column('document_number', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['product_id'], ['tenant.products.id'], ),
    sa.ForeignKeyConstraint(['shift_id'], ['tenant.shift.id'], ),
    sa.ForeignKeyConstraint(['tank_id'], ['tenant.tanks.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='tenant'
    )
    op.create_table('pumps',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('tank_id', sa.Integer(), nullable=False),
    sa.Column('litre_reading', sa.Float(), nullable=False),
    sa.Column('money_reading', sa.Float(), nullable=False),
    sa.ForeignKeyConstraint(['tank_id'], ['tenant.tanks.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='tenant'
    )
    op.create_table('tank_dips',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('dip', sa.Float(), nullable=False),
    sa.Column('tank_id', sa.Integer(), nullable=False),
    sa.Column('shift_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['shift_id'], ['tenant.shift.id'], ),
    sa.ForeignKeyConstraint(['tank_id'], ['tenant.tanks.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='tenant'
    )
    op.create_table('pump_readings',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=False),
    sa.Column('litre_reading', sa.Float(), nullable=False),
    sa.Column('money_reading', sa.Float(), nullable=True),
    sa.Column('pump_id', sa.Integer(), nullable=False),
    sa.Column('shift_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['product_id'], ['tenant.products.id'], ),
    sa.ForeignKeyConstraint(['pump_id'], ['tenant.pumps.id'], ),
    sa.ForeignKeyConstraint(['shift_id'], ['tenant.shift.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='tenant'
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('pump_readings', schema='tenant')
    op.drop_table('tank_dips', schema='tenant')
    op.drop_table('pumps', schema='tenant')
    op.drop_table('fuel_delivery', schema='tenant')
    op.drop_table('users', schema='tenant')
    op.drop_table('tanks', schema='tenant')
    op.drop_table('sales_receipts', schema='tenant')
    op.drop_table('prices', schema='tenant')
    op.drop_table('payouts', schema='tenant')
    op.drop_table('lubes_cash_up', schema='tenant')
    op.drop_table('lube_qty', schema='tenant')
    op.drop_table('invoices', schema='tenant')
    op.drop_table('customer_payments', schema='tenant')
    op.drop_table('coupon_sales', schema='tenant')
    op.drop_table('cash_up', schema='tenant')
    op.drop_table('shift_underway', schema='tenant')
    op.drop_table('shift', schema='tenant')
    op.drop_table('products', schema='tenant')
    op.drop_table('lube_products', schema='tenant')
    op.drop_table('customers', schema='tenant')
    op.drop_table('coupons', schema='tenant')
    op.drop_table('accounts', schema='tenant')
    # ### end Alembic commands ###
