"""Design system: theme tokens, CSS loading and HTML components."""
from pathlib import Path
import streamlit as st

THEMES = {
 "light": dict(bg="#F3F5FB", surface="#FFFFFF", surface2="#ECEFF9", ink="#0F1630", mute="#5B6485",
               line="rgba(15,22,48,.10)", accent="#3B4BFF", accent2="#FF6B57", glow="rgba(59,75,255,.16)",
               shadow="0 12px 32px rgba(30,40,110,.08)"),
 "dark":  dict(bg="#0A0E20", surface="#121833", surface2="#1A2142", ink="#EEF1FF", mute="#9AA4CC",
               line="rgba(255,255,255,.09)", accent="#7C8BFF", accent2="#FF8A78", glow="rgba(124,139,255,.20)",
               shadow="0 12px 32px rgba(0,0,0,.45)"),
}

def inject_css(dark: bool):
    t = THEMES["dark" if dark else "light"]
    tokens = ":root{" + "".join(f"--{k}:{v};" for k, v in t.items()) + "}"
    css = (Path(__file__).parent / "assets" / "style.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{tokens}{css}</style>", unsafe_allow_html=True)

def html(s):
    st.markdown(s.replace("\n", ""), unsafe_allow_html=True)

def ring(p, size="lg"):
    c = 2 * 3.14159 * 54
    return (f"<div class='ring {size}'><svg viewBox='0 0 128 128'><circle class='t' cx='64' cy='64' r='54'/>"
            f"<circle class='v' cx='64' cy='64' r='54' style='stroke-dasharray:{c:.1f};stroke-dashoffset:{c*(1-p):.1f};--c:{c:.1f}'/></svg>"
            f"<div class='n'>{p*100:.0f}<small>%</small></div></div>")

def meter(v, n=5):
    return "<span class='meter'>" + "".join(f"<i class='{'on' if i < v else ''}'></i>" for i in range(n)) + "</span>"

def trait_row(label, v):
    return f"<div class='trait'><span>{label}</span>{meter(v)}</div>"

def bar(label, pct, text=None):
    pct = max(0, min(100, pct))
    return (f"<div class='bar'><div class='bh'><span>{label}</span><b>{text or f'{pct:.0f}%'}</b></div>"
            f"<div class='bt'><div style='width:{pct:.0f}%'></div></div></div>")

def chips(items):
    return "".join(f"<span class='chip'>{i}</span>" for i in items)


def timeline(events):
    return "<div class='tl'>" + "".join(
        f"<div class='ev'><b>{e['kind']}</b><br><span>{e['detail']}</span><br><small>{e['ts']}</small></div>" for e in events) + "</div>"