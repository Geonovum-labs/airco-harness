#!/usr/bin/env python3
"""bk.py — de enige ingang van de skill geonovum-uml2-nl-sbb.

Draai alles vanuit de werkmap (de map waarin project.yaml komt):

    python3 SKILL/scripts/bk.py status          # zegt ALTIJD wat de volgende stap is
    python3 SKILL/scripts/bk.py help            # alle commando's

Vaste mappen in de werkmap: werk/ (tussenbestanden), uit/ (kader), reports/ (validatie,
rapport), review/ (reviewdelen), matches/ (matchdelen). Een .venv in de werkmap wordt
automatisch gebruikt.
"""
import difflib
import glob
import hashlib
import json
import os
import re
import subprocess
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HIER)
WM = os.getcwd()
VENV_PY = os.path.join(WM, ".venv", "bin", "python")


def _deps_ok():
    try:
        import lxml, pyshacl, rdflib, yaml  # noqa: F401
        return True
    except ImportError:
        return False


# Automatisch de .venv van de werkmap gebruiken.
if (len(sys.argv) < 2 or sys.argv[1] != "setup") and not _deps_ok():
    if os.path.exists(VENV_PY) and os.path.realpath(sys.prefix) != os.path.realpath(os.path.join(WM, ".venv")):
        os.execv(VENV_PY, [VENV_PY] + sys.argv)
    if len(sys.argv) > 1 and sys.argv[1] not in ("help", "-h", "--help"):
        sys.exit("Python-pakketten ontbreken. VOLGENDE STAP: python3 " + os.path.join(HIER, "bk.py") + " setup")

P = lambda *d: os.path.join(WM, *d)  # noqa: E731
INV, PROJECT, KADER = P("werk", "inventaris.json"), P("project.yaml"), P("uit", "kader.ttl")
TERMEN, SHACL, STATUS = P("uit", "termen.tsv"), P("reports", "shacl-samenvatting.txt"), P("werk", "status.json")
BESLIS = P("werk", "beslispunten.json")
PER_DEEL = 25
OORDELEN = ["ok", "term", "definitie", "twijfel"]
RELATIES = ["exactMatch", "closeMatch", "broadMatch", "narrowMatch", "relatedMatch", "geen"]


# ---------- hulpfuncties ----------

def run(script, *args, toegestaan=(0,)):
    r = subprocess.run([sys.executable, os.path.join(HIER, script), *map(str, args)])
    if r.returncode not in toegestaan:
        sys.exit(r.returncode)
    return r.returncode


def nieuwer(a, b):
    """True als bestand a bestaat en niet ouder is dan b (of b bestaat niet)."""
    return os.path.exists(a) and (not os.path.exists(b) or os.path.getmtime(a) >= os.path.getmtime(b))


def status_lees():
    return json.load(open(STATUS)) if os.path.exists(STATUS) else {}


def status_schrijf(**kw):
    s = status_lees()
    s.update(kw)
    os.makedirs(P("werk"), exist_ok=True)
    json.dump(s, open(STATUS, "w"), ensure_ascii=False, indent=1)


def yaml_lees(pad):
    import yaml
    return (yaml.safe_load(open(pad, encoding="utf-8")) or {}) if os.path.exists(pad) else {}


def yaml_schrijf(pad, data):
    import yaml
    kop = "# project.yaml — alleen afwijkingen van SKILL/standaardkeuzes.yaml. Wijzig met `bk.py zet` of met de hand;\n" \
          "# controleer daarna met `bk.py controleer`. Uitleg per sleutel: SKILL/references/keuzes.md\n"
    if os.path.exists(pad) and not os.access(pad, os.W_OK):
        os.chmod(pad, 0o644)  # bv. een voorbeeld gekopieerd uit een alleen-lezen installatie
    with open(pad, "w", encoding="utf-8") as f:
        f.write(kop + yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=110))


def standaard():
    return yaml_lees(os.path.join(SKILL, "standaardkeuzes.yaml"))


def aanvullen(doel, nieuw, pad=""):
    """Als samenvoegen, maar bestaande waarden blijven staan. -> lijst van sleutels die al een waarde hadden."""
    behouden = []
    for k, v in nieuw.items():
        if isinstance(v, dict) and isinstance(doel.get(k), dict):
            behouden += aanvullen(doel[k], v, f"{pad}{k}.")
        elif isinstance(v, list) and isinstance(doel.get(k), list) and k in ("mapping", "matches", "notities", "besloten"):
            doel[k] += [x for x in v if x not in doel[k]]
        elif k in doel and doel[k] not in (None, [], {}, "") and doel[k] != v:
            behouden.append(f"{pad}{k}")
        else:
            doel[k] = v
    return behouden


def samenvoegen(doel, nieuw):
    """Diepe merge; bronnen.mapping, matches, notities en besloten worden aangevuld i.p.v. vervangen."""
    for k, v in nieuw.items():
        if isinstance(v, dict) and isinstance(doel.get(k), dict):
            samenvoegen(doel[k], v)
        elif isinstance(v, list) and isinstance(doel.get(k), list) and k in ("mapping", "matches", "notities", "besloten"):
            doel[k] += [x for x in v if x not in doel[k]]
        else:
            doel[k] = v
    return doel


def hash_bestand(pad):
    return hashlib.sha1(open(pad, "rb").read()).hexdigest()[:12]


def volgende(tekst):
    print(f"\nVOLGENDE STAP: {tekst}")


# ---------- setup / start ----------

def cmd_setup(_):
    if not os.path.exists(VENV_PY):
        subprocess.run([sys.executable, "-m", "venv", P(".venv")], check=True)
    subprocess.run([VENV_PY, "-m", "pip", "install", "-q", "-r", os.path.join(SKILL, "requirements.txt")], check=True)
    print("Omgeving klaar (.venv in de werkmap; bk.py gebruikt die vanzelf).")
    volgende("bk.py start <bestand> (XMI, XML, EAP, EAPX, QEA of ZIP)")


