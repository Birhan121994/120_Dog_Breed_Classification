"""DogID - AI-powered digital dog identity.  Run: streamlit run app.py"""
import datetime as dt
import numpy as np
import streamlit as st
import registry as reg
from data import DB, FIELDS, norm, pretty, profile
from engine import SIM_HIGH, SIM_MID, analyze, care_plan, compat_score, get_breeds, wiki_summary
from idcard import make_card
from ui import bar, chips, html, inject_css, meter, ring, timeline, trait_row

st.set_page_config(page_title="DogID - Digital Dog Identity", page_icon="🐾", layout="wide")
try:
    default_dark = st.context.theme.type == "dark"
except Exception:
    default_dark = False
st.session_state.setdefault("dark", default_dark)
st.session_state.setdefault("last", None)
inject_css(st.session_state["dark"])
reg.init()

IMG = ["jpg", "jpeg", "png"]


def age_text(dob):
    if not dob:
        return ""
    b = dt.date.fromisoformat(dob)
    m = (dt.date.today().year - b.year) * 12 + dt.date.today().month - b.month
    return f"{m//12}y {m%12}m" if m >= 12 else f"{max(m,0)} months"


def sim_label(s):
    return ("Very similar", "") if s >= SIM_HIGH else ("Similar", "") if s >= SIM_MID else ("Weak resemblance", "")



def match_rows(matches, show_contact_if_lost=True):
    if not matches:
        st.info("No registered dogs to compare against yet.")
        return

    for i, m in enumerate(matches, 1):
        c1, c2 = st.columns(
            [1, 5],
            vertical_alignment="center"
        )

        # Missing images now display a placeholder.
        c1.image(
            reg.photo_data(m),
            use_container_width=True
        )

        label, _ = sim_label(m["sim"])

        extra = (
            f" · Contact: {m['owner_contact']}"
            if show_contact_if_lost and m["status"] == "Lost"
            else ""
        )

        with c2:
            html(
                f"<div class='match'><div class='mt'>"
                f"<b>{m['name']}</b> "
                f"<span class='idno'>{m['id']}</span> "
                f"<span class='st {m['status']}'>{m['status']}</span>"
                f"<div>{chips([pretty(m['breed']), m['sex'], label])}</div>"
                f"<div class='note'>Visual similarity "
                f"{m['sim']*100:.0f}%{extra}</div>"
                f"</div>{ring(max(m['sim'],0), 'sm')}</div>"
            )


# ---- top bar ----
c1, c2 = st.columns([6, 1.2], vertical_alignment="center")
with c1:
    html("<div class='top'><div class='logo'>🐾</div><div class='brand'>DogID<small>Digital dog identity</small></div></div>")
with c2:
    st.toggle("Dark mode", key="dark")

try:
    BREEDS = get_breeds()
except FileNotFoundError:
    st.error("The 'Images/' folder was not found. Place it next to app.py so breed names can be loaded.")
    st.stop()
NAMES = {pretty(b): b for b in BREEDS}

tab_id, tab_reg, tab_dogs, tab_find, tab_fit, tab_cmp, tab_about = st.tabs(
    ["Identify", "Register", "Registry", "Find a dog", "Lifestyle", "Compare", "About"])

