import json
import os
import random
import secrets
from collections import defaultdict
from functools import wraps

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DATA_FILE = os.path.join(DATA_DIR, "tossen.json")
WACHTWOORD_FILE = os.path.join(DATA_DIR, "wachtwoord.txt")


def leeg_toernooi():
    return {
        "deelnemers": [],
        "volgende_id": 1,
        "instellingen": {"aantal_rondes": 5, "banen_per_ronde": 3},
        "rondes": {},
    }


def laad_data():
    if not os.path.exists(DATA_FILE):
        return leeg_toernooi()
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


def sla_op(data):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def deelnemer_op_id(data, did):
    for d in data["deelnemers"]:
        if d["id"] == did:
            return d
    return None


def namen(data, ids):
    return [deelnemer_op_id(data, i)["naam"] for i in ids if deelnemer_op_id(data, i)]


def rondes_ingepland(data):
    telling = defaultdict(int)
    for ronde in data["rondes"].values():
        for w in ronde.get("wedstrijden", []):
            for speler_id in w["team1"] + w["team2"]:
                telling[speler_id] += 1
    return telling


def team_sterkte(data, ids):
    return sum(deelnemer_op_id(data, i)["niveau"] for i in ids)


def maak_teams(data, kandidaten, historie):
    mannen = [d for d in kandidaten if d["geslacht"] == "M"]
    vrouwen = [d for d in kandidaten if d["geslacht"] == "V"]
    random.shuffle(mannen)
    random.shuffle(vrouwen)
    teams = []
    # gemengde teams waar mogelijk
    while mannen and vrouwen:
        teams.append([mannen.pop()["id"], vrouwen.pop()["id"]])
    # rest: zelfde geslacht samen
    for pool in (mannen, vrouwen):
        while len(pool) >= 2:
            teams.append([pool.pop()["id"], pool.pop()["id"]])
    return teams


def vind_match(data, ronde_nr):
    return data["rondes"].get(str(ronde_nr))


def valideer_ronde_wedstrijden(data, wedstrijden):
    gezien = set()
    for w in wedstrijden:
        ids = w["team1"] + w["team2"]
        for sid in ids:
            if deelnemer_op_id(data, sid) is None:
                return f"Onbekende deelnemer (id {sid})."
            if sid in gezien:
                naam = deelnemer_op_id(data, sid)["naam"]
                return f"'{naam}' staat twee keer in deze ronde."
            gezien.add(sid)
    return None


def lees_wachtwoord():
    if not os.path.exists(WACHTWOORD_FILE):
        return None
    with open(WACHTWOORD_FILE, encoding="utf-8") as f:
        return f.read().strip()


def stel_wachtwoord_in(nw):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(WACHTWOORD_FILE, "w", encoding="utf-8") as f:
        f.write(nw)


def ingesteld_wachtwoord():
    return lees_wachtwoord() is not None


def ingelogd():
    return bool(session.get("ingelogd"))


