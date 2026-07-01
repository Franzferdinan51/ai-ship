"""AI-SHIP — FTS5 Full-Text Search Index"""
import sqlite3
from config import DB_PATH

def init_fts():
    """Create the FTS5 virtual table and populate it from items table."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DROP TABLE IF EXISTS items_fts")
        conn.execute("""
            CREATE VIRTUAL TABLE items_fts USING fts5(
                repo_id, title, tags, meta,
                content='items',
                content_rowid='id'
            )
        """)
        conn.execute("""
            INSERT INTO items_fts(rowid, repo_id, title, tags, meta)
            SELECT id, repo_id, title, tags, meta FROM items
        """)
        conn.execute("DROP TABLE IF EXISTS items_fts_idx")
        conn.execute("""
            CREATE TABLE items_fts_idx AS
            SELECT rowid, item_type, slug, downloaded FROM items
        """)
    return True

def search_fts(query, item_type=None, limit=30):
    """Full-text search over repo_id, title, and tags."""
    if not query or len(query.strip()) < 2:
        return []
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT i.repo_id, i.title, i.slug, i.item_type,
                   i.downloaded, i.size_bytes, i.created_at
            FROM items_fts f
            JOIN items i ON i.id = f.rowid
            WHERE items_fts MATCH ?
              AND (? IS NULL OR i.item_type = ?)
            LIMIT ?
        """, (query, item_type, item_type, limit)).fetchall()
        return [dict(r) for r in rows]

def update_fts(slug):
    """Re-index a single item after add_or_get."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT OR REPLACE INTO items_fts(rowid, repo_id, title, tags, meta)
            SELECT id, repo_id, title, tags, meta FROM items WHERE slug=?
        """, (slug,))

if __name__ == "__main__":
    init_fts()
    print("FTS5 index initialized")
    for q in ["llama", "whisper"]:
        r = search_fts(q, limit=5)
        print(f"Search '{q}': {len(r)} results")
