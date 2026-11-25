import sqlite3
from pathlib import Path
from contextlib import contextmanager

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "astra.db"

DATA_DIR.mkdir(parents=True, exist_ok=True)


@contextmanager
def get_connection():

    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row

    try:
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def initialize_database():

    with get_connection() as conn:

        conn.executescript("""
        
        CREATE TABLE IF NOT EXISTS student_profile (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            name TEXT NOT NULL,
            course TEXT NOT NULL,
            branch TEXT,
            semester INTEGER NOT NULL,
            university TEXT
        );

        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL COLLATE NOCASE,
            semester INTEGER NOT NULL,
            UNIQUE(name, semester)
        );

        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            deadline TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending'
                CHECK(status IN ('Pending', 'Completed')),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(subject_id) REFERENCES subjects(id)
        );

        CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            exam_date TEXT NOT NULL,
            syllabus TEXT,
            FOREIGN KEY(subject_id) REFERENCES subjects(id)
        );

        """)


initialize_database()


if __name__ == "__main__":
    print("ASTRA academic database initialized.")
    print(f"Database location: {DB_PATH}")