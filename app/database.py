import sqlite3
import json
from datetime import datetime

DB_PATH = "workflows.db"

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS workflows (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            name      TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS triggers (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_id INTEGER NOT NULL,
            type        TEXT NOT NULL,
            token       TEXT UNIQUE NOT NULL,
            FOREIGN KEY (workflow_id) REFERENCES workflows(id)
        );

        CREATE TABLE IF NOT EXISTS actions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_id INTEGER NOT NULL,
            order_num   INTEGER NOT NULL,
            type        TEXT NOT NULL,
            config      TEXT NOT NULL,
            FOREIGN KEY (workflow_id) REFERENCES workflows(id)
        );

        CREATE TABLE IF NOT EXISTS executions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_id INTEGER NOT NULL,
            status      TEXT NOT NULL,
            input_data  TEXT,
            created_at  TEXT NOT NULL,
            FOREIGN KEY (workflow_id) REFERENCES workflows(id)
        );

        CREATE INDEX IF NOT EXISTS idx_triggers_token
            ON triggers(token);
        CREATE INDEX IF NOT EXISTS idx_actions_workflow
            ON actions(workflow_id);
        CREATE INDEX IF NOT EXISTS idx_executions_workflow
            ON executions(workflow_id);
    """)
    conn.commit()
    conn.close()

def create_workflow(name: str) -> int:
    """Создаёт workflow. Возвращает id."""
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO workflows (name) VALUES (?)", (name,)
    )
    workflow_id = cur.lastrowid
    conn.commit()
    conn.close()
    return workflow_id

def create_trigger(workflow_id: int, type: str, token: str):
    conn = get_conn()
    conn.execute(
        "INSERT INTO triggers (workflow_id, type, token) VALUES (?, ?, ?)",
        (workflow_id, type, token)
    )
    conn.commit()
    conn.close()

def create_action(workflow_id: int, order_num: int, type: str, config: dict):
    conn = get_conn()
    conn.execute(
        "INSERT INTO actions (workflow_id, order_num, type, config) VALUES (?, ?, ?, ?)",
        (workflow_id, order_num, type, json.dumps(config))
    )
    conn.commit()
    conn.close()

def get_workflow_by_token(token: str) -> dict | None:
    """Возвращает workflow с триггером и действиями по токену."""
    conn = get_conn()

    trigger = conn.execute(
        "SELECT * FROM triggers WHERE token = ?", (token,)
    ).fetchone()

    if not trigger:
        conn.close()
        return None

    workflow = conn.execute(
        "SELECT * FROM workflows WHERE id = ? AND is_active = 1",
        (trigger["workflow_id"],)
    ).fetchone()

    if not workflow:
        conn.close()
        return None

    actions = conn.execute(
        "SELECT * FROM actions WHERE workflow_id = ? ORDER BY order_num",
        (workflow["id"],)
    ).fetchall()

    conn.close()

    return {
        **dict(workflow),
        "trigger": dict(trigger),
        "actions": [
            {**dict(a), "config": json.loads(a["config"])}
            for a in actions
        ]
    }

def get_workflow(workflow_id: int) -> dict | None:
    conn = get_conn()
    workflow = conn.execute(
        "SELECT * FROM workflows WHERE id = ?", (workflow_id,)
    ).fetchone()

    if not workflow:
        conn.close()
        return None

    trigger = conn.execute(
        "SELECT * FROM triggers WHERE workflow_id = ?", (workflow_id,)
    ).fetchone()

    actions = conn.execute(
        "SELECT * FROM actions WHERE workflow_id = ? ORDER BY order_num",
        (workflow_id,)
    ).fetchall()

    conn.close()

    return {
        **dict(workflow),
        "trigger": dict(trigger) if trigger else None,
        "actions": [
            {**dict(a), "config": json.loads(a["config"])}
            for a in actions
        ]
    }

def get_all_workflows() -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM workflows ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def log_execution(workflow_id: int, status: str, input_data: dict):
    conn = get_conn()
    conn.execute(
        "INSERT INTO executions (workflow_id, status, input_data, created_at) VALUES (?, ?, ?, ?)",
        (workflow_id, status, json.dumps(input_data), datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()


def get_executions(workflow_id: int) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM executions WHERE workflow_id = ? ORDER BY id DESC",
        (workflow_id,)
    ).fetchall()
    conn.close()
    return [
        {**dict(r), "input_data": json.loads(r["input_data"]) if r["input_data"] else None}
        for r in rows
    ]