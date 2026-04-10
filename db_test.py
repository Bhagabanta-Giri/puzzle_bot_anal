import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# 1. Establish the connection
try:
    conn = psycopg2.connect(
        dbname="shakuntala_db",
        user="postgres",           # Default user is usually 'postgres'
        password=os.getenv("DB_PASS"), 
        host="localhost",
        port="5432"
    )
    
    # 2. Create a cursor object
    cur = conn.cursor()
    
    # 3. Execute a command (Creating a table)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS puzzles (
            id SERIAL PRIMARY KEY,
            question TEXT,
            answer TEXT
        );
    ''')
    
    # 4. Save your changes (VERY IMPORTANT in Postgres)
    conn.commit()
    
    print("Success! Table created in PostgreSQL.")
    
    # 5. Clean up
    cur.close()
    conn.close()

except Exception as e:
    print(f"Error connecting to the database: {e}")