def cmd_start(a):
    import argparse
    ap = argparse.ArgumentParser(prog="bk.py start")
    ap.add_argument("bron")
    ap.add_argument("--package", action="append", default=[])
    ap.add_argument("--zonder", action="append", default=[])
    o = ap.parse_args(a)
    bron = os.path.abspath(o.bron)
    if not os.path.exists(bron):
        sys.exit(f"Bestand niet gevonden: {bron}")
    os.makedirs(P("werk"), exist_ok=True)
    if bron.lower().endswith(".zip"):
        import zipfile
        doel = P("werk", "bron")
        with zipfile.ZipFile(bron) as z:
            namen = [n for n in z.namelist() if re.search(r"\.(xmi|xml|eapx?|qeax?)$", n, re.I) and "/." not in n]
            if not namen:
                sys.exit("Geen XMI/EAP-bestand in de zip")
            z.extractall(doel, namen)
        kand = sorted(namen, key=lambda n: (not re.search(r"\.(eapx?|qeax?)$", n, re.I), n))
        bron = os.path.join(doel, kand[0])
        print(f"Uit zip: {kand[0]}" + (f" (ook: {', '.join(kand[1:])})" if kand[1:] else ""))
    ext = os.path.splitext(bron)[1].lower()
    script = "inventaris_eap.py" if ext in (".eap", ".eapx", ".qea", ".qeax") else "inventaris.py"
    args = [bron, INV] + sum((["--package", p] for p in o.package), []) + sum((["--zonder", z] for z in o.zonder), [])
    r = subprocess.run([sys.executable, os.path.join(HIER, script), *args], capture_output=True, text=True)
    out = r.stdout + r.stderr
    if r.returncode != 0 and "Packageboom" in out:
        open(P("werk", "packages.txt"), "w").write(out)
        regels = out.splitlines()
        print("\n".join(regels[:60]) + (f"\n... ({len(regels) - 60} regels meer in werk/packages.txt)" if len(regels) > 60 else ""))
        status_schrijf(bron=bron)
        voorstel = package_voorstel(regels, os.path.basename(o.bron))
        if voorstel:
            print(f"\nVoorstel van het script (op basis van de bestandsnaam): --package {voorstel}")
        volgende("vraag de gebruiker welke package(s) omgezet worden: het informatiemodel waar het bestand over "
                 "gaat (de bestandsnaam is de beste aanwijzing). Ingesloten basismodellen (NEN 3610, GML, ISO, MIM) "
                 "en voorbeeldmodellen laat je weg, tenzij het bestand juist dat model is. Dan: bk.py start <bestand> "
                 "--package <naam> [--package <naam2>] [--zonder <pad/subpackage>]. Bij dubbele namen een pad: Ouder/Kind.")
        return
    print(out.strip())
    if r.returncode != 0:
        sys.exit(r.returncode)
    inv = json.load(open(INV))
    inv["packages"], inv["zonder"] = o.package, o.zonder
    json.dump(inv, open(INV, "w"), ensure_ascii=False, indent=1)
    status_schrijf(bron=bron, packages=o.package, zonder=o.zonder)
    if "LET OP" in out:
        print("\nLET OP-meldingen hierboven: noem ze aan de gebruiker en in het rapport.")
    vb = voorbeeld_voorstel(os.path.basename(o.bron), o.package)
    if vb and not os.path.exists(PROJECT):
        print(f"\nDe skill heeft een ingevuld voorbeeld voor dit model: voorbeelden/{vb}.yaml "
              "(keuzes, termcorrecties, bronnen en matches van een eerdere omzetting).")
        volgende(f"vraag de gebruiker of het voorbeeld gebruikt mag worden; zo ja: bk.py voorbeeld {vb}. "
                 "Anders (of zonder gebruiker: ook gebruiken en als aanname noemen): bk.py analyseer")
        return
    volgende("bk.py analyseer")


def voorbeeld_voorstel(bestandsnaam, packages):
    """Naam van een voorbeeld in SKILL/voorbeelden/ dat bij de bestandsnaam of het gekozen package past."""
    norm = lambda x: re.sub(r"[^0-9a-z]", "", x.lower())  # noqa: E731
    stam = os.path.splitext(bestandsnaam)[0].lower()
    eerste = re.split(r"[^0-9a-z]+", stam)[0]  # IMGeluid_v3_1_1 -> imgeluid, IMEV3.0.2_... -> imev3
    namen = {norm(stam), eerste, re.sub(r"\d+$", "", eerste)} | {norm(p.split("/")[-1]) for p in packages}
    for f in sorted(glob.glob(os.path.join(SKILL, "voorbeelden", "*.yaml"))):
        vb = os.path.splitext(os.path.basename(f))[0]
        if norm(vb) in namen:
            return vb
    return None


def cmd_voorbeeld(a):
    """Kopieert SKILL/voorbeelden/<naam>.yaml naar project.yaml (met schrijfrechten)."""
    namen = sorted(os.path.splitext(os.path.basename(f))[0] for f in glob.glob(os.path.join(SKILL, "voorbeelden", "*.yaml")))
    if not a or a[0] not in namen:
        sys.exit(f"Gebruik: bk.py voorbeeld <naam>; beschikbaar: {', '.join(namen)}")
    if os.path.exists(PROJECT) and "--overschrijf" not in a:
        sys.exit("project.yaml bestaat al. Overschrijven (alle keuzes gaan verloren): bk.py voorbeeld "
                 f"{a[0]} --overschrijf")
    with open(os.path.join(SKILL, "voorbeelden", a[0] + ".yaml"), encoding="utf-8") as f:
        tekst = f.read()
    if os.path.exists(PROJECT):
        os.chmod(PROJECT, 0o644)
    with open(PROJECT, "w", encoding="utf-8") as f:
        f.write(tekst)
    print(f"project.yaml = voorbeelden/{a[0]}.yaml. Controleer kader.titel en kader.omschrijving (versie!) "
          "en noem in het rapport dat de keuzes uit het voorbeeld komen.")
    controleer()
    volgende("bk.py analyseer")


def package_voorstel(regels, bestandsnaam):
    """Package waarvan de naam het langst overeenkomt met het begin van de bestandsnaam (ondiepste bij gelijkspel)."""
    norm = lambda x: re.sub(r"[^0-9a-z]", "", x.lower())  # noqa: E731
    bn = norm(os.path.splitext(bestandsnaam)[0])
    beste = None
    for r in regels:
        if not r.startswith(" ") and not r.startswith("\t") and "(" not in r and r.strip() == r:
            diepte = 0
        else:
            diepte = (len(r) - len(r.lstrip(" "))) // 2
        naam = re.sub(r"\s*\(\d+\)$", "", r.strip())
        n = norm(naam)
        if len(n) >= 3 and bn.startswith(n):
            kand = (len(n), -diepte, naam)
            if beste is None or kand > beste:
                beste = kand
    return beste[2] if beste else None


# ---------- analyse en keuzes ----------

def cmd_analyseer(_):
    if not os.path.exists(INV):
        sys.exit("Eerst: bk.py start <bestand>")
    args = [INV] + ([PROJECT] if os.path.exists(PROJECT) else []) + [P("werk")]
    r = subprocess.run([sys.executable, os.path.join(HIER, "analyseer.py"), *args], capture_output=True, text=True)
    if r.returncode:
        print(r.stdout + r.stderr)
        sys.exit(r.returncode)
    toon_punten()


def punten():
    return json.load(open(BESLIS)) if os.path.exists(BESLIS) else []


def toon_punten():
    pp = punten()
    for i, p in enumerate(pp, 1):
        print(f"{i:2}. [{p['soort']}] {p['code']}: {p['titel'][:150]} ({len(p['details'])} details)")
    open_ = [i for i, p in enumerate(pp, 1) if p["soort"] == "VRAAG"]
    print(f"\n{len(open_)} open VRAAG-punten" + (f": nummers {open_}" if open_ else ""))
    if open_:
        volgende(f"bk.py vraag {open_[0]}  (toont één punt met details en het scriptvoorstel)")
    else:
        volgende("bk.py status")


