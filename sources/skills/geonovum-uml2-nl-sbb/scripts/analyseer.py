"""Stap 2 — inventaris.json + keuzes -> beslispunten.md/.json. Deterministisch.

Gebruik: python analyseer.py werk/inventaris.json [project.yaml] werk/

Somt op wat de standaardkeuzes automatisch afhandelen (INFO) en waar een beslissing van de
gebruiker nodig is (VRAAG). Voorstellen (VOORSTEL) zijn heuristisch en moeten bevestigd worden.
Pas na dit script legt de LLM de VRAAG-punten voor aan de gebruiker.
"""
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kern import Termen, bron_tag, clean_def, def_key, herkomst, indeling, laad_inventaris, laad_keuzes  # noqa: E402


MIM = {"objecttype", "gegevensgroeptype", "codelijst", "enumeratie", "referentielijst", "gestructureerd datatype",
       "primitief datatype", "keuze", "attribuutsoort"}


def split_voorstel(anders):
    """Per conflict: kleinste onderlinge gelijkenis van de definities. Hoog -> zelfde begrip, anders splitsen."""
    from difflib import SequenceMatcher
    zelfde, rest = [], []
    for lab, lst in anders:
        defs = sorted({clean_def(d).lower() for _, d in lst})
        minimum = min((SequenceMatcher(None, a, b).ratio() for i, a in enumerate(defs) for b in defs[i + 1:]), default=1)
        (zelfde if minimum >= 0.8 else rest).append(lab)
    v = {"waarden": {}}
    if zelfde:
        v["waarden"]["zelfde_begrip"] = zelfde
    if rest:
        v["waarden"]["automatisch_splitsen"] = "{lijst} {waarde}"
    return v


def bron_voorstel(onb):
    """Eén mappingregel per genormaliseerde tagwaarde; meest voorkomende schrijfwijze als titel."""
    groep = defaultdict(Counter)
    for t, n in onb.items():
        groep[t.strip().upper().replace(" ", "")][t.strip()] += n
    uit = []
    for pat, schrijf in sorted(groep.items(), key=lambda kv: -sum(kv[1].values())):
        t = schrijf.most_common(1)[0][0]
        titel = re.sub(r"\s+", " ", t).strip(" ;,.")
        uit.append({"patroon": re.escape(pat) + "$",
                    "sleutel": re.sub(r"[^0-9A-Za-z]+", "-", titel).strip("-")[:40] or "bron", "titel": titel})
    return uit


