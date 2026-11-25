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

# =====================================
# ASTRA LONG-TERM PERSONAL MEMORY
# =====================================

def initialize_personal_memory():

    with get_connection() as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS personal_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_key TEXT NOT NULL COLLATE NOCASE UNIQUE,
                memory_value TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'General',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)


initialize_personal_memory()

# =====================================
# ASTRA STUDY PLANNER DATABASE
# =====================================

def initialize_study_planner():

    with get_connection() as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS study_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER NOT NULL,
                topic TEXT NOT NULL,
                study_date TEXT NOT NULL,
                start_time TEXT NOT NULL,
                duration_minutes INTEGER NOT NULL
                    CHECK(duration_minutes > 0),
                priority TEXT NOT NULL DEFAULT 'Medium'
                    CHECK(priority IN ('Low', 'Medium', 'High')),
                status TEXT NOT NULL DEFAULT 'Pending'
                    CHECK(status IN ('Pending', 'Completed')),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(subject_id) REFERENCES subjects(id)
            )
        """)


initialize_study_planner()

# =====================================
# ASTRA QUIZ AND PERFORMANCE DATABASE
# =====================================

def initialize_quiz_database():

    with get_connection() as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS quiz_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER NOT NULL,
                topic TEXT NOT NULL,
                total_questions INTEGER NOT NULL
                    CHECK(total_questions > 0),
                correct_answers INTEGER NOT NULL
                    CHECK(correct_answers >= 0),
                percentage REAL NOT NULL
                    CHECK(percentage BETWEEN 0 AND 100),
                difficulty TEXT NOT NULL DEFAULT 'Medium',
                feedback TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                CHECK(correct_answers <= total_questions),
                FOREIGN KEY(subject_id) REFERENCES subjects(id)
            )
        """)


initialize_quiz_database()

# =====================================
# ASTRA NOTIFICATION DATABASE
# =====================================

def initialize_notification_database():

    with get_connection() as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS notification_history (
                notification_key TEXT PRIMARY KEY,
                notification_type TEXT NOT NULL,
                message TEXT NOT NULL,
                sent_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)


initialize_notification_database()