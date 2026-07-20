"""
Migration script to add the currency column to the orders table.
Run this once to update an existing database.

Existing rows are backfilled with USD, which is correct: every order placed
before multi-market pricing went live was charged in dollars.
"""
from database.models import get_engine
from sqlalchemy import text, inspect


def migrate():
    """Add currency column to orders table (SQLite and PostgreSQL safe)."""
    engine = get_engine()

    columns = [col['name'] for col in inspect(engine).get_columns('orders')]
    if 'currency' in columns:
        print("✅ Column 'currency' already exists on orders — nothing to do.")
        return

    with engine.connect() as conn:
        # SQLite has no ADD COLUMN IF NOT EXISTS, hence the inspector check above.
        conn.execute(text("ALTER TABLE orders ADD COLUMN currency VARCHAR(3)"))
        conn.execute(text("UPDATE orders SET currency = 'USD' WHERE currency IS NULL"))
        conn.commit()

    print("✅ Migration complete! currency column added to orders, existing rows set to USD.")


if __name__ == "__main__":
    migrate()