def cmd_vraag(a):
    if not a:
        sys.exit("Gebruik: bk.py vraag <nummer> [--vanaf N]")
    pp, n = punten(), int(a[0])
    vanaf = int(a[a.index("--vanaf") + 1]) if "--vanaf" in a else 0
    p = pp[n - 1]
    print(f"[{p['soort']}] {p['code']}: {p['titel']}\n")
    det = p["details"]
    for d in det[vanaf:vanaf + 40]:
        print(f"  - {d}")
    if len(det) > vanaf + 40:
        print(f"  ... nog {len(det) - vanaf - 40} details: bk.py vraag {n} --vanaf {vanaf + 40}")
    if p["soort"] != "VRAAG":
        print(f"\n{p['soort']}: hier hoeft niets beslist te worden (alleen noemen aan de gebruiker).")
        return
    if p["voorstel"] is not None:
        import yaml
        print("\nVoorstel van het script (komt zo in project.yaml met `bk.py overnemen " + p["code"] + "`):\n")
        print(yaml.safe_dump(p["voorstel"], allow_unicode=True, sort_keys=False))
    else:
        print("\nGeen scriptvoorstel. Leg het punt voor en zet de keuze met `bk.py zet`.")
    print(f"Wil de gebruiker de standaard houden: bk.py overnemen {p['code']} --standaard")


def cmd_overnemen(a):
    """Neemt scriptvoorstellen over in project.yaml. Codes als argument, of --alle."""
    standaard_houden = "--standaard" in a
    codes = [x for x in a if not x.startswith("--")]
    if not codes and "--alle" not in a:
        sys.exit("Gebruik: bk.py overnemen <code> [<code> ...] | --alle  [--standaard]")
    proj = yaml_lees(PROJECT)
    gedaan = []
    for p in punten():
        if p["soort"] != "VRAAG" or (codes and p["code"] not in codes):
            continue
        if standaard_houden or p["voorstel"] is None:
            samenvoegen(proj, {"besloten": [p["code"]]})
            gedaan.append(f"{p['code']}: standaard gehouden (besloten)")
        else:
            # bestaande keuzes (van de gebruiker of uit een voorbeeld) worden niet overschreven
            behouden = aanvullen(proj, p["voorstel"])
            samenvoegen(proj, {"besloten": [p["code"]],
                               "notities": [f"{p['code']}: scriptvoorstel overgenomen"]})
            gedaan.append(f"{p['code']}: voorstel overgenomen"
                          + (f"; {len(behouden)} bestaande keuze(s) behouden, bv. {behouden[0]}" if behouden else ""))
    if not gedaan:
        sys.exit("Geen open VRAAG-punten met die code(s). Draai eerst bk.py analyseer.")
    yaml_schrijf(PROJECT, proj)
    print("\n".join(gedaan))
    if controleer(stil=True):
        volgende("herstel de FOUT-regels hierboven met bk.py zet")
    else:
        volgende("bk.py analyseer")


def cmd_zet(a):
    """bk.py zet sleutel.pad 'waarde' [--notitie tekst] — waarde is YAML (null, [A, b], tekst)."""
    import yaml
    notitie = None
    if "--notitie" in a:
        i = a.index("--notitie")
        notitie, a = a[i + 1], a[:i] + a[i + 2:]
    if len(a) != 2:
        sys.exit("Gebruik: bk.py zet <sleutel.pad> '<waarde in YAML>' [--notitie '<tekst>']\n"
                 "bv.: bk.py zet termen.vast.Appurtenance 'INSPIRE-leidingelement'\n"
                 "     bk.py zet relaties.gebruik.TypeBak '[Bak, type]'")
    # sleutels met punten of dubbele punten tussen [ ]: termen.vast[Klasse.naam]
    pad = [t[1:-1] if t.startswith("[") else t for t in re.findall(r"\[[^\]]*\]|[^.\[\]]+", a[0])]
    waarde = yaml.safe_load(a[1]) if a[1] != "" else ""
    if isinstance(waarde, dict) and not a[1].lstrip().startswith("{"):
        waarde = a[1]  # 'IMGeo 2.2: begrippen' is tekst met een dubbele punt, geen sectie
    proj = yaml_lees(PROJECT)
    d = proj
    for k in pad[:-1]:
        d = d.setdefault(k, {})
        if not isinstance(d, dict):
            sys.exit(f"'{k}' is geen sectie")
    d[pad[-1]] = waarde
    if notitie:
        samenvoegen(proj, {"notities": [f"{a[0]}: {notitie}"]})
    yaml_schrijf(PROJECT, proj)
    print(f"{a[0]} = {json.dumps(waarde, ensure_ascii=False)}")
    controleer()


# ---------- controle van project.yaml ----------

