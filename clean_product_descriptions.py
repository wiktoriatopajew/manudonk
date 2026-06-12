"""
Clean product descriptions to remove MISREPRESENTATION-risk wording from the
live Railway database (e.g. "this is the same service manual your local <BRAND>
dealer will use", "official", "factory original") and fix the "2O17" year typo.

SAFE BY DEFAULT:
  - Running with no flags = DRY RUN (reads only, writes nothing, prints stats).
  - Pass --apply to actually write. Before writing it saves a full JSON backup
    of every affected row (id, title, description) so changes are reversible.

Usage:
    python clean_product_descriptions.py            # dry run
    python clean_product_descriptions.py --apply     # backup + write
"""
import sys, re, json, datetime
from dotenv import dotenv_values
import sqlalchemy as sa

APPLY = "--apply" in sys.argv

# ---- Cleaning rules (validated against the live data) -------------------------
DEALER = re.compile(r"[^.\n]{0,170}?\bdealer will use\b[^.]*\.", re.I)        # whole sentence with the misleading "dealer will use" claim
FACT   = re.compile(r"\s*This is the same factory service manual[^.]*\.", re.I)
# "THIS IS THE <BRAND> FACTORY MANUAL" -> claims the file IS the official OEM manual
FACTORY_CLAIM = re.compile(r"THIS IS THE\s+([A-Z0-9&/\.\- ]{1,20}?)\s*FACTORY MANUAL", re.I)

def clean_description(d: str):
    """Return (new_description, changed?)."""
    if not d:
        return d, False
    o = d
    d = DEALER.sub(" ", d)                              # drop "...dealer will use..." sentence
    d = FACT.sub(" ", d)                                # drop "this is the same factory service manual..." sentence
    d = FACTORY_CLAIM.sub("THIS IS A COMPREHENSIVE SERVICE MANUAL", d)  # neutralise "this is the OEM factory manual" claim
    d = re.sub(r"factory original", "comprehensive", d, flags=re.I)
    d = re.sub(r"\bofficial\b", "comprehensive", d, flags=re.I)
    d = re.sub(r"100% original", "high-quality", d, flags=re.I)
    d = re.sub(r"\b2[Oo](\d{2})\b", r"20\1", d)         # 2O17 -> 2017
    d = re.sub(r"[ \t]{2,}", " ", d)                    # collapse double spaces only (keep line breaks)
    return d, (o != d)

def clean_title(t: str):
    if not t:
        return t
    return re.sub(r"\b2[Oo](\d{2})\b", r"20\1", t)      # 2O17 -> 2017 in titles too


def main():
    url = dotenv_values(".env").get("DATABASE_URL")
    if url and url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    if not url:
        print("ERROR: DATABASE_URL not found in .env"); return
    eng = sa.create_engine(url, connect_args={"connect_timeout": 30})

    with eng.connect() as c:
        rows = c.execute(sa.text("SELECT id, title, description FROM products")).fetchall()

    changes = []  # (id, old_title, new_title, old_desc, new_desc)
    for _id, t, d in rows:
        nd, ch = clean_description(d)
        nt = clean_title(t)
        if ch or nt != t:
            changes.append((_id, t, nt, d, nd))

    print(f"Products total: {len(rows)} | products to update: {len(changes)}")
    if not changes:
        print("Nothing to change."); return

    if not APPLY:
        print("\nDRY RUN (no writes). Sample of changes:")
        for _id, t, nt, od, ndd in changes[:3]:
            print("=" * 60, f"\nID {_id}")
            if nt != t:
                print(f"  TITLE: {t!r} -> {nt!r}")
            if ndd != od:
                print(f"  DESC before: {od[:160]!r}")
                print(f"  DESC after : {ndd[:160]!r}")
        print(f"\nRun with --apply to write (a JSON backup will be saved first).")
        return

    # APPLY: backup first
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = f"backup_products_{ts}.json"
    with open(backup, "w", encoding="utf-8") as f:
        json.dump([{"id": c_[0], "title": c_[1], "description": c_[3]} for c_ in changes],
                  f, ensure_ascii=False, indent=2)
    print(f"Backup of {len(changes)} rows saved to: {backup}")

    updated = 0
    with eng.begin() as conn:  # single transaction
        for _id, t, nt, od, ndd in changes:
            conn.execute(
                sa.text("UPDATE products SET title=:t, description=:d WHERE id=:id"),
                {"t": nt, "d": ndd, "id": _id},
            )
            updated += 1
    print(f"DONE. Updated {updated} products. Backup: {backup}")


if __name__ == "__main__":
    main()
