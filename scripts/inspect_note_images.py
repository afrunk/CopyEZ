import os
import re
import sqlite3
import sys


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(ROOT, "instance", "copyez.db")


def main() -> None:
    note_id = int(sys.argv[1]) if len(sys.argv) > 1 else 13
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    row = cur.execute("select id,title,content from notes where id=?", (note_id,)).fetchone()
    if not row:
        raise SystemExit(f"note not found: {note_id}")
    _, title, content = row
    content = content or ""
    print(f"id={note_id}")
    print(f"title={title}")
    print(f"len(content)={len(content)}")
    print()

    # Print any markdown image syntaxes and raw <img> tags
    md_imgs = re.findall(r"!\[[^\]]*\]\([^\)]+\)", content)
    html_imgs = re.findall(r"<img[^>]*>", content, flags=re.IGNORECASE)
    uploads = re.findall(r"(?:/static/uploads/|static/uploads/)[^)\s\"'>]+", content)

    print(f"markdown_images={len(md_imgs)}")
    for s in md_imgs[:50]:
        print("MD:", s)
    print()

    print(f"html_img_tags={len(html_imgs)}")
    for s in html_imgs[:50]:
        print("HTML:", s)
    print()

    print(f"upload_paths={len(uploads)}")
    for s in uploads[:80]:
        print("UP:", s)

    conn.close()


if __name__ == "__main__":
    main()

