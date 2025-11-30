"""Temporary script to check database."""
import sqlite3

conn = sqlite3.connect('baseball_teams.db')
cursor = conn.cursor()

# Check indexes
print("=== Indexes ===")
cursor.execute("SELECT * FROM sqlite_master WHERE type='index'")
for r in cursor.fetchall():
    print(r)

# Check teams table structure
print("\n=== Teams Table Schema ===")
cursor.execute("SELECT sql FROM sqlite_master WHERE name='teams'")
result = cursor.fetchone()
if result:
    print(result[0])

conn.close()