# ================= Identify =================
with tab_id:
    left, right = st.columns([1.1, 1], gap="large", vertical_alignment="center")
    with left:
        html(f"<div class='hero'><h1 class='disp'>Every dog,<br><span class='grad'>a digital identity.</span></h1>"
             f"<p>Identify the breed from one photo, register your dog, and carry a shareable ID card.</p>"
             f"{chips([f'{len(BREEDS)} breeds', 'Dog registry', 'Photo matching', 'ID cards'])}</div>")
    with right:
        src = st.radio("Source", ["Upload", "Camera"], horizontal=True, label_visibility="collapsed")
        file = (st.file_uploader("Drop a dog photo", type=IMG, label_visibility="collapsed")
                if src == "Upload" else st.camera_input("Take a picture", label_visibility="collapsed"))
    if file:
        data = file.getvalue()
        with st.spinner("Analysing photo..."):
            top, _ = analyze(data)
        best, conf = top[0]
        st.session_state["last"] = {"bytes": data, "breed": best}
        p = profile(best)
        verdict = "High confidence" if conf >= .7 else "Moderate confidence" if conf >= .4 else "Low confidence - try a clearer, front-facing photo"
        a, b = st.columns([1, 1.4], gap="large")
        with a:
            st.image(data, use_container_width=True)
        with b:
            html(f"<div class='result'>{ring(conf)}<div><div class='sub'>Best match</div><div class='nm'>{pretty(best)}</div><div class='sub'>{verdict}</div></div></div>")
            html("<div class='card'><h4>Other possibilities</h4>" + "".join(bar(pretty(n), q * 100, f"{q*100:.1f}%") for n, q in top[1:]) + "</div>")
        ex, gr, food, tips = care_plan(p)
        html(f"<div class='kpis'><div class='kpi'><span>Size</span><div>{p['size']} · {p['weight']}</div></div>"
             f"<div class='kpi'><span>Lifespan</span><div>{p['life']}</div></div>"
             f"<div class='kpi'><span>Temperament</span><div style='font-size:.95rem'>{p['temper']}</div></div></div>")
        st.markdown("")
        t1, t2, t3 = st.tabs(["Breed profile", "Care guide", "About the breed"])
        with t1:
            x, y = st.columns(2, gap="large")
            with x:
                html("<div class='card'><h4>Personality</h4>" + trait_row("Energy", p["energy"]) + trait_row("Trainability", p["train"]) + trait_row("Grooming needs", p["grooming"]) + "</div>")
            with y:
                html("<div class='card'><h4>Lifestyle</h4>" + trait_row("Good with kids", p["kids"]) + trait_row("Apartment friendly", p["apt"]) + "</div>")
            if not p["curated"]:
                st.caption("Traits for this breed are neutral estimates. See the Wikipedia summary for specifics.")
        with t2:
            html(f"<div class='kpis'><div class='kpi'><span>Daily exercise</span><div>{ex}</div></div><div class='kpi'><span>Grooming</span><div style='font-size:.95rem'>{gr}</div></div><div class='kpi'><span>Food per day</span><div>{food}</div></div></div>")
            st.markdown("")
            html("<div class='card'><h4>Good to know</h4>" + "".join(f"<p style='margin:.4rem 0'>• {t}</p>" for t in tips) + "</div>")
        with t3:
            html(f"<div class='card'><p style='margin:0;line-height:1.65'>{wiki_summary(best)}</p></div>")
        st.info("Ready to give this dog an identity? Open the **Register** tab. Your photo and breed are already filled in.")

# ================= Register =================
with tab_reg:
    st.markdown("### Register a dog")
    last = st.session_state["last"]
    breed_opts = list(NAMES)
    default_idx = breed_opts.index(pretty(last["breed"])) if last and pretty(last["breed"]) in NAMES else 0
    with st.form("register"):
        a, b = st.columns(2, gap="large")
        name = a.text_input("Dog's name")
        breed = a.selectbox("Breed", breed_opts, index=default_idx)
        sex = a.radio("Sex", ["Female", "Male", "Unknown"], horizontal=True)
        dob = a.date_input("Date of birth (optional)", value=None, min_value=dt.date(1995, 1, 1), max_value=dt.date.today())
        color = a.text_input("Colour and markings")
        owner = b.text_input("Owner name")
        contact = b.text_input("Owner contact (phone or email)", help="Only shown publicly if you mark the dog as Lost.")
        chip = b.text_input("Microchip number (optional)")
        pin = b.text_input("Create an owner PIN (4+ digits)", type="password", help="Needed to add photos, transfer ownership or change status.")
        files = st.file_uploader("Photos (1 to 5; clear and front-facing works best)", type=IMG, accept_multiple_files=True)
        use_last = st.checkbox("Use the photo from the Identify tab", value=True) if last else False
        notes = st.text_area("Notes", height=70)
        allow = st.checkbox("Register even if look-alike dogs already exist")
        go = st.form_submit_button("Register dog")
    if go:
        raws = [f.getvalue() for f in (files or [])][:5] + ([last["bytes"]] if use_last and last else [])
        if not (name.strip() and owner.strip() and contact.strip()):
            st.error("Name, owner and contact are required.")
        elif len(pin) < 4:
            st.error("Choose a PIN with at least 4 characters.")
        elif not raws:
            st.error("Add at least one photo.")
        elif reg.microchip_taken(chip.strip()):
            st.error("That microchip number is already registered.")
        else:
            with st.spinner("Analysing photos..."):
                shots = [(r, analyze(r)[1]) for r in raws]
            dupes = [m for _, e in shots for m in reg.find_similar(e, top=1) if m["sim"] >= SIM_HIGH]
            if dupes and not allow:
                st.warning("Very similar dogs are already registered. If this is a different dog, tick the box above and submit again.")
                match_rows(dupes[:3])
            else:
                info = dict(name=name.strip(), breed=NAMES[breed], sex=sex, dob=dob.isoformat() if dob else None,
                            color=color.strip(), microchip=chip.strip() or None, owner=owner.strip(),
                            contact=contact.strip(), notes=notes.strip())
                dog_id = reg.add_dog(info, pin, shots)
                st.session_state["sel_dog"] = f"{info['name']} · {dog_id}"
                st.success(f"{info['name']} is registered as {dog_id}. Open the Registry tab to view the profile and ID card. Keep your PIN safe.")
                st.balloons()

