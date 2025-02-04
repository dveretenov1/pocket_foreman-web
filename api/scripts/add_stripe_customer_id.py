from sqlalchemy import create_engine, MetaData, Table, Column, String
from alembic import op
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SQLALCHEMY_DATABASE_URL

def upgrade():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    meta = MetaData()
    meta.reflect(bind=engine)
    
    # Add stripe_customer_id column if it doesn't exist
    if 'users' in meta.tables:
        users = meta.tables['users']
        if 'stripe_customer_id' not in users.c:
            op.add_column('users', Column('stripe_customer_id', String, nullable=True))
            print("Added stripe_customer_id column to users table")
        else:
            print("stripe_customer_id column already exists")
    else:
        print("users table not found")

def downgrade():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    meta = MetaData()
    meta.reflect(bind=engine)
    
    # Remove stripe_customer_id column if it exists
    if 'users' in meta.tables:
        users = meta.tables['users']
        if 'stripe_customer_id' in users.c:
            op.drop_column('users', 'stripe_customer_id')
            print("Removed stripe_customer_id column from users table")
        else:
            print("stripe_customer_id column not found")
    else:
        print("users table not found")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()
