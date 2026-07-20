"""
Migration script to add the currency column to the orders table.
Run this once per database, before deploying the multi-market pricing code.

Existing rows are backfilled with USD, which is correct: every order placed
before multi-market pricing went live was charged in dollars.

Usage:
    python migrate_add_order_currency.py           # local SQLite
    python migrate_add_order_currency.py --yes     # required for a remote database

The --yes guard exists because .env points at the production Postgres on
Railway, so running this without thinking would touch the live store.
"""
import sys
from dotenv import load_dotenv

# Load .env the same way main.py does, so the target matches what the app uses.
load_dotenv()

from database.models import get_engine, DATABASE_URL  # noqa: E402  (must follow load_dotenv)
from sqlalchemy import text, inspect  # noqa: E402


def migrate(confirmed: bool):
    """Add currency column to orders table (SQLite and PostgreSQL safe)."""
    is_remote = not DATABASE_URL.startswith('sqlite')
    target = 'REMOTE/PRODUCTION' if is_remote else 'local SQLite'
    print(f"🎯 Target database: {target}")

    if is_remote and not confirmed:
        print("\n⛔ Refusing to modify a remote database without confirmation.")
        print("   Re-run with --yes if this is really the database you meant:")
        print("   python migrate_add_order_currency.py --yes")
        sys.exit(1)

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
    migrate(confirmed='--yes' in sys.argv)