# ================= Registry =================
with tab_dogs:
    dogs = reg.list_dogs()
    if not dogs:
        st.info("No dogs registered yet. Use the Register tab to create the first digital identity.")
    else:
        labels = {f"{d['name']} · {d['id']}": d["id"] for d in dogs}
        if st.session_state.get("sel_dog") not in labels:
            st.session_state["sel_dog"] = next(iter(labels))
        sel = st.selectbox("Select a dog", list(labels), key="sel_dog")
        d = reg.get_dog(labels[sel])
        shots = reg.photos(d["id"])
        p = profile(d["breed"])
        t_prof, t_card, t_hist, t_manage, t_like = st.tabs(["Profile", "ID card", "History & ownership", "Manage", "Look-alikes"])
        with t_prof:
            a, b = st.columns([1, 1.5], gap="large")
            with a:
                if shots:
                    st.image(
                        reg.photo_data(shots[0]),
                        use_container_width=True
                    )

                    if len(shots) > 1:
                        st.image(
                            [reg.photo_data(s) for s in shots[1:]],
                            width=80
                        )
                else:
                    st.info("No photos registered for this dog.")
            with b:
                html(f"<div class='card'><span class='idno'>{d['id']}</span> <span class='st {d['status']}'>{d['status']}</span>"
                     f"<div class='nm disp' style='font-family:Sora;font-weight:800;font-size:2rem;margin:.3rem 0'>{d['name']}</div>"
                     f"{chips([pretty(d['breed']), d['sex'], age_text(d['dob']) or 'Age unknown', d['color'] or 'Colour n/a'])}"
                     f"<p class='mute' style='margin:.6rem 0 0'>Owner: <b>{d['owner_name']}</b> · Registered {d['created'][:10]}"
                     + (f" · Microchip {d['microchip']}" if d["microchip"] else "") + "</p>"
                     + (f"<p style='margin:.6rem 0 0'>{d['notes']}</p>" if d["notes"] else "")
                     + (f"<p style='margin:.6rem 0 0'><b>Lost dog contact:</b> {d['owner_contact']}</p>" if d["status"] == "Lost" else "") + "</div>")
                html("<div class='card'><h4>Breed traits</h4>" + trait_row("Energy", p["energy"]) + trait_row("Grooming needs", p["grooming"]) + trait_row("Trainability", p["train"]) + trait_row("Good with kids", p["kids"]) + "</div>")
        with t_card:
            show_owner = st.toggle(
                    "Show owner name on the card",
                    value=False,
                    key=f"show_owner_{d['id']}"
                )

            if not shots:
                st.warning(
                    "No photos available. "
                    "Please upload a replacement under Manage → Add a photo."
                )

            else:
                photo_bytes = reg.photo_data(shots[0])

                png = make_card(
                    {**dict(d), "breed": pretty(d["breed"])},
                    photo_bytes,
                    show_owner,
                    age_text(d["dob"])
                )

                # Display the card exactly once.
                st.image(
                    png,
                    caption="DogID Digital Identity Card",
                    use_container_width=True
                )

                st.download_button(
                    "Download ID card (PNG)",
                    data=png,
                    file_name=f"{d['id']}.png",
                    mime="image/png",
                    key=f"download_id_card_{d['id']}"
                )

                st.code(
                    f"DogID {d['id']}: {d['name']}, "
                    f"{pretty(d['breed'])}. Verify with the DogID registry.",
                    language=None
                )

                st.caption(
                    "Cards hide the owner's contact details. "
                    "Share the PNG or the text above."
                )
        with t_hist:
            x, y = st.columns(2, gap="large")
            with x:
                st.markdown("#### Profile history")
                html(timeline(reg.history(d["id"])))
            with y:
                st.markdown("#### Ownership")
                html("<div class='card'>" + "".join(
                    f"<div class='trait'><span><b>{o['name']}</b><br><small class='mute'>{o['since'][:10]} to {o['until'][:10] if o['until'] else 'present'}</small></span>"
                    f"<span class='st'>{'Current' if not o['until'] else 'Former'}</span></div>" for o in reg.owners(d["id"])) + "</div>")
        with t_manage:
            st.caption("Changes require the owner PIN created at registration.")
            mpin = st.text_input("Owner PIN", type="password", key="mpin")
            ok = lambda: bool(mpin) and reg.verify_pin(d["id"], mpin) or (st.error("Incorrect PIN.") and False)
            with st.expander("Add a photo"):
                newph = st.file_uploader("New photo", type=IMG, key="newph")
                if st.button("Save photo") and newph and ok():
                    raw = newph.getvalue()
                    reg.save_photo(d["id"], raw, analyze(raw)[1])
                    reg.log(d["id"], "Photo added", "A new photo was added to the profile")
                    st.success("Photo added."); st.rerun()
            with st.expander("Change status"):
                ns = st.radio("Status", ["Registered", "Lost", "Found"], index=["Registered", "Lost", "Found"].index(d["status"]), horizontal=True)
                if st.button("Update status") and ok():
                    reg.set_status(d["id"], ns); st.rerun()
            with st.expander("Transfer ownership"):
                tn = st.text_input("New owner name")
                tc = st.text_input("New owner contact")
                tp = st.text_input("New owner PIN (4+ characters)", type="password")
                if st.button("Transfer ownership") and ok():
                    if tn.strip() and tc.strip() and len(tp) >= 4:
                        reg.transfer(d["id"], tn.strip(), tc.strip(), tp)
                        st.success("Ownership transferred."); st.rerun()
                    else:
                        st.error("Enter the new owner's name, contact and a PIN of 4+ characters.")
        with t_like:
            st.caption(
                "Other registered dogs that look similar to this dog's main photo."
            )

            if shots:
                emb = np.frombuffer(
                    shots[0]["emb"],
                    dtype="float32"
                )

                matches = reg.find_similar(
                    emb,
                    exclude=d["id"]
                )

                match_rows(matches)

            else:
                st.info(
                    "No photo available for similarity matching."
                )
