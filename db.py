"""
AI-SHIP — Database
SQLite index of all models and datasets available via torrent.
"""
import sqlite3, json, hashlib
from config import DB_PATH

def _row_to_dict(row):
    if row is None:
        return None
    return dict(row)

def init():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_type TEXT NOT NULL,   -- 'model' or 'dataset'
                repo_id  TEXT NOT NULL,    -- e.g. 'meta-llama/Llama-3-8B'
                slug     TEXT UNIQUE NOT NULL,
                title    TEXT NOT NULL,
                filename TEXT NOT NULL,     -- local filename or 'HF:<repo_id>'
                size_bytes INTEGER DEFAULT 0,
                sha256   TEXT,              -- checksum if available
                magnet   TEXT,              -- full magnet URI
                torrent_file TEXT,          -- path to .torrent file
                seeded   INTEGER DEFAULT 0, -- 1 = currently seeding
                downloaded INTEGER DEFAULT 0,
                tags     TEXT DEFAULT '',   -- JSON list
                meta     TEXT DEFAULT '{}', -- JSON dict, extra HF fields
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS peers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER REFERENCES items(id),
                peer_id  TEXT,
                ip       TEXT,
                port     INTEGER,
                seen_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_type ON items(item_type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_slug ON items(slug)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_repo ON items(repo_id)")

def add_or_get(item_type, repo_id, title, filename, size_bytes=0,
                sha256=None, magnet=None, torrent_file=None, tags=None, meta=None):
    slug = repo_id.replace('/', '_')
    tags  = json.dumps(tags  or [])
    meta  = json.dumps(meta  or {})
    with sqlite3.connect(DB_PATH) as conn:
        try:
            cur = conn.execute("""
                INSERT INTO items
                    (item_type, repo_id, slug, title, filename,
                     size_bytes, sha256, magnet, torrent_file, tags, meta)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, (item_type, repo_id, slug, title, filename,
                  size_bytes, sha256, magnet, torrent_file, tags, meta))
            return cur.lastrowid
        except sqlite3.IntegrityError:
            cur = conn.execute("SELECT id FROM items WHERE slug=?", (slug,))
            row = cur.fetchone()
            return row[0]

def mark_seeding(item_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE items SET seeded=1 WHERE id=?", (item_id,))

def mark_downloaded(item_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE items SET downloaded=1 WHERE id=?", (item_id,))

def get_all(item_type=None, search=None, limit=50, offset=0):
    q = "SELECT * FROM items WHERE 1=1"
    params = []
    if item_type:
        q += " AND item_type=?"
        params.append(item_type)
    if search:
        q += " AND (title LIKE ? OR repo_id LIKE ?)"
        s = f"%{search}%"
        params.extend([s, s])
    q += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(q, params).fetchall()
        return [dict(r) for r in rows]

def get_by_slug(slug):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM items WHERE slug=?", (slug,)).fetchone()
        return dict(row) if row else None

def count_items(item_type=None):
    with sqlite3.connect(DB_PATH) as conn:
        if item_type:
            r = conn.execute("SELECT COUNT(*) FROM items WHERE item_type=?", (item_type,)).fetchone()
        else:
            r = conn.execute("SELECT COUNT(*) FROM items").fetchone()
        return r[0]

def stats():
    with sqlite3.connect(DB_PATH) as conn:
        models = conn.execute("SELECT COUNT(*) FROM items WHERE item_type='model'").fetchone()[0]
        datasets = conn.execute("SELECT COUNT(*) FROM items WHERE item_type='dataset'").fetchone()[0]
        seeded = conn.execute("SELECT COUNT(*) FROM items WHERE seeded=1").fetchone()[0]
        downloaded = conn.execute("SELECT COUNT(*) FROM items WHERE downloaded=1").fetchone()[0]
        total_size = conn.execute("SELECT SUM(size_bytes) FROM items").fetchone()[0] or 0
        return dict(models=models, datasets=datasets, seeded=seeded,
                    downloaded=downloaded, total_size_bytes=total_size)

# Init on import
init()
