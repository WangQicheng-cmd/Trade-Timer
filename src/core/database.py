import sqlite3
import json
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Generator

from .config import config, BASE_DIR


TaskStatus = ("pending", "waiting", "monitoring", "triggered", "executed", "failed", "cancelled")
TaskSide = ("buy", "sell")


class Database:
    _instance: Optional["Database"] = None

    def __new__(cls) -> "Database":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self) -> None:
        db_path_str = config.get("database.path")
        db_path = Path(db_path_str)
        if not db_path.is_absolute():
            db_path = BASE_DIR / db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = str(db_path)
        self._create_tables()

    @contextmanager
    def _get_conn(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _create_tables(self) -> None:
        with self._get_conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_input TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    trigger_price REAL,
                    trigger_direction TEXT,
                    amount REAL,
                    amount_type TEXT,
                    delay_seconds INTEGER DEFAULT 0,
                    start_time TEXT,
                    trigger_time TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    error_message TEXT,
                    tx_hash TEXT,
                    fee_amount REAL,
                    params_json TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
                CREATE INDEX IF NOT EXISTS idx_tasks_start_time ON tasks(start_time);

                CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    price REAL NOT NULL,
                    timestamp TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_price_history_symbol_time ON price_history(symbol, timestamp);
            """)

    def create_task(self, task_data: Dict[str, Any]) -> int:
        now = datetime.utcnow().isoformat()
        params_json = json.dumps(task_data.get("params", {}), ensure_ascii=False)
        with self._get_conn() as conn:
            cursor = conn.execute(
                """
                INSERT INTO tasks (
                    user_input, symbol, side, trigger_price, trigger_direction,
                    amount, amount_type, delay_seconds, start_time, status,
                    created_at, updated_at, params_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task_data.get("user_input", ""),
                    task_data.get("symbol", ""),
                    task_data.get("side", "buy"),
                    task_data.get("trigger_price"),
                    task_data.get("trigger_direction"),
                    task_data.get("amount"),
                    task_data.get("amount_type"),
                    task_data.get("delay_seconds", 0),
                    task_data.get("start_time"),
                    task_data.get("status", "pending"),
                    now,
                    now,
                    params_json,
                ),
            )
            return cursor.lastrowid

    def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
            return self._row_to_dict(row) if row else None

    def list_tasks(self, status: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        query = "SELECT * FROM tasks"
        params: tuple = ()
        if status:
            query += " WHERE status = ?"
            params = (status,)
        query += " ORDER BY created_at DESC LIMIT ?"
        params = params + (limit,)
        with self._get_conn() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_dict(row) for row in rows]

    def update_task_status(self, task_id: int, status: str, **kwargs) -> None:
        now = datetime.utcnow().isoformat()
        fields = ["status = ?", "updated_at = ?"]
        values: list = [status, now]
        for key, value in kwargs.items():
            fields.append(f"{key} = ?")
            values.append(value)
        values.append(task_id)
        with self._get_conn() as conn:
            conn.execute(f"UPDATE tasks SET {', '.join(fields)} WHERE id = ?", values)

    def get_pending_tasks_to_start(self, current_time: str) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT * FROM tasks
                WHERE status IN ('pending', 'waiting')
                  AND start_time IS NOT NULL
                  AND start_time <= ?
                ORDER BY start_time ASC
                """,
                (current_time,),
            ).fetchall()
            return [self._row_to_dict(row) for row in rows]

    def get_monitoring_tasks(self) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM tasks WHERE status = 'monitoring' ORDER BY created_at ASC"
            ).fetchall()
            return [self._row_to_dict(row) for row in rows]

    def save_price(self, symbol: str, price: float) -> None:
        now = datetime.utcnow().isoformat()
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO price_history (symbol, price, timestamp) VALUES (?, ?, ?)",
                (symbol, price, now),
            )

    def get_recent_prices(self, symbol: str, limit: int = 100) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT * FROM price_history
                WHERE symbol = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (symbol, limit),
            ).fetchall()
            return [dict(row) for row in rows]

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        data = dict(row)
        if data.get("params_json"):
            try:
                data["params"] = json.loads(data["params_json"])
            except json.JSONDecodeError:
                data["params"] = {}
        else:
            data["params"] = {}
        return data


db = Database()
