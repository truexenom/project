import sqlalchemy as sa

metadata = sa.MetaData()

create_date_customer = sa.Table(
    'view_created_date_customer',
    metadata,
    sa.Column('created_date', sa.Date, primary_key=True),
    sa.Column('customer_name', sa.String(), primary_key=True),
    sa.Column('bb_b_out', sa.Float()),
    sa.Column('bb_b_in', sa.Float()),
    sa.Column('bb_b_total', sa.Float()),
    sa.Column('bb_b_in2', sa.Float()),
    sa.Column('bb_b_chr_algo1_hier', sa.Float()),
    sa.Column('bb_b_chr_algo1_hier2', sa.Float()),
    sa.Column('bb_b_chr_algo2_hier', sa.Float()),
    sa.Column('bb_b_chr_algo2_hier2', sa.Float()),
    sa.Column('bb_r_out', sa.Float()),
    sa.Column('bb_r_in', sa.Float()),
    sa.Column('bb_r_total', sa.Float()),
    sa.Column('bb_r_in2', sa.Float()),
    sa.Column('reg_b_out', sa.Float()),
    sa.Column('reg_b_in', sa.Float()),
    sa.Column('reg_b_total', sa.Float()),
    sa.Column('reg_r_out', sa.Float()),
    sa.Column('reg_r_in', sa.Float()),
    sa.Column('reg_r_total', sa.Float()),
)

billing_data_join_day = sa.Table(
    'billing_data_join_day',
    metadata,
    sa.Column('created_date', sa.Date, primary_key=True),
    sa.Column('svc', sa.Text),
    sa.Column('a_id', sa.Integer),
    sa.Column('short_name', sa.VARCHAR(255)),
    sa.Column('company_name', sa.VARCHAR(255)),
    sa.Column('customer_name', sa.VARCHAR(255), primary_key=True),
    sa.Column('pop', sa.Text()),
    sa.Column('region_name', sa.VARCHAR(255)),
    sa.Column('bb_b_out', sa.Float()),
    sa.Column('bb_b_in', sa.Float()),
    sa.Column('bb_b_total', sa.Float()),
    sa.Column('bb_b_in2', sa.Float()),
    sa.Column('bb_b_chr_algo1_hier', sa.Float()),
    sa.Column('bb_b_chr_algo1_hier2', sa.Float()),
    sa.Column('bb_b_chr_algo2_hier', sa.Float()),
    sa.Column('bb_b_chr_algo2_hier2', sa.Float()),
    sa.Column('bb_r_out', sa.Float()),
    sa.Column('bb_r_in', sa.Float()),
    sa.Column('bb_r_total', sa.Float()),
    sa.Column('bb_r_in2', sa.Float()),
    sa.Column('reg_b_out', sa.Float()),
    sa.Column('reg_b_in', sa.Float()),
    sa.Column('reg_b_total', sa.Float()),
    sa.Column('reg_r_out', sa.Float()),
    sa.Column('reg_r_in', sa.Float()),
    sa.Column('reg_r_total', sa.Float()),
)

five_min_customer_peak_day = sa.Table(
    '5min_customer_peak_day',
    metadata,
    sa.Column('created_date', sa.Date, primary_key=True),
    sa.Column('customer_name', sa.String(), primary_key=True),
    sa.Column('time', sa.Integer()),
    sa.Column('bb_gbps_total', sa.Float()),
)

five_min_customer_peak_daily = sa.Table(
    '5min_customer_peak_daily',
    metadata,
    sa.Column('created_date', sa.Date, primary_key=True),
    sa.Column('customer_name', sa.String(), primary_key=True),
    sa.Column('bb_gbps_total', sa.Float()),
)
