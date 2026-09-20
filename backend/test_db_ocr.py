import sqlite3
import json

conn = sqlite3.connect('metrolens.db')
c = conn.cursor()
c.execute("SELECT extracted_fields FROM inspections ORDER BY created_at DESC LIMIT 1")
row = c.fetchone()
if row:
    print(json.loads(row[0]).get('raw_ocr_text', 'NOT FOUND'))
