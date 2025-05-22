
import sqlite3
import os

DB_FILE = "database.db"


def get_connection():
    return sqlite3.connect(DB_FILE)


def initialize_database():
    with get_connection() as conn:
        cursor = conn.cursor()

        # Клубы
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clubs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                city TEXT
            )
        """)

        # Спортсмены
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS athletes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                birth_date TEXT,
                weight REAL,
                club_id INTEGER,
                belt TEXT,
                FOREIGN KEY(club_id) REFERENCES clubs(id)
            )
        """)

        # Категории
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            )
        """)

        # Привязка спортсменов к категориям
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS category_athletes (
                category_id INTEGER,
                athlete_id INTEGER,
                PRIMARY KEY (category_id, athlete_id),
                FOREIGN KEY (category_id) REFERENCES categories(id),
                FOREIGN KEY (athlete_id) REFERENCES athletes(id)
            )
        """)

        # Проверим и добавим колонку belt, если нужно
        cursor.execute("PRAGMA table_info(athletes)")
        columns = [row[1] for row in cursor.fetchall()]
        if "belt" not in columns:
            cursor.execute("ALTER TABLE athletes ADD COLUMN belt TEXT")

        conn.commit()

        # Таблица турнирных сеток
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS brackets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        """)

        # Бои внутри сетки
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bracket_matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bracket_id INTEGER,
                red_athlete_id INTEGER,
                blue_athlete_id INTEGER,
                round_number INTEGER,
                winner_id INTEGER,
                FOREIGN KEY (bracket_id) REFERENCES brackets(id),
                FOREIGN KEY (red_athlete_id) REFERENCES athletes(id),
                FOREIGN KEY (blue_athlete_id) REFERENCES athletes(id),
                FOREIGN KEY (winner_id) REFERENCES athletes(id)
            )
        """)
