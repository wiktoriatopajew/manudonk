from database.models import get_engine
from sqlalchemy import inspect

engine = get_engine()
inspector = inspect(engine)
columns = inspector.get_columns('products')

print('Kolumny w tabeli products:')
for col in columns:
    print(f"  - {col['name']}: {col['type']}")