def login_verplicht(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if ingesteld_wachtwoord() and not ingelogd():
            return redirect(url_for("login"))
        return fn(*args, **kwargs)

    return wrapper


@app.before_request
def bescherm_alles():
    open_endpoints = {"login", "static"}
    if request.endpoint in open_endpoints:
        return None
    if ingesteld_wachtwoord() and not ingelogd() and request.endpoint != "static":
        return redirect(url_for("login"))
    return None


@app.route("/login", methods=["GET", "POST"])
def login():
    wachtwoord = lees_wachtwoord()
    if wachtwoord is None:
        return redirect(url_for("index"))
    if request.method == "POST":
        opgegeven = request.form.get("wachtwoord", "")
        if secrets.compare_digest(opgegeven, wachtwoord):
            session["ingelogd"] = True
            session.permanent = True
            flash("Welkom!")
            return redirect(url_for("index"))
        flash("Verkeerd wachtwoord.")
    return render_template("login.html")


@app.route("/uitloggen")
def uitloggen():
    session.clear()
    flash("Je bent uitgelogd.")
    return redirect(url_for("login"))


@app.route("/wachtwoord", methods=["GET", "POST"])
@login_verplicht
def wachtwoord_instellen():
    if request.method == "POST":
        actie = request.form.get("actie")
        huidig = lees_wachtwoord()
        if actie == "instellen":
            nw = request.form.get("nieuw", "").strip()
            if len(nw) < 4:
                flash("Gebruik minimaal 4 tekens.")
            else:
                stel_wachtwoord_in(nw)
                flash("Wachtwoord opgeslagen.")
                return redirect(url_for("index"))
        elif actie == "wijzigen":
            oud = request.form.get("huidig", "")
            nw = request.form.get("nieuw", "").strip()
            if not secrets.compare_digest(oud, huidig or ""):
                flash("Huidige wachtwoord klopt niet.")
            elif len(nw) < 4:
                flash("Gebruik minimaal 4 tekens.")
            else:
                stel_wachtwoord_in(nw)
                flash("Wachtwoord gewijzigd.")
                return redirect(url_for("index"))
    return render_template(
        "wachtwoord.html", heeft_wachtwoord=lees_wachtwoord() is not None
    )


@app.context_processor
def injecteer_helpers():
    return {
        "namen": namen,
        "heeft_wachtwoord": ingesteld_wachtwoord(),
        "ingelogd": ingelogd,
    }


@app.route("/")
def index():
    data = laad_data()
    telling = rondes_ingepland(data)
    instellingen = data["instellingen"]
    ronde_info = []
    for nr in range(1, instellingen["aantal_rondes"] + 1):
        ronde = vind_match(data, nr)
        ronde_info.append(
            {
                "nr": nr,
                "status": ronde["status"] if ronde else "leeg",
                "aantal_wedstrijden": len(ronde["wedstrijden"]) if ronde else 0,
            }
        )
    return render_template(
        "index.html",
        data=data,
        telling=telling,
        ronde_info=ronde_info,
    )


@app.route("/deelnemers", methods=["GET", "POST"])
def deelnemers():
    data = laad_data()
    if request.method == "POST":
        actie = request.form.get("actie")
        if actie == "toevoegen":
            naam = request.form.get("naam", "").strip()
            geslacht = request.form.get("geslacht")
            niveau = request.form.get("niveau", type=int)
            if not naam:
                flash("Vul een naam in.")
            elif geslacht not in ("M", "V"):
                flash("Kies man of vrouw.")
            elif niveau not in (1, 2, 3):
                flash("Kies een speelsterkte (1, 2 of 3).")
            else:
                data["deelnemers"].append(
                    {
                        "id": data["volgende_id"],
                        "naam": naam,
                        "geslacht": geslacht,
                        "niveau": niveau,
                        "actief": True,
                    }
                )
                data["volgende_id"] += 1
                sla_op(data)
                flash(f"'{naam}' toegevoegd.")
        elif actie == "verwijder":
            did = request.form.get("id", type=int)
            data["deelnemers"] = [d for d in data["deelnemers"] if d["id"] != did]
            for ronde in data["rondes"].values():
                ronde["wedstrijden"] = [
                    w
                    for w in ronde.get("wedstrijden", [])
                    if did not in w["team1"] + w["team2"]
                ]
            sla_op(data)
            flash("Deelnemer verwijderd.")
        elif actie == "toggle_actief":
            did = request.form.get("id", type=int)
            d = deelnemer_op_id(data, did)
            if d:
                d["actief"] = not d["actief"]
                sla_op(data)
        elif actie == "niveau":
            did = request.form.get("id", type=int)
            niveau = request.form.get("niveau", type=int)
            d = deelnemer_op_id(data, did)
            if d and niveau in (1, 2, 3):
                d["niveau"] = niveau
                sla_op(data)
        return redirect(url_for("deelnemers"))
    telling = rondes_ingepland(data)
    return render_template("deelnemers.html", data=data, telling=telling)


@app.route("/instellingen", methods=["GET", "POST"])
def instellingen():
    data = laad_data()
    if request.method == "POST":
        rondes = request.form.get("aantal_rondes", type=int)
        banen = request.form.get("banen_per_ronde", type=int)
        if rondes and rondes > 0 and rondes <= 30:
            data["instellingen"]["aantal_rondes"] = rondes
        if banen and banen > 0 and banen <= 20:
            data["instellingen"]["banen_per_ronde"] = banen
        sla_op(data)
        flash("Instellingen opgeslagen.")
        return redirect(url_for("instellingen"))
    return render_template("instellingen.html", data=data)


@app.route("/ronde/<int:ronde_nr>")
def ronde_detail(ronde_nr):
    data = laad_data()
    ronde = vind_match(data, ronde_nr)
    if ronde_nr < 1 or ronde_nr > data["instellingen"]["aantal_rondes"]:
        flash("Die ronde bestaat niet.")
        return redirect(url_for("index"))
    telling = rondes_ingepland(data)
    return render_template(
        "ronde.html",
        data=data,
        ronde=ronde,
        ronde_nr=ronde_nr,
        telling=telling,
    )


@app.route("/ronde/<int:ronde_nr>/indelen", methods=["POST"])
def ronde_indelen(ronde_nr):
    data = laad_data()
    ronde = vind_match(data, ronde_nr)
    if ronde and ronde["status"] == "gespeeld":
        flash("Deze ronde is geblokkeerd en kan niet opnieuw worden ingedeeld.")
        return redirect(url_for("ronde_detail", ronde_nr=ronde_nr))
    banen = data["instellingen"]["banen_per_ronde"]
    telling = rondes_ingepland(data)
    actief = [d for d in data["deelnemers"] if d["actief"]]
    # weinigste keer ingedeeld eerst; bij gelijkspel lager niveau eerst
    kandidaten = sorted(actief, key=lambda d: (telling[d["id"]], d["niveau"], d["id"]))
    if len(kandidaten) < 4:
        flash("Er zijn minimaal 4 actieve deelnemers nodig om in te delen.")
        return redirect(url_for("ronde_detail", ronde_nr=ronde_nr))
    max_banen = min(banen, len(kandidaten) // 4)
    if max_banen == 0:
        flash("Te weinig actieve deelnemers voor minimaal één baan (4 spelers).")
        return redirect(url_for("ronde_detail", ronde_nr=ronde_nr))
    geselecteerd = kandidaten[: max_banen * 4]
    teams = maak_teams(data, geselecteerd, telling)
    # eerlijke wedstrijden: teams op totaal sterkte sorteren en naast elkaar koppelen
    teams.sort(key=lambda t: team_sterkte(data, t))
    wedstrijden = []
    for i in range(0, len(teams) - 1, 2):
        wedstrijden.append(
            {
                "baan": len(wedstrijden) + 1,
                "team1": teams[i],
                "team2": teams[i + 1],
                "score": [None, None],
            }
        )
    fout = valideer_ronde_wedstrijden(data, wedstrijden)
    if fout:
        flash(f"Indelen mislukt: {fout}")
    else:
        data["rondes"][str(ronde_nr)] = {"status": "open", "wedstrijden": wedstrijden}
        sla_op(data)
        flash(f"Ronde {ronde_nr} is automatisch ingedeeld ({len(wedstrijden)} baan/banen).")
    return redirect(url_for("ronde_detail", ronde_nr=ronde_nr))


@app.route("/ronde/<int:ronde_nr>/handmatig", methods=["POST"])
def ronde_handmatig(ronde_nr):
    data = laad_data()
    ronde = vind_match(data, ronde_nr)
    if not ronde:
        flash("Deze ronde is nog niet ingedeeld.")
        return redirect(url_for("ronde_detail", ronde_nr=ronde_nr))
    if ronde["status"] == "gespeeld":
        flash("Deze ronde is geblokkeerd.")
        return redirect(url_for("ronde_detail", ronde_nr=ronde_nr))
    wedstrijden = []
    idx = 0
    while f"w{idx}_team1_speler1" in request.form:
        team1 = [
            request.form.get(f"w{idx}_team1_speler1", type=int),
            request.form.get(f"w{idx}_team1_speler2", type=int),
        ]
        team2 = [
            request.form.get(f"w{idx}_team2_speler1", type=int),
            request.form.get(f"w{idx}_team2_speler2", type=int),
        ]
        oud = ronde["wedstrijden"][idx]
        wedstrijden.append(
            {
                "baan": idx + 1,
                "team1": [i for i in team1 if i],
                "team2": [i for i in team2 if i],
                "score": oud["score"] if idx < len(ronde["wedstrijden"]) else [None, None],
            }
        )
        idx += 1
    for w in wedstrijden:
        if len(w["team1"]) != 2 or len(w["team2"]) != 2:
            flash("Elk team moet uit 2 spelers bestaan.")
            return redirect(url_for("ronde_detail", ronde_nr=ronde_nr))
    fout = valideer_ronde_wedstrijden(data, wedstrijden)
    if fout:
        flash(f"Aanpassing mislukt: {fout}")
    else:
        for i, w in enumerate(wedstrijden):
            w["baan"] = ronde["wedstrijden"][i]["baan"]
        ronde["wedstrijden"] = wedstrijden
        sla_op(data)
        flash("Indeling aangepast.")
    return redirect(url_for("ronde_detail", ronde_nr=ronde_nr))


@app.route("/ronde/<int:ronde_nr>/score", methods=["POST"])
def ronde_score(ronde_nr):
    data = laad_data()
    ronde = vind_match(data, ronde_nr)
    if not ronde:
        flash("Deze ronde is nog niet ingedeeld.")
        return redirect(url_for("ronde_detail", ronde_nr=ronde_nr))
    if ronde["status"] == "gespeeld":
        flash("Deze ronde is geblokkeerd.")
        return redirect(url_for("ronde_detail", ronde_nr=ronde_nr))
    for w in ronde["wedstrijden"]:
        s1 = request.form.get(f"score_{w['baan']}_1")
        s2 = request.form.get(f"score_{w['baan']}_2")
        w["score"] = [
            int(s1) if s1 not in (None, "") else None,
            int(s2) if s2 not in (None, "") else None,
        ]
    sla_op(data)
    flash("Stand opgeslagen.")
    return redirect(url_for("ronde_detail", ronde_nr=ronde_nr))


@app.route("/ronde/<int:ronde_nr>/blokkeer", methods=["POST"])
def ronde_blokkeer(ronde_nr):
    data = laad_data()
    ronde = vind_match(data, ronde_nr)
    if ronde:
        ronde["status"] = "gespeeld" if ronde["status"] == "open" else "open"
        sla_op(data)
        if ronde["status"] == "gespeeld":
            flash(f"Ronde {ronde_nr} is geblokkeerd (gespeeld).")
        else:
            flash(f"Ronde {ronde_nr} is weer geopend.")
    return redirect(url_for("ronde_detail", ronde_nr=ronde_nr))


@app.route("/ronde/<int:ronde_nr>/wis", methods=["POST"])
def ronde_wis(ronde_nr):
    data = laad_data()
    ronde = vind_match(data, ronde_nr)
    if ronde and ronde["status"] == "gespeeld":
        flash("Deze ronde is geblokkeerd; deblokkeer hem eerst.")
        return redirect(url_for("ronde_detail", ronde_nr=ronde_nr))
    if str(ronde_nr) in data["rondes"]:
        del data["rondes"][str(ronde_nr)]
        sla_op(data)
        flash(f"Indeling van ronde {ronde_nr} gewist.")
    return redirect(url_for("ronde_detail", ronde_nr=ronde_nr))


@app.route("/ronde/<int:ronde_nr>/print")
def ronde_print(ronde_nr):
    data = laad_data()
    ronde = vind_match(data, ronde_nr)
    if not ronde:
        flash("Deze ronde is nog niet ingedeeld.")
        return redirect(url_for("ronde_detail", ronde_nr=ronde_nr))
    return render_template("print.html", data=data, ronde=ronde, ronde_nr=ronde_nr)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=bool(os.environ.get("DEBUG")))