def controleer(stil=False):
    import yaml
    fouten, waarsch = [], []
    if not os.path.exists(PROJECT):
        fouten.append("project.yaml bestaat niet")
        return fouten
    try:
        proj = yaml.safe_load(open(PROJECT, encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        return [f"project.yaml is geen geldige YAML: {e}"]
    std = standaard()
    for k, v in proj.items():
        if k not in std:
            fouten.append(f"onbekende sleutel '{k}'" + _lijkt(k, std))
            continue
        if isinstance(std[k], dict) and std[k] and k not in ("prefixen",):
            if not isinstance(v, dict):
                fouten.append(f"'{k}' moet een sectie zijn (sleutel: waarde)")
                continue
            for k2 in v:
                if k2 not in std[k]:
                    fouten.append(f"onbekende sleutel '{k}.{k2}'" + _lijkt(k2, std[k]))
    inv = json.load(open(INV)) if os.path.exists(INV) else {"elementen": {}}
    el = inv["elementen"].values()
    klassen = {c["name"] for c in el} | {c.get("alias") for c in el if c.get("alias")}
    attrs = {(c["name"], a["name"]) for c in el for a in c["attrs"]}
    anamen = {a for _, a in attrs}
    cfg = samenvoegen(std, json.loads(json.dumps(proj)))
    k = cfg.get("kader") or {}
    if not str(k.get("uri") or "").startswith("http"):
        fouten.append("kader.uri ontbreekt of begint niet met http")
    for veld in ("titel", "omschrijving"):
        if not k.get(veld):
            waarsch.append(f"kader.{veld} ontbreekt")
    t = cfg["termen"]
    for n in t.get("vast") or {}:
        if inv["elementen"] and n not in klassen and n not in anamen:
            waarsch.append(f"termen.vast: '{n}' komt niet voor als klasse-, attribuut- of waardenaam")
    if not isinstance(t.get("alias_als_voorkeursterm"), list):
        fouten.append("termen.alias_als_voorkeursterm moet een lijst zijn, bv. [\"*\"]")
    for n in cfg["attributen"].get("term_correcties") or {}:
        bestaat = tuple(n.split(".", 1)) in attrs if "." in n else n in anamen
        if inv["elementen"] and not bestaat:
            waarsch.append(f"attributen.term_correcties: attribuut '{n}' bestaat niet")
    w = cfg["waarden"]
    for sl in w.get("splitsingen") or {}:
        if "|" not in sl:
            fouten.append(f"waarden.splitsingen: sleutel '{sl}' moet 'waarde|Waardelijst' zijn")
        elif inv["elementen"] and sl.split("|")[1] not in klassen:
            fouten.append(f"waarden.splitsingen: waardelijst '{sl.split('|')[1]}' bestaat niet")
    if w.get("automatisch_splitsen") and "{waarde}" not in w["automatisch_splitsen"]:
        fouten.append("waarden.automatisch_splitsen moet {waarde} bevatten, bv. \"{lijst} {waarde}\"")
    r = cfg["relaties"]
    for n in ([r["wortel"]] if r.get("wortel") else []) + list(r.get("zelfstandig") or []):
        if inv["elementen"] and n not in klassen:
            fouten.append(f"relaties: klasse '{n}' bestaat niet")
    for lijst, doel in (r.get("gebruik") or {}).items():
        if inv["elementen"] and lijst not in klassen:
            fouten.append(f"relaties.gebruik: waardelijst '{lijst}' bestaat niet")
        if doel is None:
            continue
        if not (isinstance(doel, list) and len(doel) == 2):
            fouten.append(f"relaties.gebruik.{lijst}: moet null of [Klasse, attribuut|null] zijn")
        elif inv["elementen"] and doel[0] not in klassen:
            fouten.append(f"relaties.gebruik.{lijst}: klasse '{doel[0]}' bestaat niet")
        elif inv["elementen"] and doel[1] and (doel[0], doel[1]) not in attrs:
            fouten.append(f"relaties.gebruik.{lijst}: attribuut '{doel[0]}.{doel[1]}' bestaat niet")
    b = cfg["bronnen"]
    if not isinstance(b.get("tag"), (list, str)):
        fouten.append("bronnen.tag moet een lijst van tagnamen zijn")
    for i, m in enumerate(b.get("mapping") or [], 1):
        if not isinstance(m, dict) or not {"patroon", "sleutel", "titel"} <= set(m):
            fouten.append(f"bronnen.mapping regel {i}: nodig zijn patroon, sleutel en titel")
            continue
        try:
            re.compile(m["patroon"])
        except re.error as e:
            fouten.append(f"bronnen.mapping regel {i}: ongeldige regex '{m['patroon']}': {e}")
    for i, m in enumerate(cfg.get("matches") or [], 1):
        if not isinstance(m, dict) or not {"term", "relatie", "uri"} <= set(m):
            fouten.append(f"matches regel {i}: nodig zijn term, relatie en uri")
        elif m["relatie"] not in RELATIES[:-1]:
            fouten.append(f"matches regel {i}: relatie '{m['relatie']}' moet een van {RELATIES[:-1]} zijn")
        elif not str(m["uri"]).startswith("http"):
            fouten.append(f"matches regel {i}: uri moet met http beginnen")
    if not stil or fouten:
        for f in fouten:
            print(f"FOUT: {f}")
        for f in waarsch:
            print(f"waarschuwing: {f}")
        print(f"project.yaml: {len(fouten)} fouten, {len(waarsch)} waarschuwingen")
    return fouten


def _lijkt(k, opties):
    m = difflib.get_close_matches(str(k), [str(o) for o in opties], 1)
    return f" (bedoel je '{m[0]}'?)" if m else ""


def cmd_controleer(_):
    if controleer():
        sys.exit(1)
    volgende("bk.py status")


# ---------- genereren en valideren ----------

def cmd_genereer(_):
    if controleer(stil=True):
        sys.exit("Herstel eerst project.yaml (zie FOUT-regels).")
    rc = run("genereer.py", INV, PROJECT, KADER, toegestaan=(0, 2))
    if rc == 2:
        volgende("open beslissingen hierboven: bk.py analyseer en bk.py vraag <nr> (waarden-splitsen)")
        sys.exit(2)
    volgende("bk.py valideer (kan bij grote modellen 10+ minuten duren; niet afbreken)")


def cmd_valideer(_):
    if not os.path.exists(KADER):
        sys.exit("Eerst: bk.py genereer")
    print("Bezig met SHACL-validatie; dit kan lang duren. Wacht tot het klaar is.", flush=True)
    run("extern.py", "context", KADER, PROJECT, P("werk", "context.ttl"))
    if not (yaml_lees(PROJECT).get("matches")):
        print("(Geen matches in project.yaml: de externe context is leeg en run B is gelijk aan run A. Dat is normaal.)")
    run("valideer.py", KADER, PROJECT, P("reports"), P("werk", "context.ttl"))
    volgende("bk.py review")


# ---------- review in delen ----------

AFK = re.compile(r"\b[A-Z]{2,}\b")


def termen_lezen():
    import csv
    return list(csv.DictReader(open(TERMEN, encoding="utf-8"), delimiter="\t"))


def term_voorstel(t):
    """Voorstel voor een term met leestekens (alleen een hint; het oordeel blijft aan de reviewer).
    'recreatie: camping' -> 'camping'; 'benzine- / olieput' -> 'benzine- of olieput';
    'greppel, droge sloot' -> 'greppel of droge sloot'; 'meer, plas, ven, vijver' -> 'meer, plas, ven of vijver';
    '(haven)kraan' -> 'havenkraan'; 'maatschappelijke en/of publieksvoorziening' -> '... of ...'.
    Geen voorstel bij een verkort tweede deel ('brandkraan / -put'): dat vraagt kennis van het woord."""
    v = t.strip()
    if re.search(r"/\s*-", v):
        return None
    m = re.fullmatch(r"[^:]{2,40}:\s*(.+)", v)
    if m:
        v = m.group(1)
    v = re.sub(r"\((\w+)\)(?=\w)", r"\1", v)        # (haven)kraan -> havenkraan
    v = re.sub(r"\s+en/of\s+", " of ", v)
    v = re.sub(r"\s*/\s*", " of ", v)
    delen = [d.strip() for d in v.split(",")]
    if len(delen) > 1 and all(delen):
        v = ", ".join(delen[:-1]) + " of " + delen[-1]
    return re.sub(r"\s+", " ", v).strip()


def signalen(rijen):
    """Deterministische signalen per term; het oordeel blijft aan de LLM."""
    from collections import Counter
    defs = Counter(re.sub(r"\W+", " ", r["definitie"].lower()).strip() for r in rijen if r["definitie"])
    labs = Counter(r["voorkeursterm"].lower() for r in rijen)
    uit = []
    for r in rijen:
        t, d = r["voorkeursterm"], r["definitie"]
        s = []
        if not d:
            s.append("geen definitie")
        else:
            dk = re.sub(r"\W+", " ", d.lower()).strip()
            if defs[dk] > 1:
                s.append(f"definitie identiek aan {defs[dk] - 1} ander(e) begrip(pen)")
            if len(d.split()) < 4:
                s.append("zeer korte definitie")
            woorden = re.findall(r"\w+", d.lower())
            if re.search(r"\b" + re.escape(t.lower()) + r"\b", " ".join(woorden[:4])) \
                    and len(woorden) <= len(t.split()) + 5:
                s.append("korte definitie die vooral de term herhaalt (circulair?)")
        if labs[t.lower()] > 1:
            s.append("voorkeursterm komt vaker voor")
        if re.search(r"[()\[\]/;:,]", t):
            v = term_voorstel(t)
            s.append("leesteken in term" + (f" (voorstel: '{v}')" if v and v != t else ""))
        if AFK.search(t):
            s.append("afkorting in term")
        if t[:1].isupper() and not AFK.match(t):
            s.append("hoofdletter aan begin van term")
        if re.fullmatch(r"[\d\W]+", t):
            s.append("term is alleen een code/getal")
        uit.append(s)
    return uit


def cmd_review(a):
    if a and a[0] == "klaar":
        return review_klaar()
    if not os.path.exists(TERMEN):
        sys.exit("Eerst: bk.py genereer")
    rijen = termen_lezen()
    sig = signalen(rijen)
    h = hash_bestand(TERMEN)
    idx_pad = P("review", "index.json")
    if os.path.exists(idx_pad) and json.load(open(idx_pad))["hash"] == h and "--opnieuw" not in a:
        print("Reviewdelen bestaan al voor deze termen.tsv (gebruik --opnieuw om ze te overschrijven).")
        return review_voortgang()
    os.makedirs(P("review"), exist_ok=True)
    # eerdere oordelen bewaren: zelfde definitie + zelfde soort (de term kan intussen gecorrigeerd zijn)
    oud = {}
    for f in glob.glob(P("review", "deel-*.md")):
        for i in lees_deel(f):
            if i["oordeel"].strip():
                oud[(i["term"].lower(), i["definitie"])] = (i["oordeel"], i["opmerking"])
                if i["oordeel"].strip().lower() != "term":  # gecorrigeerde term opnieuw beoordelen
                    oud.setdefault(("", i["definitie"], i["soort"]), (i["oordeel"], i["opmerking"]))
        os.remove(f)
    hergebruikt = 0
    delen = []
    for start in range(0, len(rijen), PER_DEEL):
        nr = len(delen) + 1
        naam = f"deel-{nr:03}.md"
        regels = [f"# Review deel {nr} van {(len(rijen) + PER_DEEL - 1) // PER_DEEL} — begrippen {start + 1} t/m "
                  f"{min(start + PER_DEEL, len(rijen))}", "",
                  "Vul bij ELK begrip `oordeel:` in met precies één van: ok | term | definitie | twijfel.",
                  "- ok = term en definitie in orde",
                  "- term = de omzetting van de UML-naam naar de term is fout (verkeerde splitsing, hoofdletter, "
                  "samenstelling); zet bij `opmerking:` de betere term",
                  "- definitie = probleem in de brondefinitie (vaag, circulair, identiek, ontbreekt): advies aan de "
                  "UML-beheerder; NIET herschrijven",
                  "- twijfel = weet niet zeker; leg uit bij `opmerking:`",
                  "Bij alles behalve ok is `opmerking:` verplicht. Verwijder geen regels. Script-signalen zijn "
                  "hints, geen oordeel.", ""]
        for i, (r, s) in enumerate(zip(rijen[start:start + PER_DEEL], sig[start:start + PER_DEEL]), start + 1):
            regels += [f"### {i:04} | {r['voorkeursterm']}",
                       f"soort: {r['soort']} | notatie: {r['notatie'] or '-'} | altLabels: {r['altLabels'] or '-'}",
                       f"id: {r['uri'].rsplit('/', 1)[-1]}",
                       f"definitie: {r['definitie'] or '(geen)'}",
                       f"signalen: {'; '.join(s) if s else '-'}"]
            d0 = r["definitie"] or "(geen)"
            vorig = oud.get((r["voorkeursterm"].lower(), d0)) or (oud.get(("", d0, r["soort"])) if r["definitie"] else None)
            if vorig:
                hergebruikt += 1
                regels += [f"oordeel: {vorig[0]}", f"opmerking: {vorig[1]}", ""]
            else:
                regels += ["oordeel: ", "opmerking: ", ""]
        open(P("review", naam), "w", encoding="utf-8").write("\n".join(regels))
        delen.append(dict(bestand=naam, van=start + 1, tot=min(start + PER_DEEL, len(rijen))))
    json.dump(dict(hash=h, aantal=len(rijen), delen=delen), open(idx_pad, "w"), indent=1)
    print(f"{len(rijen)} begrippen in {len(delen)} delen van max. {PER_DEEL} (review/deel-001.md ...).")
    print(f"Signalen van het script: {sum(1 for s in sig if s)} begrippen met minstens één signaal.")
    if hergebruikt:
        print(f"{hergebruikt} oordelen overgenomen uit de vorige review (zelfde definitie); controleer alleen de rest.")
    review_voortgang()


def lees_deel(pad):
    """-> lijst van dicts per begrip: nr, term, oordeel, opmerking, signalen."""
    uit, cur = [], None
    for regel in open(pad, encoding="utf-8"):
        regel = regel.rstrip("\n")
        if m := re.match(r"^### (\d+) \| (.*)$", regel):
            cur = dict(nr=int(m.group(1)), term=m.group(2).strip(), oordeel="", opmerking="", signalen="",
                       soort="", definitie="", id="")
            uit.append(cur)
        elif cur is not None:
            for veld in ("oordeel", "opmerking", "signalen", "definitie", "id"):
                if regel.lower().startswith(veld + ":"):
                    cur[veld] = regel.split(":", 1)[1].strip()
            if regel.startswith("soort:"):
                cur["soort"] = regel.split("|")[0].split(":", 1)[1].strip()
    return uit


def deel_problemen(pad, van, tot, oordelen=OORDELEN, veld="oordeel"):
    items = lees_deel(pad)
    prob = []
    nrs = [i["nr"] for i in items]
    if nrs != list(range(van, tot + 1)):
        prob.append(f"begrippen ontbreken of zijn verplaatst (verwacht {van}-{tot}, gevonden {len(nrs)})")
    for i in items:
        o = i[veld].strip().strip("`*").lower()
        o = next((x for x in oordelen if x.lower() == o), None)
        if not o:
            prob.append(f"{i['nr']:04} {i['term']}: {veld} leeg of ongeldig ('{i[veld]}')")
        elif o not in ("ok", "geen") and not i["opmerking"]:
            prob.append(f"{i['nr']:04} {i['term']}: opmerking ontbreekt bij '{o}'")
        elif o == "ok" and veld == "oordeel" and i["signalen"] not in ("", "-") and not i["opmerking"]:
            prob.append(f"{i['nr']:04} {i['term']}: 'ok' terwijl het script een signaal geeft; "
                        "leg in opmerking uit waarom het signaal niet terecht is")
    return prob


def cmd_oordeel(a):
    """Oordelen invullen via stdin, één regel per begrip: `0007 term | betere term` of `0008 ok`."""
    map_, veld, toegestaan = ("matches", "relatie", RELATIES) if "--matches" in a else ("review", "oordeel", OORDELEN)
    idx_pad = P(map_, "index.json")
    if not os.path.exists(idx_pad):
        sys.exit(f"Eerst: bk.py {map_}")
    idx = json.load(open(idx_pad))
    invoer = {}
    fout = []
    for regel in sys.stdin.read().splitlines():
        if not regel.strip():
            continue
        m = re.match(r"^\s*(\d+)(?:\s*-\s*(\d+))?\s+(\S+)\s*(?:\|\s*(.*))?$", regel)
        w = m and next((x for x in toegestaan if x.lower() == m.group(3).strip("`*").lower()), None)
        if not w:
            fout.append(f"niet begrepen: '{regel}' (vorm: <nr> <{'|'.join(toegestaan)}> [| opmerking])")
            continue
        van, tot = int(m.group(1)), int(m.group(2) or m.group(1))
        if tot - van >= PER_DEEL:
            fout.append(f"reeks te groot: '{regel}' (hoogstens {PER_DEEL} begrippen, en alleen als je ze allemaal gelezen hebt)")
            continue
        for n in range(van, tot + 1):
            invoer[n] = (w, (m.group(4) or "").strip())
    gezet = 0
    for d in idx["delen"]:
        nrs = [n for n in invoer if d["van"] <= n <= d["tot"]]
        if not nrs:
            continue
        pad = P(map_, d["bestand"])
        regels, cur = open(pad, encoding="utf-8").read().split("\n"), None
        for i, r in enumerate(regels):
            if m := re.match(r"^### (\d+) \|", r):
                cur = int(m.group(1))
            elif cur in invoer and r.lower().startswith(veld + ":"):
                regels[i] = f"{veld}: {invoer[cur][0]}"
                gezet += 1
            elif cur in invoer and r.lower().startswith("opmerking:") and invoer[cur][1]:
                regels[i] = f"opmerking: {invoer[cur][1]}"
        open(pad, "w", encoding="utf-8").write("\n".join(regels))
    for f in fout:
        print(f"FOUT: {f}")
    print(f"{gezet} begrippen ingevuld.")
    review_voortgang(map_, toegestaan, veld, f"bk.py {map_} klaar")


def review_voortgang(map_="review", oordelen=OORDELEN, veld="oordeel", klaar_cmd="bk.py review klaar", stil=False):
    idx_pad = P(map_, "index.json")
    if not os.path.exists(idx_pad):
        return None
    idx = json.load(open(idx_pad))
    open_ = []
    for d in idx["delen"]:
        pr = deel_problemen(P(map_, d["bestand"]), d["van"], d["tot"], oordelen, veld)
        if pr:
            open_.append((d["bestand"], pr))
    klaar = len(idx["delen"]) - len(open_)
    print(f"Voortgang: {klaar} van {len(idx['delen'])} delen volledig ingevuld.")
    if open_:
        bestand, pr = open_[0]
        print(f"Eerstvolgende: {map_}/{bestand} ({len(pr)} punten open, bv. {pr[0]})")
        volgende(f"lees {map_}/{bestand} helemaal en vul elk begrip in met `bk.py oordeel"
                 f"{' --matches' if map_ == 'matches' else ''}` (regels '<nr> <{veld}> | opmerking'). "
                 "Eén deel tegelijk; sla geen deel over.")
    elif not stil:
        volgende(klaar_cmd)
    return open_


def review_klaar():
    open_ = review_voortgang(stil=True)
    if open_ is None:
        sys.exit("Eerst: bk.py review")
    if open_:
        for b, pr in open_[:3]:
            print(f"\n{b}:")
            for x in pr[:10]:
                print(f"  - {x}")
        sys.exit(1)
    idx = json.load(open(P("review", "index.json")))
    alle = [i for d in idx["delen"] for i in lees_deel(P("review", d["bestand"]))]
    for i in alle:
        i["oordeel"] = i["oordeel"].strip().strip("`*").lower()
    import csv
    with open(P("reports", "review.tsv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["nr", "id", "term", "soort", "oordeel", "opmerking", "signalen"])
        for i in alle:
            w.writerow([i["nr"], i["id"], i["term"], i["soort"], i["oordeel"], i["opmerking"], i["signalen"]])
    from collections import Counter
    tel = Counter(i["oordeel"] for i in alle)
    md = [f"# Inhoudelijke review — {len(alle)} begrippen", "",
          " | ".join(f"{o}: {tel.get(o, 0)}" for o in OORDELEN), ""]
    for o, kop in (("term", "Termomzetting aanpassen (via project.yaml)"),
                   ("definitie", "Advies voor het UML-model (definities niet herschreven)"), ("twijfel", "Twijfel")):
        rij = [i for i in alle if i["oordeel"] == o]
        if rij:
            md += [f"## {kop} ({len(rij)})", "", "Verwijs met de id (vast); het nummer verschuift na opnieuw genereren.", "",
                   "| id | term | soort | opmerking |", "|---|---|---|---|"]
            md += [f"| {i['id'] or i['nr']} | {i['term']} | {i['soort']} | {i['opmerking'].replace('|', '/')} |" for i in rij]
            md.append("")
    open(P("reports", "review.md"), "w", encoding="utf-8").write("\n".join(md))
    print(f"Review compleet: {dict(tel)} -> reports/review.md, reports/review.tsv")
    if tel.get("term"):
        print("Termcorrecties: leg ze voor aan de gebruiker en zet ze met bk.py zet (klasse/waarde: termen.vast.<UML-naam>; "
              "attribuut: attributen.term_correcties.<UML-attribuutnaam>). Daarna bk.py genereer.")
    volgende("bk.py rapport")


def cmd_voortgang(_):
    if review_voortgang() is None:
        print("Nog geen review gestart.")


# ---------- externe matches in delen ----------

def cmd_matches(a):
    if a and a[0] == "klaar":
        return matches_klaar()
    run("extern.py", "voorstellen", KADER, PROJECT, P("werk"))
    kand = json.load(open(P("werk", "matchkandidaten.json")))
    kand = [k for k in kand if not k["al_gelegd"]]
    os.makedirs(P("matches"), exist_ok=True)
    for f in glob.glob(P("matches", "deel-*.md")):
        os.remove(f)
    delen = []
    for start in range(0, len(kand), PER_DEEL):
        nr = len(delen) + 1
        regels = [f"# Matchkandidaten deel {nr}", "",
                  f"Vul bij ELKE kandidaat `relatie:` in met één van: {' | '.join(RELATIES)}.",
                  "exactMatch = zelfde betekenis; closeMatch = vrijwel gelijk; broadMatch = extern begrip is breder; "
                  "narrowMatch = extern is smaller; relatedMatch = verwant; geen = geen match.",
                  "Bij alles behalve geen is `opmerking:` verplicht (korte motivering). Verwijder geen regels.", ""]
        for i, k in enumerate(kand[start:start + PER_DEEL], start + 1):
            regels += [f"### {i:04} | {k['term']}", f"ons: {k['definitie'] or '(geen)'}",
                       f"extern ({k['kader']}): {k['extern_term']} <{k['extern_uri']}>",
                       f"extern definitie: {k['extern_definitie'] or '(geen)'}", "relatie: ", "opmerking: ", ""]
        naam = f"deel-{nr:03}.md"
        open(P("matches", naam), "w", encoding="utf-8").write("\n".join(regels))
        delen.append(dict(bestand=naam, van=start + 1, tot=min(start + PER_DEEL, len(kand))))
    json.dump(dict(aantal=len(kand), delen=delen), open(P("matches", "index.json"), "w"), indent=1)
    print(f"{len(kand)} matchkandidaten in {len(delen)} delen (matches/). Kaders zonder bulkdownload (BAG): "
          "matches alleen handmatig, zie werk/matchvoorstellen.md.")
    review_voortgang("matches", RELATIES, "relatie", "bk.py matches klaar")


def matches_klaar():
    open_ = review_voortgang("matches", RELATIES, "relatie", "bk.py matches klaar", stil=True)
    if open_ is None:
        sys.exit("Eerst: bk.py matches")
    if open_:
        sys.exit(1)
    idx = json.load(open(P("matches", "index.json")))
    nieuw = []
    for d in idx["delen"]:
        tekst = open(P("matches", d["bestand"]), encoding="utf-8").read()
        for blok in tekst.split("\n### ")[1:]:
            term = blok.split("\n")[0].split("|", 1)[1].strip()
            uri = re.search(r"<(http[^>]+)>", blok).group(1)
            rel = re.search(r"^relatie:\s*(\S*)", blok, re.M).group(1).strip("`*")
            rel = next((x for x in RELATIES if x.lower() == rel.lower()), rel)
            if rel != "geen":
                nieuw.append(dict(term=term, relatie=rel, uri=uri))
    if "--overnemen" not in sys.argv:
        for m in nieuw:
            print(f"  {m['term']} {m['relatie']} <{m['uri']}>")
        print(f"\n{len(nieuw)} matches. Leg deze lijst ter bevestiging voor aan de gebruiker (het matchtype is een "
              "inhoudelijk oordeel).")
        volgende("na bevestiging: bk.py matches klaar --overnemen, daarna bk.py genereer")
        return
    proj = yaml_lees(PROJECT)
    samenvoegen(proj, {"matches": nieuw, "notities": [f"matches: {len(nieuw)} matches uit matches/ overgenomen"]})
    yaml_schrijf(PROJECT, proj)
    print(f"{len(nieuw)} matches in project.yaml gezet.")
    volgende("bk.py genereer")


# ---------- opzoeken ----------

def cmd_toon(a):
    if not a:
        sys.exit("Gebruik: bk.py toon <naam of Klasse.attribuut>")
    from kern import clean_def
    inv = json.load(open(INV))
    q = a[0].lower()
    kl, at = (q.split(".", 1) + [None])[:2] if "." in q else (q, None)
    gevonden = 0
    for c in inv["elementen"].values():
        if at is None and q in (c["name"].lower(), (c.get("alias") or "").lower()):
            gevonden += 1
            print(f"{c['name']} «{c['stereo']}» ({c['type']}) package {c.get('pkg')} alias {c.get('alias') or '-'}")
            print(f"  definitie: {clean_def(c['doc'])[:400] or '(geen)'}")
            print(f"  superklassen: {[inv['elementen'].get(g, {}).get('name') or inv.get('externe_klassen', {}).get(g, g) for g in c.get('gens', [])]}")
            for x in c["attrs"][:60]:
                print(f"  - {x['name']}: {x.get('type') or '-'} | {clean_def(x['doc'])[:100]}")
            if len(c["attrs"]) > 60:
                print(f"  ... {len(c['attrs']) - 60} meer")
        for x in c["attrs"]:
            if (at and c["name"].lower() == kl and x["name"].lower() == at) or (at is None and x["name"].lower() == q):
                gevonden += 1
                print(f"{c['name']}.{x['name']} (type {x.get('type') or '-'}): {clean_def(x['doc'])[:400] or '(geen)'}")
    if not gevonden:
        namen = [c["name"] for c in inv["elementen"].values()]
        print(f"Niet gevonden. Lijkt op: {difflib.get_close_matches(a[0], namen, 5)}")


# ---------- optioneel ----------

def cmd_vergelijk(a):
    if not a:
        sys.exit("Gebruik: bk.py vergelijk <URL of bestand van het gepubliceerde kader>")
    r = subprocess.run([sys.executable, os.path.join(HIER, "vergelijk.py"), KADER, a[0], P("uit", "vergelijking.csv")],
                       capture_output=True, text=True)
    print(r.stdout + r.stderr)
    if r.returncode:
        sys.exit(r.returncode)
    with open(P("uit", "vergelijking.txt"), "w", encoding="utf-8") as f:
        f.write(f"gepubliceerd kader: {a[0]}\n{r.stdout}")
    print("-> uit/vergelijking.txt en uit/vergelijking.csv (komt in het rapport bij bk.py rapport)")
    volgende("bk.py rapport (neemt de vergelijking op)")


def cmd_bronnen(a):
    run("bronnencontrole.py", KADER, P("reports", "bronnencontrole.tsv"), *a)


# ---------- rapport ----------

def cmd_rapport(_):
    from collections import Counter
    st, proj = status_lees(), yaml_lees(PROJECT)
    inv = json.load(open(INV)) if os.path.exists(INV) else {"elementen": {}}
    r = ["# Rapport omzetting naar NL-SBB", "",
         "## 1. Bron", "",
         f"- bestand: {os.path.basename(st.get('bron', inv.get('bron', '?')))}",
         f"- packages: {', '.join(st.get('packages') or []) or '(alles)'}"
         + (f"; uitgesloten: {', '.join(st.get('zonder'))}" if st.get("zonder") else ""),
         f"- inventaris: {len(inv['elementen'])} UML-elementen, "
         f"{sum(len(c['attrs']) for c in inv['elementen'].values())} attributen/waarden", ""]
    r += ["## 2. Keuzes", "", "Standaardkeuzes uit de skill, met deze afwijkingen (project.yaml):", "", "```yaml"]
    import yaml
    r += [yaml.safe_dump({k: v for k, v in proj.items() if k not in ("notities",)}, allow_unicode=True,
                         sort_keys=False, width=110).rstrip(), "```", ""]
    if proj.get("notities"):
        r += ["Notities bij de keuzes:", ""] + [f"- {n}" for n in proj["notities"]] + [""]
    pp = punten()
    if pp:
        tel = Counter(p["soort"] for p in pp)
        r += [f"Beslispunten: {dict(tel)}.", ""]
        r += [f"- [{p['soort']}] {p['code']}: {p['titel'][:160]}" for p in pp if p["soort"] in ("VRAAG", "BESLOTEN")]
        r.append("")
    if os.path.exists(P("werk", "aannames.md")):
        r += ["Aannames (zonder bevestiging door de gebruiker):", "", open(P("werk", "aannames.md")).read().strip(), ""]
    r += ["## 3. Resultaat", ""]
    if os.path.exists(TERMEN):
        rij = termen_lezen()
        tel = Counter(x["soort"] for x in rij)
        r += [f"- {len(rij)} begrippen: " + ", ".join(f"{k} {v}" for k, v in sorted(tel.items())),
              f"- zonder definitie: {sum(1 for x in rij if not x['definitie'])}"]
    if os.path.exists(P("uit", "beslissingen.md")):
        r.append(f"- log: {sum(1 for x in open(P('uit', 'beslissingen.md')) if x.startswith('- '))} regels in uit/beslissingen.md")
    r.append("")
    if os.path.exists(SHACL):
        r += ["## 4. SHACL-validatie", "", "Instellingen: NL-SBB-profiel + skill-extensie, advanced=True, inference=rdfs. "
              "Oordeel op de telling per ernstniveau, niet op `conforms`.", ""]
        for x in open(SHACL):
            if x.startswith("===") or "telling:" in x or x.startswith("profiel") or x.startswith("waarvan"):
                r.append(f"    {x.rstrip()}")
        laatste = open(SHACL).read().split("\n=== ")[-1].split("\n")
        top = [x.rstrip() for x in laatste if x.startswith("[Violation]")][:8]
        if top:
            r += ["", "Belangrijkste violations:", ""] + [f"- {x[:200]}" for x in top]
        r.append("")
    if os.path.exists(P("reports", "review.md")):
        rv = open(P("reports", "review.md")).read().split("\n")
        r += ["## 5. Inhoudelijke review", "", rv[2], "", "Details: reports/review.md", ""]
    else:
        r += ["## 5. Inhoudelijke review", "", "NIET UITGEVOERD of niet compleet (bk.py review).", ""]
    if os.path.exists(P("uit", "vergelijking.txt")):
        r += ["## 6. Vergelijking met gepubliceerd kader", "", "```",
              open(P("uit", "vergelijking.txt")).read().strip()[:4000], "```", ""]
    if os.path.exists(P("werk", "rapport-aanvulling.md")):
        # eigen secties (bv. doorgevoerde termcorrecties); bk.py rapport overschrijft rapport.md, dit bestand niet
        r += [open(P("werk", "rapport-aanvulling.md"), encoding="utf-8").read().strip(), ""]
    r += ["## Conclusie", "", "<!-- LLM: vervang deze regel door 3-6 zinnen: bruikbaarheid, belangrijkste problemen, "
          "wat de gebruiker nog moet beslissen. Verzin geen cijfers; gebruik alleen de getallen hierboven. -->", ""]
    os.makedirs(P("reports"), exist_ok=True)
    open(P("reports", "rapport.md"), "w", encoding="utf-8").write("\n".join(r))
    print("reports/rapport.md geschreven.")
    volgende("vul alleen de sectie 'Conclusie' in reports/rapport.md aan; verander de cijfers niet.")


# ---------- status ----------

def cmd_status(_):
    def stap(t):
        print(f"Werkmap: {WM}")
        volgende(t)
    if not _deps_ok():
        return stap("python3 SKILL/scripts/bk.py setup")
    if not os.path.exists(INV):
        if os.path.exists(P("werk", "packages.txt")):
            return stap("kies package(s) uit werk/packages.txt en draai bk.py start <bestand> --package <naam>")
        return stap("bk.py start <bestand>")
    if not nieuwer(BESLIS, INV) or not nieuwer(BESLIS, PROJECT):
        return stap("bk.py analyseer")
    open_ = [(i, p) for i, p in enumerate(punten(), 1) if p["soort"] == "VRAAG"]
    if open_:
        print(f"{len(open_)} open VRAAG-punten: " + ", ".join(f"{i}={p['code']}" for i, p in open_))
        return stap(f"bk.py vraag {open_[0][0]}  -> voorleggen -> bk.py overnemen {open_[0][1]['code']} "
                    "(of bk.py zet ...) -> bk.py analyseer")
    if not os.path.exists(PROJECT):
        return stap("vraag de gebruiker of de standaardkeuzes goed zijn; leg kader-URI vast met bk.py zet kader.uri ...")
    if controleer(stil=True):
        return stap("herstel project.yaml (bk.py controleer toont de fouten)")
    if not nieuwer(KADER, PROJECT) or not nieuwer(KADER, INV):
        return stap("bk.py genereer")
    if not nieuwer(SHACL, KADER):
        return stap("bk.py valideer")
    idx = P("review", "index.json")
    if not os.path.exists(idx) or json.load(open(idx))["hash"] != hash_bestand(TERMEN):
        return stap("bk.py review" + (" --opnieuw" if os.path.exists(idx) else ""))
    if not nieuwer(P("reports", "review.md"), idx):
        review_voortgang()  # noemt het eerstvolgende deel, of `bk.py review klaar`
        return
    if not nieuwer(P("reports", "rapport.md"), P("reports", "review.md")) or \
            any(os.path.exists(f) and not nieuwer(P("reports", "rapport.md"), f)
                for f in (P("uit", "vergelijking.txt"), P("werk", "rapport-aanvulling.md"))):
        return stap("bk.py rapport")
    if "<!-- LLM:" in open(P("reports", "rapport.md")).read():
        return stap("vul de sectie 'Conclusie' in reports/rapport.md")
    print("KLAAR: kader, validatie, review en rapport zijn compleet.")
    print("Optioneel (eerst de gebruiker vragen): bk.py matches | bk.py vergelijk <url> | bk.py bronnen")


COMMANDO = {
    "setup": (cmd_setup, "virtuele omgeving maken in de werkmap"),
    "status": (cmd_status, "toont de volgende stap (draai dit na elke stap)"),
    "start": (cmd_start, "<bestand> [--package P] [--zonder P]: inventaris uit XMI/EAP/ZIP"),
    "voorbeeld": (cmd_voorbeeld, "<naam> [--overschrijf]: ingevuld voorbeeld uit SKILL/voorbeelden/ als project.yaml"),
    "analyseer": (cmd_analyseer, "beslispunten maken (INFO / VRAAG / BESLOTEN)"),
    "vraag": (cmd_vraag, "<nr> [--vanaf N]: één beslispunt met details en scriptvoorstel"),
    "overnemen": (cmd_overnemen, "<code ...> | --alle [--standaard]: scriptvoorstel(len) in project.yaml"),
    "zet": (cmd_zet, "<sleutel.pad> '<yaml-waarde>' [--notitie T]: één keuze in project.yaml"),
    "controleer": (cmd_controleer, "project.yaml controleren (sleutels, namen, regexen)"),
    "toon": (cmd_toon, "<naam | Klasse.attribuut>: element uit de inventaris opzoeken"),
    "genereer": (cmd_genereer, "kader.ttl + termen.tsv + beslissingen.md maken"),
    "valideer": (cmd_valideer, "SHACL-validatie (run A en B)"),
    "review": (cmd_review, "[klaar | --opnieuw]: reviewdelen maken / controleren en samenvoegen"),
    "oordeel": (cmd_oordeel, "[--matches] < regels '<nr> <oordeel> [| opmerking]': oordelen invullen via stdin"),
    "voortgang": (cmd_voortgang, "voortgang van de review"),
    "matches": (cmd_matches, "[klaar [--overnemen]]: matchkandidaten in delen / overnemen"),
    "vergelijk": (cmd_vergelijk, "<url|bestand>: vergelijken met een gepubliceerd kader"),
    "bronnen": (cmd_bronnen, "[--skosmos URL] [--bronnenlijst PAD]: bronnencontrole"),
    "rapport": (cmd_rapport, "reports/rapport.md maken (cijfers door het script)"),
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("help", "-h", "--help") or sys.argv[1] not in COMMANDO:
        if len(sys.argv) >= 2 and sys.argv[1] not in ("help", "-h", "--help"):
            print(f"Onbekend commando '{sys.argv[1]}'{_lijkt(sys.argv[1], COMMANDO)}\n")
        print("bk.py <commando> — draai vanuit de werkmap. Begin altijd met: bk.py status\n")
        for k, (_, uitleg) in COMMANDO.items():
            print(f"  {k:11} {uitleg}")
        return
    sys.path.insert(0, HIER)
    COMMANDO[sys.argv[1]][0](sys.argv[2:])


if __name__ == "__main__":
    main()
