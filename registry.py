"""DogID registry: SQLite storage for dogs, photos, ownership and history."""
import hashlib, io, secrets, sqlite3, time
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).parent / "registry"
PHOTOS, DB = ROOT / "photos", ROOT / "dogid.db"
SCHEMA = """
CREATE TABLE IF NOT EXISTS dogs(id TEXT PRIMARY KEY, name TEXT, breed TEXT, sex TEXT, dob TEXT, color TEXT,
 microchip TEXT, owner_name TEXT, owner_contact TEXT, notes TEXT, status TEXT DEFAULT 'Registered',
 pin_salt TEXT, pin_hash TEXT, created TEXT);
CREATE TABLE IF NOT EXISTS photos(id INTEGER PRIMARY KEY AUTOINCREMENT, dog_id TEXT, path TEXT, emb BLOB, created TEXT);
CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT, dog_id TEXT, ts TEXT, kind TEXT, detail TEXT);
CREATE TABLE IF NOT EXISTS owners(id INTEGER PRIMARY KEY AUTOINCREMENT, dog_id TEXT, name TEXT, contact TEXT, since TEXT, until TEXT);
"""
now = lambda: time.strftime("%Y-%m-%d %H:%M")


def _c():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def init():
    PHOTOS.mkdir(parents=True, exist_ok=True)
    c = _c(); c.executescript(SCHEMA); c.commit(); c.close()


def q(sql, args=(), one=False, write=False):
    c = _c()
    try:
        cur = c.execute(sql, args)
        if write:
            c.commit(); return cur.lastrowid
        rows = cur.fetchall()
        return (rows[0] if rows else None) if one else rows
    finally:
        c.close()


def _hash(pin, salt):
    return hashlib.pbkdf2_hmac("sha256", pin.encode(), bytes.fromhex(salt), 100_000).hex()


def verify_pin(dog_id, pin):
    d = get_dog(dog_id)
    return bool(d) and secrets.compare_digest(_hash(pin, d["pin_salt"]), d["pin_hash"])


def log(dog_id, kind, detail=""):
    q("INSERT INTO events(dog_id,ts,kind,detail) VALUES(?,?,?,?)", (dog_id, now(), kind, detail), write=True)


def new_id():
    while True:
        i = "DID-" + "".join(secrets.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(6))
        if not get_dog(i):
            return i


def save_photo(dog_id, raw, emb):
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    img.thumbnail((900, 900))
    path = PHOTOS / f"{dog_id}_{int(time.time()*1000)}.jpg"
    img.save(path, quality=88)
    q("INSERT INTO photos(dog_id,path,emb,created) VALUES(?,?,?,?)", (dog_id, str(path), emb.astype("float32").tobytes(), now()), write=True)


def add_dog(info, pin, shots):
    """shots: list of (raw_bytes, embedding)."""
    i, salt = new_id(), secrets.token_hex(16)
    q("INSERT INTO dogs(id,name,breed,sex,dob,color,microchip,owner_name,owner_contact,notes,pin_salt,pin_hash,created) "
      "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
      (i, info["name"], info["breed"], info["sex"], info["dob"], info["color"], info["microchip"], info["owner"],
       info["contact"], info["notes"], salt, _hash(pin, salt), now()), write=True)
    for raw, emb in shots:
        save_photo(i, raw, emb)
    q("INSERT INTO owners(dog_id,name,contact,since) VALUES(?,?,?,?)", (i, info["owner"], info["contact"], now()), write=True)
    log(i, "Registered", f"Registered by {info['owner']} with {len(shots)} photo(s)")
    return i


def get_dog(i):
    return q("SELECT * FROM dogs WHERE id=?", (i,), one=True)


def list_dogs():
    return q("SELECT * FROM dogs ORDER BY created DESC")


def photos(i):
    return q("SELECT * FROM photos WHERE dog_id=? ORDER BY id", (i,))


def history(i):
    return q("SELECT * FROM events WHERE dog_id=? ORDER BY id DESC", (i,))


def owners(i):
    return q("SELECT * FROM owners WHERE dog_id=? ORDER BY id DESC", (i,))


def microchip_taken(chip):
    return bool(chip) and q("SELECT 1 FROM dogs WHERE microchip=?", (chip,), one=True) is not None


def set_status(i, status):
    q("UPDATE dogs SET status=? WHERE id=?", (status, i), write=True)
    log(i, "Status changed", f"Marked as {status}")


def transfer(i, name, contact, pin):
    old = get_dog(i)
    salt = secrets.token_hex(16)
    q("UPDATE owners SET until=? WHERE dog_id=? AND until IS NULL", (now(), i), write=True)
    q("INSERT INTO owners(dog_id,name,contact,since) VALUES(?,?,?,?)", (i, name, contact, now()), write=True)
    q("UPDATE dogs SET owner_name=?, owner_contact=?, pin_salt=?, pin_hash=? WHERE id=?", (name, contact, salt, _hash(pin, salt), i), write=True)
    log(i, "Ownership transferred", f"{old['owner_name']} to {name}")


def find_similar(emb, exclude=None, breed=None, top=5):
    """Best cosine similarity per dog across all its photos."""
    best = {}
    for r in q("SELECT p.path AS path, p.emb AS emb, d.* FROM photos p JOIN dogs d ON d.id=p.dog_id"):
        if r["id"] == exclude or (breed and r["breed"] != breed):
            continue
        e = np.frombuffer(r["emb"], dtype="float32")
        if e.shape != emb.shape:
            continue
        s = float(np.dot(emb, e))
        if r["id"] not in best or s > best[r["id"]]["sim"]:
            best[r["id"]] = {**dict(r), "sim": s}
    return sorted(best.values(), key=lambda m: m["sim"], reverse=True)[:top]