# ================= Find a dog =================
with tab_find:
    st.markdown("### Found a dog? Compare it with the registry")
    lost = [x for x in reg.list_dogs() if x["status"] == "Lost"]
    if lost:
        html(f"<div class='card'><h4>{len(lost)} dog(s) currently marked as lost</h4>" + chips([f"{x['name']} · {x['id']}" for x in lost]) + "</div>")
    fsrc = st.radio("Photo source", ["Upload", "Camera"], horizontal=True, key="fsrc")
    ffile = st.file_uploader("Upload a photo", type=IMG, key="ffile") if fsrc == "Upload" else st.camera_input("Take a picture", key="fcam")
    same = st.checkbox("Only show dogs of the same predicted breed")
    if ffile:
        raw = ffile.getvalue()
        with st.spinner("Searching the registry..."):
            top, emb = analyze(raw)
            res = reg.find_similar(emb, breed=top[0][0] if same else None)
        st.image(raw, width=180, caption=f"Predicted breed: {pretty(top[0][0])} ({top[0][1]*100:.0f}%)")
        match_rows(res)
        st.caption("Similarity measures visual resemblance, not identity. Always confirm with a microchip scan or the owner.")

# ================= Lifestyle =================
with tab_fit:
    st.markdown("### Which breed fits your life?")
    with st.form("lifestyle"):
        a, b = st.columns(2, gap="large")
        home = a.radio("Where do you live?", ["Apartment", "House"], horizontal=True)
        yard = a.checkbox("I have a fenced yard", value=True)
        kids = a.radio("Children at home?", ["No", "Yes"], horizontal=True) == "Yes"
        hours = b.slider("Daily exercise time (hours)", 0.5, 3.0, 1.0, 0.5)
        lowmaint = b.slider("Preference for low-maintenance coats", 1, 5, 3, help="1 = grooming is fine, 5 = as little as possible")
        exp = b.select_slider("Dog-owning experience", ["Beginner", "Some experience", "Experienced"])
        go = st.form_submit_button("Find my matches")
    if go:
        ans = dict(home=home, yard=yard, kids=kids, hours=hours, lowmaint=lowmaint, exp=exp)
        ranked = sorted(((*compat_score(dict(zip(FIELDS, v)), ans), k, dict(zip(FIELDS, v))) for k, v in DB.items()), key=lambda r: r[0], reverse=True)[:5]
        for i, (s, parts, k, p) in enumerate(ranked, 1):
            html(f"<div class='match'><div class='rk'>{i}</div><div class='mt'><b>{k.title()}</b><div>{chips([p['size'], p['life'], p['temper'].split(',')[0]])}</div></div>{ring(s/100, 'sm')}</div>")
            with st.expander("Why this score"):
                html("".join(bar(n, v * 100) for n, v in parts.items()))
        st.caption(f"Scored across {len(DB)} breeds with curated profiles. A guide, not a guarantee.")

