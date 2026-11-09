"""Stap 4 — SHACL-validatie tegen NL-SBB (profiel + skill-extensie). Deterministisch.

Gebruik: python valideer.py uit/kader.ttl project.yaml reports/ [context.ttl ...]

Run A: alleen het kader. Run B (als er context is): kader + externe kaders, alleen
focusnodes binnen kader.uri geteld. Instellingen volgens de NL-SBB-skill: advanced=True,
inference=rdfs, geen allow-warnings; oordeel op telling per ernstniveau, niet op `conforms`.
"""
import collections
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pyshacl  # noqa: E402
import rdflib  # noqa: E402
from rdflib.namespace import SKOS  # noqa: E402

from kern import SKILL_DIR, haal, laad_keuzes  # noqa: E402

SH = rdflib.Namespace("http://www.w3.org/ns/shacl#")


def extensie(cfg, werk):
    """De skill-extensie: uit SKILL/shacl/, of (als die map bij de installatie is weggevallen) een kopie."""
    pad = os.path.join(SKILL_DIR, "shacl", "skos-ap-nl-extensie.ttl")
    if os.path.exists(pad):
        return pad
    kopie = os.path.join(werk, "skos-ap-nl-extensie.ttl")
    url = cfg["validatie"].get("extensie_fallback")
    if os.path.exists(kopie) or (url and haal(url, kopie, accept="text/turtle,*/*")):
        print(f"LET OP: {pad} ontbreekt (onvolledige installatie); kopie gebruikt: {url}")
        return kopie
    sys.exit(f"FOUT: de SHACL-extensie ontbreekt: {pad}\n"
             f"De installatie van de skill is onvolledig (de map shacl/ hoort erbij), en ophalen van {url} lukte niet.\n"
             f"Herstel: zet dat bestand in SKILL/shacl/ of in werk/, en draai bk.py valideer opnieuw.")


def profiel(cfg, werk):
    pad = os.path.join(werk, "skos-ap-nl.ttl")
    if not os.path.exists(pad):
        for url in (cfg["validatie"]["profiel"], cfg["validatie"]["profiel_fallback"]):
            if haal(url, pad, accept="text/turtle,*/*"):
                print(f"profiel: {url}")
                break
        else:
            sys.exit("Geen SHACL-profiel beschikbaar")
    g = rdflib.Graph().parse(pad)
    versie = next(iter(g.objects(None, rdflib.OWL.versionInfo)), "?")
    g.parse(extensie(cfg, werk))
    return g, versie


def extern_zonder_begrip(data, kader_uri):
    """Match-doelen buiten het kader die in de graaf geen skos:Concept zijn (extern kader niet opgehaald)."""
    doelen = set()
    for p in ("exactMatch", "closeMatch", "broadMatch", "narrowMatch", "relatedMatch"):
        doelen |= {o for o in data.objects(None, SKOS[p]) if not str(o).startswith(kader_uri)}
    return {o for o in doelen if (o, rdflib.RDF.type, SKOS.Concept) not in data}


def run(naam, data, shapes, alleen, reports, label_graph, extern=frozenset()):
    conf, rg, txt = pyshacl.validate(data, shacl_graph=shapes, advanced=True, inference="rdfs")
    open(os.path.join(reports, f"shacl-{naam}.txt"), "w").write(txt)
    rows, tel = collections.defaultdict(list), collections.Counter()
    door_extern = 0
    for r in rg.subjects(rdflib.RDF.type, SH.ValidationResult):
        foc = rg.value(r, SH.focusNode)
        if alleen and not str(foc).startswith(alleen):
            continue
        sev = str(rg.value(r, SH.resultSeverity)).split("#")[1]
        tel[sev] += 1
        if sev == "Violation" and rg.value(r, SH.value) in extern:
            door_extern += 1
        shape = str(rg.value(r, SH.sourceShape)).split("#")[-1].split("/")[-1]
        # focus-URI's uit de melding halen, zodat gelijke bevindingen samen geteld worden
        msg = re.sub(r"<[^>]+>", "<…>", str(rg.value(r, SH.resultMessage)))[:110]
        rows[(sev, shape, msg)].append(str(label_graph.value(foc, SKOS.prefLabel) or foc))
    out = [f"=== {naam} ===", f"conforms-veld: {conf} (niet leidend) | telling: "
           f"Violation {tel['Violation']}, Warning {tel['Warning']}, Info {tel['Info']}"]
    if door_extern:
        out.append(f"waarvan {door_extern} violations door match-doelen die in de graaf geen skos:Concept zijn "
                   f"({len(extern)} externe URI's; extern kader niet opgehaald of begrip bestaat daar niet)")
    volg = {"Violation": 0, "Warning": 1, "Info": 2}
    for (sev, sh, msg), l in sorted(rows.items(), key=lambda kv: (volg.get(kv[0][0], 3), -len(kv[1]), kv[0])):
        out.append(f"[{sev}] {sh} x{len(l)}: {msg}\n     bv. {sorted(set(l))[:8]}")
    s = "\n".join(out)
    print(s)
    return s


def main(kader, project, reports, *ctx):
    cfg = laad_keuzes(project)
    werk = os.path.join(os.path.dirname(os.path.abspath(reports)), "werk")
    os.makedirs(reports, exist_ok=True)
    os.makedirs(werk, exist_ok=True)
    shapes, versie = profiel(cfg, werk)
    print(f"NL-SBB-profiel owl:versionInfo {versie}; pySHACL {pyshacl.__version__}; advanced=True, inference=rdfs\n")
    data = rdflib.Graph().parse(kader)
    uri = cfg["kader"]["uri"]
    delen = [run("A-kaal", data, shapes, None, reports, data, extern_zonder_begrip(data, uri))]
    if ctx:
        d2 = rdflib.Graph().parse(kader)
        for f in ctx:
            d2.parse(f)
        delen.append(run("B-context", d2, shapes, uri, reports, d2, extern_zonder_begrip(d2, uri)))
    open(os.path.join(reports, "shacl-samenvatting.txt"), "w").write(
        f"profiel {versie}, pySHACL {pyshacl.__version__}, advanced=True, inference=rdfs\n\n" + "\n\n".join(delen) + "\n")


if __name__ == "__main__":
    main(*sys.argv[1:])
