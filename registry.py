
"""DogID registry: SQLite storage for dogs, photos, ownership and history."""

import hashlib
import io
import secrets
import sqlite3
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent / "registry"
PHOTOS = ROOT / "photos"
DB = ROOT / "dogid.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS dogs(
    id TEXT PRIMARY KEY,
    name TEXT,
    breed TEXT,
    sex TEXT,
    dob TEXT,
    color TEXT,
    microchip TEXT,
    owner_name TEXT,
    owner_contact TEXT,
    notes TEXT,
    status TEXT DEFAULT 'Registered',
    pin_salt TEXT,
    pin_hash TEXT,
    created TEXT
);

CREATE TABLE IF NOT EXISTS photos(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dog_id TEXT,
    path TEXT,
    emb BLOB,
    created TEXT
);

CREATE TABLE IF NOT EXISTS events(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dog_id TEXT,
    ts TEXT,
    kind TEXT,
    detail TEXT
);

CREATE TABLE IF NOT EXISTS owners(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dog_id TEXT,
    name TEXT,
    contact TEXT,
    since TEXT,
    until TEXT
);
"""

now = lambda: time.strftime("%Y-%m-%d %H:%M")


def _c():
    ROOT.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def init():
    ROOT.mkdir(parents=True, exist_ok=True)
    PHOTOS.mkdir(parents=True, exist_ok=True)

    c = _c()
    try:
        c.executescript(SCHEMA)

        columns = {
            row["name"]
            for row in c.execute(
                "PRAGMA table_info(photos)"
            ).fetchall()
        }

        if "image" not in columns:
            c.execute(
                "ALTER TABLE photos ADD COLUMN image BLOB"
            )

        c.commit()
    finally:
        c.close()


def q(sql, args=(), one=False, write=False):
    c = _c()

    try:
        cur = c.execute(sql, args)

        if write:
            c.commit()
            return cur.lastrowid

        rows = cur.fetchall()
        return (rows[0] if rows else None) if one else rows

    finally:
        c.close()


def _hash(pin, salt):
    return hashlib.pbkdf2_hmac(
        "sha256",
        pin.encode(),
        bytes.fromhex(salt),
        100_000
    ).hex()


def verify_pin(dog_id, pin):
    d = get_dog(dog_id)

    return bool(d) and secrets.compare_digest(
        _hash(pin, d["pin_salt"]),
        d["pin_hash"]
    )


def log(dog_id, kind, detail=""):
    q(
        "INSERT INTO events(dog_id,ts,kind,detail) VALUES(?,?,?,?)",
        (dog_id, now(), kind, detail),
        write=True
    )


def new_id():
    while True:
        i = "DID-" + "".join(
            secrets.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789")
            for _ in range(6)
        )

        if not get_dog(i):
            return i


def placeholder_image():
    """Generate a placeholder when the original photo is missing."""

    img = Image.new("RGB", (700, 500), "#202b55")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype(
            "DejaVuSans-Bold.ttf", 35
        )
    except Exception:
        font = ImageFont.load_default()

    draw.text(
        (350, 210),
        "DOG PHOTO",
        fill="white",
        font=font,
        anchor="mm"
    )

    draw.text(
        (350, 270),
        "Photo unavailable",
        fill="#b8c5ff",
        anchor="mm"
    )

    output = io.BytesIO()
    img.save(output, format="PNG")

    return output.getvalue()


def photo_data(photo):
    """
    Retrieve image bytes from SQLite or legacy filesystem.
    Return a placeholder instead of crashing if the image is missing.
    """

    try:
        data = photo["image"]

        if data:
            return bytes(data)

    except (KeyError, IndexError):
        pass

    try:
        path = photo["path"]

        if path and Path(path).is_file():
            return Path(path).read_bytes()

    except (KeyError, IndexError, OSError, TypeError):
        pass

    return placeholder_image()


def save_photo(dog_id, raw, emb):
    """Save optimized image bytes and embedding in SQLite."""

    img = Image.open(
        io.BytesIO(raw)
    ).convert("RGB")

    img.thumbnail((900, 900))

    buffer = io.BytesIO()

    img.save(
        buffer,
        format="JPEG",
        quality=88,
        optimize=True
    )

    image_bytes = buffer.getvalue()

    embedding = np.asarray(
        emb,
        dtype="float32"
    ).tobytes()

    q(
        """
        INSERT INTO photos(dog_id,path,image,emb,created)
        VALUES(?,NULL,?,?,?)
        """,
        (dog_id, image_bytes, embedding, now()),
        write=True
    )


def add_dog(info, pin, shots):
    """Register a new dog with its photos."""

    i = new_id()
    salt = secrets.token_hex(16)

    q(
        """
        INSERT INTO dogs(
            id,name,breed,sex,dob,color,microchip,
            owner_name,owner_contact,notes,
            pin_salt,pin_hash,created
        )
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            i,
            info["name"],
            info["breed"],
            info["sex"],
            info["dob"],
            info["color"],
            info["microchip"],
            info["owner"],
            info["contact"],
            info["notes"],
            salt,
            _hash(pin, salt),
            now()
        ),
        write=True
    )

    for raw, emb in shots:
        save_photo(i, raw, emb)

    q(
        """
        INSERT INTO owners(dog_id,name,contact,since)
        VALUES(?,?,?,?)
        """,
        (i, info["owner"], info["contact"], now()),
        write=True
    )

    log(
        i,
        "Registered",
        f"Registered by {info['owner']} with {len(shots)} photo(s)"
    )

    return i


