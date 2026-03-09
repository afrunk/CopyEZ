import os
import sqlite3
from typing import List, Tuple


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(ROOT, "instance", "copyez.db")


def _get_tables(cur: sqlite3.Cursor) -> List[str]:
    return [r[0] for r in cur.execute("select name from sqlite_master where type='table' order by name").fetchall()]


def main() -> None:
    if not os.path.exists(DB_PATH):
        raise SystemExit(f"DB not found: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    tables = _get_tables(cur)
    if "notes" not in tables:
        raise SystemExit(f"'notes' table not found. tables={tables}")

    rows: List[Tuple[int, str, str]] = cur.execute("select id, title, content from notes").fetchall()
    hits = []
    for note_id, title, content in rows:
        c = content or ""
        score = 0
        if "/static/uploads/" in c:
            score += c.count("/static/uploads/")
        if "static/uploads/" in c:
            score += c.count("static/uploads/")
        if "<img" in c.lower():
            score += 1
        if score:
            hits.append((score, note_id, title or ""))

    hits.sort(key=lambda x: (-x[0], x[1]))
    print(f"db={DB_PATH}")
    print(f"notes_total={len(rows)}")
    print(f"notes_with_possible_images={len(hits)}")
    print()
    print("score\tnote_id\ttitle")
    for score, note_id, title in hits[:80]:
        print(f"{score}\t{note_id}\t{title}")

    conn.close()


if __name__ == "__main__":
    main()

