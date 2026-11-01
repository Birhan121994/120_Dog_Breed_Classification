
"""Shareable digital dog identity card (PNG)."""

import io

import numpy as np
from PIL import Image, ImageDraw, ImageFont


def _font(size, bold=False):
    names = (
        ["DejaVuSans-Bold.ttf", "arialbd.ttf"]
        if bold
        else ["DejaVuSans.ttf", "arial.ttf"]
    )

    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            pass

    try:
        return ImageFont.load_default(size)
    except TypeError:
        return ImageFont.load_default()


def make_card(d, photo_data, show_owner=False, age=""):

    W, H = 1011, 638

    t = (
        np.linspace(0, 1, W)[None, :] * .6
        + np.linspace(0, 1, H)[:, None] * .4
    )[..., None]

    arr = (
        np.array([59, 75, 255]) * (1 - t)
        + np.array([22, 28, 110]) * t
    ).astype("uint8")

    img = Image.fromarray(arr).convert("RGBA")

    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)

    od.ellipse(
        (620, -220, 1180, 340),
        fill=(255, 107, 87, 70)
    )

    od.ellipse(
        (-160, 380, 300, 840),
        fill=(255, 255, 255, 24)
    )

    img = Image.alpha_composite(img, ov)
    dr = ImageDraw.Draw(img)

    dr.text(
        (48, 40),
        "DogID",
        font=_font(40, True),
        fill="white"
    )

    dr.text(
        (W - 48, 52),
        "DIGITAL DOG IDENTITY",
        font=_font(20),
        fill=(255, 255, 255, 200),
        anchor="ra"
    )

    S = 330

    # Accept either raw image bytes or a file path.
    if isinstance(photo_data, (bytes, bytearray)):
        p = Image.open(
            io.BytesIO(photo_data)
        ).convert("RGB")
    else:
        p = Image.open(photo_data).convert("RGB")

    sq = min(p.size)

    l = (p.width - sq) // 2
    tp = (p.height - sq) // 2

    p = p.crop(
        (l, tp, l + sq, tp + sq)
    ).resize((S, S))

    mask = Image.new("L", (S, S), 0)

    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, S, S),
        40,
        fill=255
    )

    img.paste(p, (48, 130), mask)

    x = 410

    dr.text(
        (x, 125),
        d["name"][:16],
        font=_font(62, True),
        fill="white"
    )

    dr.text(
        (x, 205),
        d["breed"],
        font=_font(30),
        fill=(255, 255, 255, 220)
    )

    rows = [
        ("SEX", d["sex"]),
        (
            "BORN",
            (d["dob"] or "Unknown")
            + (f" ({age})" if age else "")
        ),
        ("COLOUR", d["color"] or "-"),
        (
            "OWNER",
            d["owner_name"] if show_owner else "Private"
        )
    ]

    for i, (key, value) in enumerate(rows):

        y = 275 + i * 56

        dr.text(
            (x, y),
            key,
            font=_font(17),
            fill=(255, 255, 255, 160)
        )

        dr.text(
            (x + 130, y - 6),
            str(value)[:26],
            font=_font(27, True),
            fill="white"
        )

    dr.text(
        (48, 520),
        "ID",
        font=_font(18),
        fill=(255, 255, 255, 160)
    )

    dr.text(
        (48, 546),
        d["id"],
        font=_font(40, True),
        fill="white"
    )

    try:
        import qrcode

        qr = qrcode.make(
            f"dogid:{d['id']}"
        ).convert("RGB").resize((150, 150))

        dr.rounded_rectangle(
            (W - 214, H - 214, W - 48, H - 48),
            20,
            fill="white"
        )

        img.paste(
            qr,
            (W - 206, H - 206)
        )

    except Exception:
        pass

    out = Image.new(
        "RGBA",
        (W, H),
        (0, 0, 0, 0)
    )

    mk = Image.new("L", (W, H), 0)

    ImageDraw.Draw(mk).rounded_rectangle(
        (0, 0, W, H),
        48,
        fill=255
    )

    out.paste(img, (0, 0), mk)

    buf = io.BytesIO()
    out.save(buf, "PNG")

    return buf.getvalue()
