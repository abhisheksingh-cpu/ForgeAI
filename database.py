import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    database_url = os.getenv("DATABASE_URL")

    return psycopg.connect(database_url)

def create_task(task_id, requirement, status):
    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO tasks (id, requirement, status)
        VALUES (%s, %s, %s)
        """,
        (task_id, requirement, status)
    )

    conn.commit()

    cursor.close()
    conn.close()

def get_task(task_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, requirement, status, result, created_at
        FROM tasks
        WHERE id = %s
        """,
        (task_id,)
    )

    task = cursor.fetchone()

    cursor.close()
    conn.close()

    return task