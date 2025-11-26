"""Check actual database schema."""
import sqlite3

conn = sqlite3.connect('baseball_teams.db')
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("=== TABLES IN DATABASE ===")
for table in tables:
    print(f"\n{table[0]}:")
    cursor.execute(f"PRAGMA table_info({table[0]})")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]} ({col[2]})")

# Check teams
print("\n=== SAMPLE DATA ===")
cursor.execute("SELECT * FROM teams LIMIT 1")
print(f"\nteams columns: {[desc[0] for desc in cursor.description]}")
row = cursor.fetchone()
if row:
    print(f"Sample row: {row}")

# Check pitchers
cursor.execute("SELECT * FROM pitchers LIMIT 1")
print(f"\npitchers columns: {[desc[0] for desc in cursor.description]}")
row = cursor.fetchone()
if row:
    print(f"Sample row (first 10 values): {row[:10]}")

conn.close()
