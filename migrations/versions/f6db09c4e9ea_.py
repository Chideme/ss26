"""empty message

Revision ID: f6db09c4e9ea
Revises: 
Create Date: 2021-04-20 16:45:24.442695

"""
from alembic import op
import sqlalchemy as sa
from werkzeug.security import check_password_hash, generate_password_hash


# revision identifiers, used by Alembic.
revision = 'f6db09c4e9ea'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute("CREATE SCHEMA tenant")
    packages_table = op.create_table('packages',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(), nullable=False),
                    sa.Column('number_of_days', sa.Integer(), nullable=False),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('name'),
                    schema='public'
                    )
    roles_table = op.create_table('roles',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            schema='public'
            )
    system_table = op.create_table('system_admin',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('password', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        schema='public'
        )
    op.create_table('tenants',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('address', sa.String(), nullable=False),
    sa.Column('company_email', sa.String(), nullable=False),
    sa.Column('database_url', sa.String(), nullable=False),
    sa.Column('tenant_code', sa.String(), nullable=False),
    sa.Column('contact_person', sa.String(), nullable=True),
    sa.Column('phone_number', sa.String(), nullable=True),
    sa.Column('schema', sa.String(), nullable=True),
    sa.Column('active', sa.Date(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name'),
    sa.UniqueConstraint('schema'),
    schema='public'
    )
    op.create_table('accounts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.Integer(), nullable=False),
    sa.Column('account_name', sa.String(), nullable=False),
    sa.Column('account_category', sa.String(), nullable=False),
    sa.Column('entry', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('account_name'),
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
    op.create_table('subscriptions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('tenant_id', sa.Integer(), nullable=False),
    sa.Column('package', sa.Integer(), nullable=False),
    sa.Column('amount', sa.Float(), nullable=True),
    sa.Column('expiration_date', sa.Date(), nullable=False),
    sa.ForeignKeyConstraint(['package'], ['public.packages.id'], ),
    sa.ForeignKeyConstraint(['tenant_id'], ['public.tenants.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='public'
    )

    op.create_table('logged_in_users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('tenant_id', sa.Integer(), nullable=False),
    sa.Column('user_count', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['tenant_id'], ['public.tenants.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='public'
    )

    op.create_table('cash_up',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('shift_id', sa.Integer(), nullable=False),
    sa.Column('sales_amount', sa.Float(), nullable=False),
    sa.Column('expected_amount', sa.Float(), nullable=False),
    sa.Column('actual_amount', sa.Float(), nullable=False),
    sa.Column('variance', sa.Float(), nullable=False),
    sa.ForeignKeyConstraint(['shift_id'], ['tenant.shift.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='tenant'
    )
    op.create_table('customers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('contact_person', sa.String(), nullable=True),
    sa.Column('address', sa.String(), nullable=True),
    sa.Column('phone_number', sa.String(), nullable=True),
    sa.Column('account_id', sa.Integer(), nullable=False),
    sa.Column('opening_balance', sa.Float(), nullable=False),
    sa.ForeignKeyConstraint(['account_id'], ['tenant.accounts.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name'),
    schema='tenant'
    )
    op.create_table('lubes_cash_up',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('shift_id', sa.Integer(), nullable=False),
    sa.Column('sales_amount', sa.Float(), nullable=False),
    sa.Column('expected_amount', sa.Float(), nullable=False),
    sa.Column('actual_amount', sa.Float(), nullable=False),
    sa.Column('variance', sa.Float(), nullable=False),
    sa.ForeignKeyConstraint(['shift_id'], ['tenant.shift.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='tenant'
    )
    op.create_table('payouts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('shift_id', sa.Integer(), nullable=False),
    sa.Column('amount', sa.Float(), nullable=False),
    sa.Column('source_account', sa.Integer(), nullable=False),
    sa.Column('pay_out_account', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['pay_out_account'], ['tenant.accounts.id'], ),
    sa.ForeignKeyConstraint(['shift_id'], ['tenant.shift.id'], ),
    sa.ForeignKeyConstraint(['source_account'], ['tenant.accounts.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='tenant'
    )
    op.create_table('products',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('product_type', sa.String(), nullable=False),
    sa.Column('cost_price', sa.Float(), nullable=True),
    sa.Column('avg_price', sa.Float(), nullable=True),
    sa.Column('selling_price', sa.Float(), nullable=False),
    sa.Column('unit', sa.Float(), nullable=False),
    sa.Column('qty', sa.Float(), nullable=False),
    sa.Column('account_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['account_id'], ['tenant.accounts.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name'),
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
    op.create_table('supplier',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('contact_person', sa.String(), nullable=True),
    sa.Column('address', sa.String(), nullable=True),
    sa.Column('phone_number', sa.String(), nullable=True),
    sa.Column('account_id', sa.Integer(), nullable=False),
    sa.Column('opening_balance', sa.Float(), nullable=False),
    sa.ForeignKeyConstraint(['account_id'], ['tenant.accounts.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name'),
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
    op.create_table('coupons',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('coupon_qty', sa.Float(), nullable=False),
    sa.Column('customer_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['customer_id'], ['tenant.customers.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name'),
    schema='tenant'
    )
    op.create_table('customer_transactions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('txn_type', sa.String(), nullable=False),
    sa.Column('customer_id', sa.Integer(), nullable=False),
    sa.Column('amount', sa.Float(), nullable=False),
    sa.Column('post_balance', sa.Float(), nullable=False),
    sa.ForeignKeyConstraint(['customer_id'], ['tenant.customers.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='tenant'
    )
    op.create_index(op.f('ix_tenant_customer_transactions_customer_id'), 'customer_transactions', ['customer_id'], unique=False, schema='tenant')
    op.create_table('journals',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('details', sa.String(), nullable=True),
    sa.Column('dr', sa.Integer(), nullable=False),
    sa.Column('cr', sa.Integer(), nullable=False),
    sa.Column('amount', sa.Float(), nullable=False),
    sa.Column('created_by', sa.Integer(), nullable=False),
    sa.Column('created_on', sa.DateTime(), nullable=False),
    sa.Column('updated', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['cr'], ['tenant.accounts.id'], ),
    sa.ForeignKeyConstraint(['created_by'], ['tenant.users.id'], ),
    sa.ForeignKeyConstraint(['dr'], ['tenant.accounts.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='tenant'
    )
    op.create_table('journals_pending',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('details', sa.String(), nullable=True),
    sa.Column('dr', sa.Integer(), nullable=False),
    sa.Column('cr', sa.Integer(), nullable=False),
    sa.Column('amount', sa.Float(), nullable=False),
    sa.Column('created_by', sa.Integer(), nullable=False),
    sa.Column('created_on', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['cr'], ['tenant.accounts.id'], ),
    sa.ForeignKeyConstraint(['created_by'], ['tenant.users.id'], ),
    sa.ForeignKeyConstraint(['dr'], ['tenant.accounts.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='tenant'
    )
    op.create_table('lube_qty',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('shift_id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('qty', sa.Float(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['product_id'], ['tenant.products.id'], ),
    sa.ForeignKeyConstraint(['shift_id'], ['tenant.shift.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='tenant'
    )
    op.create_index(op.f('ix_tenant_lube_qty_shift_id'), 'lube_qty', ['shift_id'], unique=False, schema='tenant')
    op.create_table('prices',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('shift_id', sa.Integer(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=False),
    sa.Column('cost_price', sa.Float(), nullable=False),
    sa.Column('selling_price', sa.Float(), nullable=False),
    sa.Column('avg_price', sa.Float(), nullable=False),
    sa.ForeignKeyConstraint(['product_id'], ['tenant.products.id'], ),
    sa.ForeignKeyConstraint(['shift_id'], ['tenant.shift.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='tenant'
    )
    op.create_index(op.f('ix_tenant_prices_shift_id'), 'prices', ['shift_id'], unique=False, schema='tenant')
    op.create_table('supplier_transactions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('txn_type', sa.String(), nullable=False),
    sa.Column('supplier_id', sa.Integer(), nullable=False),
    sa.Column('amount', sa.Float(), nullable=False),
    sa.Column('ref', sa.String(), nullable=True),
    sa.Column('post_balance', sa.Float(), nullable=False),
    sa.ForeignKeyConstraint(['supplier_id'], ['tenant.supplier.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='tenant'
    )
    op.create_index(op.f('ix_tenant_supplier_transactions_supplier_id'), 'supplier_transactions', ['supplier_id'], unique=False, schema='tenant')
    op.create_table('tanks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=False),
    sa.Column('dip', sa.Float(), nullable=False),
    sa.ForeignKeyConstraint(['product_id'], ['tenant.products.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name'),
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
    op.create_table('credit_notes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('shift_id', sa.Integer(), nullable=False),
    sa.Column('customer_id', sa.Integer(), nullable=False),
    sa.Column('qty', sa.Float(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=False),
    sa.Column('price', sa.Float(), nullable=False),
    sa.Column('vehicle_number', sa.String(), nullable=True),
    sa.Column('driver_name', sa.String(), nullable=True),
    sa.Column('customer_txn_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['customer_id'], ['tenant.customers.id'], ),
    sa.ForeignKeyConstraint(['customer_txn_id'], ['tenant.customer_transactions.id'], ),
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
    sa.Column('customer_txn_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['customer_id'], ['tenant.customers.id'], ),
    sa.ForeignKeyConstraint(['customer_txn_id'], ['tenant.customer_transactions.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='tenant'
    )
    op.create_table('debit_notes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('shift_id', sa.Integer(), nullable=False),
    sa.Column('tank_id', sa.Integer(), nullable=True),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('qty', sa.Float(), nullable=False),
    sa.Column('cost_price', sa.Float(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=True),
    sa.Column('document_number', sa.String(), nullable=True),
    sa.Column('supplier', sa.Integer(), nullable=False),
    sa.Column('supplier_txn_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['product_id'], ['tenant.products.id'], ),
    sa.ForeignKeyConstraint(['shift_id'], ['tenant.shift.id'], ),
    sa.ForeignKeyConstraint(['supplier'], ['tenant.supplier.id'], ),
    sa.ForeignKeyConstraint(['supplier_txn_id'], ['tenant.supplier_transactions.id'], ),
    sa.ForeignKeyConstraint(['tank_id'], ['tenant.tanks.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='tenant'
    )
    op.create_table('delivery',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('shift_id', sa.Integer(), nullable=False),
    sa.Column('tank_id', sa.Integer(), nullable=True),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('qty', sa.Float(), nullable=False),
    sa.Column('cost_price', sa.Float(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=True),
    sa.Column('document_number', sa.String(), nullable=True),
    sa.Column('supplier', sa.Integer(), nullable=False),
    sa.Column('supplier_txn_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['product_id'], ['tenant.products.id'], ),
    sa.ForeignKeyConstraint(['shift_id'], ['tenant.shift.id'], ),
    sa.ForeignKeyConstraint(['supplier'], ['tenant.supplier.id'], ),
    sa.ForeignKeyConstraint(['supplier_txn_id'], ['tenant.supplier_transactions.id'], ),
    sa.ForeignKeyConstraint(['tank_id'], ['tenant.tanks.id'], ),
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
    sa.Column('customer_txn_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['customer_id'], ['tenant.customers.id'], ),
    sa.ForeignKeyConstraint(['customer_txn_id'], ['tenant.customer_transactions.id'], ),
    sa.ForeignKeyConstraint(['product_id'], ['tenant.products.id'], ),
    sa.ForeignKeyConstraint(['shift_id'], ['tenant.shift.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='tenant'
    )
    op.create_table('ledger',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('account_id', sa.Integer(), nullable=False),
    sa.Column('journal_id', sa.Integer(), nullable=False),
    sa.Column('txn_type', sa.String(), nullable=False),
    sa.Column('amount', sa.Float(), nullable=False),
    sa.Column('post_balance', sa.Float(), nullable=False),
    sa.Column('updated_on', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['account_id'], ['tenant.accounts.id'], ),
    sa.ForeignKeyConstraint(['journal_id'], ['tenant.journals.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='tenant'
    )
    op.create_index(op.f('ix_tenant_ledger_account_id'), 'ledger', ['account_id'], unique=False, schema='tenant')
    op.create_table('pumps',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('tank_id', sa.Integer(), nullable=False),
    sa.Column('litre_reading', sa.Float(), nullable=False),
    sa.Column('money_reading', sa.Float(), nullable=False),
    sa.ForeignKeyConstraint(['tank_id'], ['tenant.tanks.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name'),
    schema='tenant'
    )
    op.create_table('supplier_payments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('supplier_id', sa.Integer(), nullable=False),
    sa.Column('amount', sa.Float(), nullable=False),
    sa.Column('ref', sa.String(), nullable=True),
    sa.Column('supplier_txn_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['supplier_id'], ['tenant.supplier.id'], ),
    sa.ForeignKeyConstraint(['supplier_txn_id'], ['tenant.supplier_transactions.id'], ),
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
    op.create_index(op.f('ix_tenant_tank_dips_shift_id'), 'tank_dips', ['shift_id'], unique=False, schema='tenant')
    op.create_table('attendant_sales',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('attendant_id', sa.Integer(), nullable=False),
    sa.Column('pump_id', sa.Integer(), nullable=False),
    sa.Column('shift_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['attendant_id'], ['tenant.users.id'], ),
    sa.ForeignKeyConstraint(['pump_id'], ['tenant.pumps.id'], ),
    sa.ForeignKeyConstraint(['shift_id'], ['tenant.shift.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='tenant'
    )
    op.create_index(op.f('ix_tenant_attendant_sales_shift_id'), 'attendant_sales', ['shift_id'], unique=False, schema='tenant')
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
    op.create_index(op.f('ix_tenant_pump_readings_shift_id'), 'pump_readings', ['shift_id'], unique=False, schema='tenant')
    
    
    password = generate_password_hash("Kud@94")
    op.bulk_insert(system_table,
    [
        {'name':'Admin','password':password}
    ],
     multiinsert=False)

    op.bulk_insert(packages_table,
    [
        {'name':'free','number_of_days':7},
        {'name':'monthly','number_of_days':30},
        {'name':'yearly','number_of_days':365}
    ],
     multiinsert=False)

   

    op.bulk_insert(roles_table,
    [
        {'name':'admin'},
        {'name':'assistant manager'},
        {'name':'attendant'}
    ],
     multiinsert=False)
    
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'logged_in_users', schema='public', type_='foreignkey')
    op.drop_index(op.f('ix_tenant_pump_readings_shift_id'), table_name='pump_readings', schema='tenant')
    op.drop_table('pump_readings', schema='tenant')
    op.drop_index(op.f('ix_tenant_attendant_sales_shift_id'), table_name='attendant_sales', schema='tenant')
    op.drop_table('attendant_sales', schema='tenant')
    op.drop_index(op.f('ix_tenant_tank_dips_shift_id'), table_name='tank_dips', schema='tenant')
    op.drop_table('tank_dips', schema='tenant')
    op.drop_table('supplier_payments', schema='tenant')
    op.drop_table('pumps', schema='tenant')
    op.drop_index(op.f('ix_tenant_ledger_account_id'), table_name='ledger', schema='tenant')
    op.drop_table('ledger', schema='tenant')
    op.drop_table('invoices', schema='tenant')
    op.drop_table('delivery', schema='tenant')
    op.drop_table('debit_notes', schema='tenant')
    op.drop_table('customer_payments', schema='tenant')
    op.drop_table('credit_notes', schema='tenant')
    op.drop_table('coupon_sales', schema='tenant')
    op.drop_table('tanks', schema='tenant')
    op.drop_index(op.f('ix_tenant_supplier_transactions_supplier_id'), table_name='supplier_transactions', schema='tenant')
    op.drop_table('supplier_transactions', schema='tenant')
    op.drop_index(op.f('ix_tenant_prices_shift_id'), table_name='prices', schema='tenant')
    op.drop_table('prices', schema='tenant')
    op.drop_index(op.f('ix_tenant_lube_qty_shift_id'), table_name='lube_qty', schema='tenant')
    op.drop_table('lube_qty', schema='tenant')
    op.drop_table('journals_pending', schema='tenant')
    op.drop_table('journals', schema='tenant')
    op.drop_index(op.f('ix_tenant_customer_transactions_customer_id'), table_name='customer_transactions', schema='tenant')
    op.drop_table('customer_transactions', schema='tenant')
    op.drop_table('coupons', schema='tenant')
    op.drop_table('users', schema='tenant')
    op.drop_table('supplier', schema='tenant')
    op.drop_table('sales_receipts', schema='tenant')
    op.drop_table('products', schema='tenant')
    op.drop_table('payouts', schema='tenant')
    op.drop_table('lubes_cash_up', schema='tenant')
    op.drop_table('customers', schema='tenant')
    op.drop_table('cash_up', schema='tenant')
    op.drop_table('subscriptions', schema='public')
    op.drop_table('shift_underway', schema='tenant')
    op.drop_table('shift', schema='tenant')
    op.drop_table('accounts', schema='tenant')
    op.drop_table('tenants', schema='public')
    op.drop_table('system_admin', schema='public')
    op.drop_table('roles', schema='public')
    op.drop_table('packages', schema='public')
    # ### end Alembic commands ###