# ================= Compare =================
with tab_cmp:
    st.markdown("### Compare breeds side by side")
    pre = [n for n in NAMES if norm(NAMES[n]) in ("golden retriever", "pug")][:2]
    pick = st.multiselect("Choose 2 to 4 breeds", list(NAMES), default=pre, max_selections=4)
    if len(pick) >= 2:
        P = [profile(NAMES[n]) for n in pick]
        row = lambda label, fn: f"<tr><td>{label}</td>" + "".join(f"<td>{fn(p)}</td>" for p in P) + "</tr>"
        html("<div class='cmpwrap'><table class='cmp'><tr><th></th>" + "".join(f"<th>{n}</th>" for n in pick) + "</tr>"
             + row("Size", lambda p: p["size"]) + row("Weight", lambda p: p["weight"]) + row("Lifespan", lambda p: p["life"])
             + row("Energy", lambda p: meter(p["energy"])) + row("Grooming", lambda p: meter(p["grooming"]))
             + row("Trainability", lambda p: meter(p["train"])) + row("Good with kids", lambda p: meter(p["kids"]))
             + row("Apartment friendly", lambda p: meter(p["apt"])) + row("Temperament", lambda p: p["temper"]) + "</table></div>")
        st.caption("More filled bars means more of that trait. Uncurated breeds show neutral estimates.")
    else:
        st.info("Pick at least two breeds to compare.")

# ================= About =================
with tab_about:
    html("<div class='card'><h4>How DogID works</h4><p>An InceptionV3 model fine-tuned on 120 breeds predicts the breed and also produces a visual fingerprint "
         "of each photo. Registered dogs keep their photos and fingerprints in a local SQLite registry; new photos are compared by cosine similarity.</p>"
         "<h4>What matching can and cannot do</h4><p>The model was trained to tell breeds apart, not individual dogs. Matching is a visual-resemblance aid for finding "
         "candidates, and look-alikes of the same breed can score highly. Confirm identity with a microchip scan or the owner.</p>"
         "<h4>Privacy</h4><p>ID cards never show contact details. Contact is shown only while a dog is marked Lost. PINs are stored salted and hashed.</p>"
         "<h4>Note</h4><p>Care guidance is general information, not veterinary advice.</p></div>")

html("<div class='foot'>DogID · Built by Birhan Tamiru</div>")