def get_dog(i):
    return q(
        "SELECT * FROM dogs WHERE id=?",
        (i,),
        one=True
    )


def list_dogs():
    return q(
        "SELECT * FROM dogs ORDER BY created DESC"
    )


def photos(i):
    return q(
        "SELECT * FROM photos WHERE dog_id=? ORDER BY id",
        (i,)
    )


def history(i):
    return q(
        "SELECT * FROM events WHERE dog_id=? ORDER BY id DESC",
        (i,)
    )


def owners(i):
    return q(
        "SELECT * FROM owners WHERE dog_id=? ORDER BY id DESC",
        (i,)
    )


def microchip_taken(chip):
    return bool(chip) and q(
        "SELECT 1 FROM dogs WHERE microchip=?",
        (chip,),
        one=True
    ) is not None


def set_status(i, status):
    q(
        "UPDATE dogs SET status=? WHERE id=?",
        (status, i),
        write=True
    )

    log(i, "Status changed", f"Marked as {status}")


def transfer(i, name, contact, pin):
    old = get_dog(i)
    salt = secrets.token_hex(16)

    q(
        "UPDATE owners SET until=? WHERE dog_id=? AND until IS NULL",
        (now(), i),
        write=True
    )

    q(
        """
        INSERT INTO owners(dog_id,name,contact,since)
        VALUES(?,?,?,?)
        """,
        (i, name, contact, now()),
        write=True
    )

    q(
        """
        UPDATE dogs
        SET owner_name=?, owner_contact=?, pin_salt=?, pin_hash=?
        WHERE id=?
        """,
        (name, contact, salt, _hash(pin, salt), i),
        write=True
    )

    log(
        i,
        "Ownership transferred",
        f"{old['owner_name']} to {name}"
    )


def find_similar(emb, exclude=None, breed=None, top=5):
    """Find visually similar dogs using stored embeddings."""

    best = {}

    rows = q(
        """
        SELECT
            p.id AS photo_id,
            p.path,
            p.image,
            p.emb,
            d.*
        FROM photos p
        JOIN dogs d ON d.id=p.dog_id
        """
    )

    for r in rows:

        if r["id"] == exclude:
            continue

        if breed and r["breed"] != breed:
            continue

        if not r["emb"]:
            continue

        e = np.frombuffer(
            r["emb"],
            dtype="float32"
        )

        if e.shape != emb.shape:
            continue

        score = float(np.dot(emb, e))

        if (
            r["id"] not in best
            or score > best[r["id"]]["sim"]
        ):
            best[r["id"]] = {
                **dict(r),
                "sim": score
            }

    return sorted(
        best.values(),
        key=lambda m: m["sim"],
        reverse=True
    )[:top]