def main(inv_pad, project, uitdir):
    cfg = laad_keuzes(project)
    inv = laad_inventaris(inv_pad, cfg)
    T = Termen(cfg)
    obj, dat, cod, over = indeling(inv, cfg)
    klassen = {**obj, **dat}
    ext = inv.get("externe_klassen") or {}
    rel = cfg["relaties"]
    punten = []

    besloten = set(cfg.get("besloten") or [])

    def punt(soort, code, titel, details=None, voorstel=None):
        if soort == "VRAAG" and code in besloten:
            soort = "BESLOTEN"  # de gebruiker heeft dit punt bewust zo gelaten (project.yaml: besloten)
        punten.append(dict(soort=soort, code=code, titel=titel, details=details or [], voorstel=voorstel))

    # A. overzicht
    st = Counter((c["type"], c["stereo"]) for c in inv["elementen"].values())
    punt("INFO", "overzicht", f"{len(obj)} objecttypen, {len(dat)} datatypen, {len(cod)} waardelijsten, "
         f"{len(over)} overgeslagen; {sum(len(c['attrs']) for c in klassen.values())} attributen, "
         f"{sum(len(c['attrs']) for c in cod.values())} waarden",
         [f"{t} «{s}»: {n}" for (t, s), n in sorted(st.items(), key=str)])

    # B. stereotypen die niet in de lijsten staan -> objecttype
    bekend = {s.lower() for s in cfg["stereotypen"]["waardelijst"] + cfg["stereotypen"]["datatype"]
              + (cfg["stereotypen"].get("overslaan") or [])}
    onbekend = Counter(c["stereo"] for c in obj.values() if c["stereo"] and c["stereo"].lower() not in bekend)
    if onbekend:
        punt("INFO", "stereotypen", "Stereotypen die als objecttype worden behandeld (controleer)",
             [f"«{s}»: {n}" for s, n in onbekend.items()])

    # C. hiërarchie
    by_name = {c["name"]: k for k, c in klassen.items()}
    zonder = []
    for k, c in klassen.items():
        if k in dat:
            continue
        intern = [g for g in c["gens"] if g in klassen and g != k]
        if intern:
            continue
        extn = [ext.get(g, g) for g in c["gens"] if g not in klassen]
        opnaam = [n for n in extn if n in by_name and by_name[n] != k]
        if opnaam and rel.get("externe_superklasse_op_naam", True):
            continue
        zonder.append((c["name"], extn))
    if zonder:
        cand = Counter(n for _, e in zonder for n in e)
        root_guess = next((c["name"] for c in klassen.values() if c["name"].lstrip("_") in
                           {n.lstrip("_") for n in cand}), None)
        soort = "INFO" if rel.get("wortel") else "VRAAG"
        punt(soort, "wortel",
             f"{len(zonder)} klassen zonder superklasse in het model"
             + (f" (komen onder wortel '{rel['wortel']}')" if rel.get("wortel") else
                ": allemaal topbegrip, of één wortelbegrip kiezen (relaties.wortel) en uitzonderingen (relaties.zelfstandig)?"),
             [f"{n}" + (f" (externe superklasse: {', '.join(e)})" if e else "") for n, e in zonder],
             voorstel={"relaties": {"wortel": root_guess}} if root_guess and not rel.get("wortel") else
             ({"relaties": {"wortel": None}} if not rel.get("wortel") else None))

    # D. ontbrekende definities
    leeg = [f"klasse {c['name']}" for c in klassen.values() if not clean_def(c["doc"])]
    leeg += [f"attribuut {c['name']}.{a['name']}" for c in klassen.values() for a in c["attrs"] if not clean_def(a["doc"])]
    leeg += [f"waarde {c['name']}.{a['name']}" for c in cod.values() for a in c["attrs"] if not clean_def(a["doc"])]
    if leeg:
        punt("INFO", "definities", f"{len(leeg)} elementen zonder definitie (komen zonder skos:definition in het kader -> SHACL-fout)", leeg)

    # E. attributen met dezelfde naam
    an = defaultdict(lambda: defaultdict(list))
    for c in klassen.values():
        for a in c["attrs"]:
            an[a["name"]][def_key(a["doc"])].append(c["name"])
    same = {n: d for n, d in an.items() if len(d) == 1 and len(next(iter(d.values()))) > 1}
    diff = {n: d for n, d in an.items() if len(d) > 1}
    if same:
        punt("INFO", "attributen-samen", f"{len(same)} attribuutnamen met gelijke definitie in meerdere klassen -> één begrip",
             [f"{n}: {', '.join(next(iter(d.values())))}" for n, d in same.items()])
    if diff:
        punt("INFO", "attributen-context", f"{len(diff)} attribuutnamen met verschillende definities -> termen krijgen objecttype-context",
             [f"{n}: {len(d)} definities" for n, d in diff.items()])
    pref = Counter(m.group(0) for c in klassen.values() for a in c["attrs"] if (m := re.match(r"^[a-z]+-", a["name"])))
    pref = {p: n for p, n in pref.items() if n > 1}
    if pref and not cfg["termen"].get("naam_prefixen_verwijderen"):
        punt("VRAAG", "prefixen", "Attribuutnamen met een prefix: verwijderen uit de term (termen.naam_prefixen_verwijderen) "
             "en eventueel als voorvoegsel behouden (attributen.prefix_term)?", [f"'{p}': {n}x" for p, n in pref.items()],
             voorstel={"termen": {"naam_prefixen_verwijderen": sorted(pref)}})

    # F. waarden in meerdere waardelijsten
    split = {k.lower() for k in (cfg["waarden"].get("splitsingen") or {})}
    hern = {k.lower(): v for k, v in (cfg["waarden"].get("hernoem") or {}).items()}
    vg = defaultdict(list)
    for c in cod.values():
        for a in c["attrs"]:
            nm = a["name"].strip()
            if f"{nm.lower()}|{c['name'].lower()}" in split:
                continue
            vg[hern.get(nm.lower()) or (a.get("term") or None) or T.waarde(nm)].append((c["name"], a["doc"]))
    zelfde = {z.lower() for z in cfg["waarden"].get("zelfde_begrip") or []}
    auto = cfg["waarden"].get("automatisch_splitsen")
    gelijk, lees, anders = [], [], []
    for lab, lst in sorted(vg.items()):
        if len(lst) < 2:
            continue
        keys = {def_key(d) for _, d in lst}
        variants = {clean_def(d) for _, d in lst}
        if len(keys) > 1 and lab.lower() in zelfde:
            lees.append(f"{lab}: {len(keys)} definitievarianten, samengevoegd via waarden.zelfde_begrip")
        elif len(keys) > 1:
            anders.append((lab, lst))
        elif len(variants) > 1:
            lees.append(f"{lab}: {', '.join(c for c, _ in lst)}")
        else:
            gelijk.append(f"{lab}: {len(lst)} lijsten ({', '.join(c for c, _ in lst)})")
    if gelijk:
        punt("INFO", "waarden-samen", f"{len(gelijk)} waarden met gelijke naam en definitie in meerdere lijsten -> één begrip "
             "(standaardkeuze), lid van meerdere collecties", gelijk)
    if lees:
        punt("INFO", "waarden-leestekens", f"{len(lees)} waarden waarvan de definities alleen in leestekens verschillen -> samengevoegd", lees)
    if anders and auto:
        punt("INFO", "waarden-splitsen", f"{len(anders)} waarden met gelijke naam en andere definitie worden automatisch "
             f"gesplitst volgens '{auto}' (waarden.automatisch_splitsen)", [lab for lab, _ in anders])
    elif anders:
        det = []
        for lab, lst in anders:
            det.append(f"'{lab}':")
            det += [f"    {c}: \"{clean_def(d)[:160]}\"" for c, d in lst]
        punt("VRAAG", "waarden-splitsen", f"{len(anders)} waarden met gelijke naam en inhoudelijk andere definitie: "
             "splitsen in aparte begrippen (waarden.splitsingen, sleutel 'waarde|Waardelijst') — genereer.py stopt anders. "
             "Voorstel: bijna gelijke definities (gelijkenis >= 0,8) als één begrip (waarden.zelfde_begrip), "
             "de rest automatisch splitsen met de term van de lijst ervoor", det,
             voorstel=split_voorstel(anders))

    # G. gebruik van waardelijsten
    gebruikt = {a.get("type") for c in klassen.values() for a in c["attrs"]}
    cfg_g = rel.get("gebruik") or {}
    leeg = [c["name"] for c in cod.values() if not c["attrs"]]
    if leeg:
        punt("INFO", "waardelijsten-leeg", f"{len(leeg)} waardelijsten zonder waarden in het model (extern beheerd?): "
             "geen collectie; attributen die ze gebruiken worden wel begrip", leeg)
    los = [c for c in cod.values() if c["attrs"] and c["name"] not in gebruikt and c["name"] not in cfg_g]
    auto = [c["name"] for c in cod.values() if c["name"] in gebruikt and c["name"] not in cfg_g]
    if auto:
        punt("INFO", "gebruik-auto", f"{len(auto)} waardelijsten automatisch gekoppeld via attribuuttype", auto)
    if los:
        det, voorstel = [], {}
        cod_namen = {c["name"] for c in cod.values()}
        pfx_woorden = {m.group(1) for c in klassen.values() for a in c["attrs"] if (m := re.match(r"^([a-z]+)-", a["name"]))}
        labels = {c["name"]: [c["name"].lstrip("_"), c["alias"] or ""] for c in klassen.values()}
        for c in los:
            low = c["name"].lower()
            best = max(((len(x), n) for n, xs in labels.items() for x in xs if x and x.lower() in low), default=None)
            attr = None
            if best:
                cw = set(T.humanize(c["name"]).split())
                for a in klassen[by_name[best[1]]]["attrs"]:
                    m = re.match(r"^([a-z]+)-", a["name"])
                    q = m.group(1) if m else None
                    # prefix (bv. plus-) moet passen bij de lijst: TypeBakPlus -> plus-type, TypeBak niet
                    has = {p for p in pfx_woorden if p in low}
                    pas = (q in has) or (not has and (q is None or (c["name"] + q.capitalize()) not in cod_namen))
                    aw = set(T.humanize(re.sub(r"^[a-z]+-", "", a["name"])).split())
                    if pas and aw and aw <= cw | {"type"}:
                        attr = a["name"]
                voorstel[c["name"]] = [best[1], attr]
            else:
                voorstel[c["name"]] = None
            det.append(f"{c['name']} -> " + (f"[{best[1]}, {attr}]" if best else "geen voorstel"))
        punt("VRAAG", "gebruik", f"{len(los)} waardelijsten die door geen attribuut (type) worden gebruikt: aan welk "
             "attribuut of objecttype koppelen (relaties.gebruik; null = niet relateren -> verweesde waarden)?",
             det, voorstel={"relaties": {"gebruik": voorstel}})

    # H. herkomst
    tagnaam = cfg["bronnen"]["tag"]
    tags = Counter()
    for c in list(klassen.values()) + list(cod.values()):
        tags[bron_tag(c, cfg)] += 1
        for a in c["attrs"]:
            tags[bron_tag(a, cfg)] += 1
    url = {t for t in tags if t and re.fullmatch(r"https?://\S+", t.strip())}
    if url:
        punt("INFO", "bronnen-uri", f"{len(url)} herkomstwaarden zijn een URL: brondocument met foaf:page", sorted(url))
    onb = {t: n for t, n in tags.items() if t is not None and t not in url and herkomst(t, cfg) == "ONBEKEND"}
    bek = {t: herkomst(t, cfg) for t in tags if t is not None and herkomst(t, cfg) not in (None, "ONBEKEND")}
    if bek:
        punt("INFO", "bronnen", f"{len(set(bek.values()))} brondocumenten herkend uit tag '{tagnaam}'",
             [f"'{t}' -> {v[0]}" for t, v in sorted(bek.items())])
    if onb:
        punt("VRAAG", "bronnen-onbekend", f"{len(onb)} waarden van tag '{tagnaam}' zonder bronmapping (bronnen.mapping): "
             "welk brondocument (sleutel + titel)? Voorstel: één brondocument per tagwaarde (titel controleren)",
             [f"'{t}': {n}x" for t, n in sorted(onb.items(), key=lambda x: -x[1])],
             voorstel={"bronnen": {"mapping": bron_voorstel(onb)}})
    if not any(tags.keys() - {None}):
        alle = Counter(t for c in list(klassen.values()) + list(cod.values()) for a in [c] + c["attrs"] for t in a["tags"])
        punt("VRAAG", "bronnen-tag", f"Tag '{tagnaam}' komt niet voor; welke tagged value bevat de herkomst van definities?",
             [f"{t}: {n}x" for t, n in alle.most_common(25)],
             voorstel=next(({"bronnen": {"tag": [t]}} for t, _ in alle.most_common()
                            if re.search(r"herkomst|bron|source", t, re.I)), None))

    # I. aliassen
    al = Counter(c["stereo"] for c in klassen.values() if c["alias"] and c["alias"] != c["name"])
    if al:
        punt("INFO" if cfg["termen"].get("alias_als_voorkeursterm") else "VRAAG", "alias",
             "Klassen met een alias: alias als voorkeursterm gebruiken (termen.alias_als_voorkeursterm), met "
             + ("de UML-naam als altLabel@" + cfg['termen']['alias_naam_als_altlabel'] if cfg['termen'].get('alias_naam_als_altlabel')
              else "de UML-naam alleen als notatie (geen altLabel)") + "?",
             [f"«{s}»: {n}x, bv. " + ", ".join(f"{c['name']} = {c['alias']}" for c in klassen.values()
                                                if c["stereo"] == s and c["alias"])[:200] for s, n in al.items()],
             voorstel=None if cfg["termen"].get("alias_als_voorkeursterm") else {"termen": {
                 "alias_als_voorkeursterm": ["*"],
                 # MIM-modellen hebben Nederlandse UML-namen: geen altLabel@en (UML-naam blijft notatie), zoals in voorbeelden/
                 "alias_naam_als_altlabel": None if any((c["stereo"] or "").lower() in MIM for c in klassen.values())
                 else cfg["termen"].get("alias_naam_als_altlabel")}})

    # J. parent-tag
    pt = rel.get("waarde_parent_tag")
    np_ = sum(1 for c in cod.values() for a in c["attrs"] if (a["tags"].get(pt) or "").strip())
    if pt and np_:
        punt("INFO", "parent", f"{np_} waarden met tag '{pt}' -> broaderGeneric naar de bovenliggende waarde")

    # K. kader
    if not cfg["kader"].get("uri"):
        punt("VRAAG", "kader", "Kader-URI, titel en omschrijving ontbreken (kader.uri / kader.titel / kader.omschrijving)",
             [f"modelnaam/package: {', '.join(sorted({c['pkg'] for c in obj.values() if c['pkg']}))}"],
             voorstel={"kader": {"uri": "http://definities.geostandaarden.nl/" + re.sub(r"[^0-9a-z]+", "", (inv.get("packages") or [os.path.splitext(os.path.basename(inv.get("bron", "model")))[0]])[0].split("/")[-1].lower()),
                                 "titel": (inv.get("packages") or [os.path.splitext(os.path.basename(inv.get("bron", "model")))[0]])[0].split("/")[-1] + "-begrippenkader",
                                 "omschrijving": "Begrippen uit het informatiemodel " + os.path.basename(inv.get("bron", "")) + ", omgezet volgens NL-SBB."}})

    os.makedirs(uitdir, exist_ok=True)
    json.dump(punten, open(os.path.join(uitdir, "beslispunten.json"), "w"), ensure_ascii=False, indent=1)
    with open(os.path.join(uitdir, "beslispunten.md"), "w") as f:
        f.write(f"# Beslispunten — {os.path.basename(inv.get('bron', ''))}\n\n")
        for p in punten:
            f.write(f"## [{p['soort']}] {p['code']}: {p['titel']}\n\n")
            for d in p["details"]:
                f.write(f"- {d}\n" if not d.startswith("    ") else f"  - {d.strip()}\n")
            if p["voorstel"]:
                f.write(f"\nVoorstel (bevestigen):\n\n```yaml\n{json.dumps(p['voorstel'], ensure_ascii=False, indent=1)}\n```\n")
            f.write("\n")
    for p in punten:
        print(f"[{p['soort']}] {p['code']}: {p['titel']}")
    print(f"\n{sum(p['soort'] == 'VRAAG' for p in punten)} vragen; details in {os.path.join(uitdir, 'beslispunten.md')}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) == 2:
        main(a[0], None, a[1])
    else:
        main(*a[:3])
