"""Externe kaders. Deterministisch.

  python extern.py voorstellen uit/kader.ttl project.yaml werk/
      Downloadt externe kaders met bulkdata en zoekt kandidaat-matches op gelijke
      (genormaliseerde) termen. -> werk/matchvoorstellen.md. Het matchtype kiest de LLM
      inhoudelijk; de gebruiker bevestigt; daarna in project.yaml onder `matches`.

  python extern.py context uit/kader.ttl project.yaml werk/context.ttl
      Haalt alle doelen van harmonisatierelaties op (bulk of per begrip) en schrijft ze als
      context voor de SHACL-validatie. Meldt doelen die niet gevonden zijn.
"""
import os
import re
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rdflib  # noqa: E402
from rdflib import RDF  # noqa: E402
from rdflib.namespace import SKOS  # noqa: E402

from kern import haal, laad_keuzes  # noqa: E402

MATCH = [SKOS.exactMatch, SKOS.closeMatch, SKOS.broadMatch, SKOS.narrowMatch, SKOS.relatedMatch]


def norm(s):
    return re.sub(r"[\W_]+", "", str(s).lower())


def bulk(kader, werk):
    if not kader.get("data"):
        return None
    pad = os.path.join(werk, "extern-" + norm(kader["naam"]) + ".ttl")
    if haal(kader["data"], pad):
        return rdflib.Graph().parse(pad, format="turtle")
    return None


def voorstellen(kader_ttl, project, werk):
    cfg = laad_keuzes(project)
    os.makedirs(werk, exist_ok=True)
    ons = rdflib.Graph().parse(kader_ttl)
    idx = {}
    for c in ons.subjects(RDF.type, SKOS.Concept):
        for p in (SKOS.prefLabel, SKOS.altLabel):
            for l in ons.objects(c, p):
                idx.setdefault(norm(l), set()).add(c)
    al = {(str(s), str(o)) for p in MATCH for s, o in ons.subject_objects(p)}
    regels = ["# Matchvoorstellen (op gelijke term)\n",
              "Kies per voorstel het matchtype (exactMatch / closeMatch / broadMatch / narrowMatch / relatedMatch) "
              "op basis van de definities, of laat weg. Bevestig met de gebruiker.\n"]
    kand = []
    for k in cfg.get("externe_kaders") or []:
        g = bulk(k, werk)
        if g is None:
            regels.append(f"\n## {k['naam']}\n\nGeen bulkdownload; voorstellen alleen handmatig (namespace {k['namespace']}).\n")
            continue
        regels.append(f"\n## {k['naam']}\n\n| ons begrip | definitie ons | extern begrip | definitie extern | al gelegd |\n|---|---|---|---|---|")
        n = 0
        for c in g.subjects(RDF.type, SKOS.Concept):
            for l in list(g.objects(c, SKOS.prefLabel)) + list(g.objects(c, SKOS.altLabel)):
                for o in sorted(idx.get(norm(l), ())):
                    n += 1
                    d1 = str(ons.value(o, SKOS.definition) or "")[:140].replace("|", "/")
                    d2 = str(g.value(c, SKOS.definition) or "")[:140].replace("|", "/")
                    regels.append(f"| {ons.value(o, SKOS.prefLabel)} | {d1} | [{g.value(c, SKOS.prefLabel)}]({c}) | {d2} | "
                                  f"{'ja' if (str(o), str(c)) in al else ''} |")
                    kand.append(dict(kader=k["naam"], term=str(ons.value(o, SKOS.prefLabel)),
                                     definitie=str(ons.value(o, SKOS.definition) or ""),
                                     extern_term=str(g.value(c, SKOS.prefLabel)), extern_uri=str(c),
                                     extern_definitie=str(g.value(c, SKOS.definition) or ""),
                                     al_gelegd=(str(o), str(c)) in al))
        print(f"{k['naam']}: {n} kandidaten op gelijke term")
    open(os.path.join(werk, "matchvoorstellen.md"), "w").write("\n".join(regels) + "\n")
    import json
    json.dump(kand, open(os.path.join(werk, "matchkandidaten.json"), "w"), ensure_ascii=False, indent=1)
    print(f"-> {os.path.join(werk, 'matchvoorstellen.md')}")


def context(kader_ttl, project, uit):
    cfg = laad_keuzes(project)
    werk = os.path.dirname(os.path.abspath(uit))
    ons = rdflib.Graph().parse(kader_ttl)
    doelen = {o for p in MATCH for o in ons.objects(None, p)}
    ctx = rdflib.Graph()
    ontbreekt = []
    for k in cfg.get("externe_kaders") or []:
        mijn = sorted(d for d in doelen if str(d).startswith(k["namespace"]))
        if not mijn:
            continue
        g = bulk(k, werk)
        if g is not None:
            for d in mijn:
                for t in g.triples((d, None, None)):
                    ctx.add(t)
        elif k.get("per_begrip"):
            for d in mijn:
                url = k["per_begrip"].format(uri=urllib.parse.quote(str(d), safe=":/"))
                pad = os.path.join(werk, "extern-" + norm(str(d)[-60:]) + ".ttl")
                if haal(url, pad):
                    try:
                        for t in rdflib.Graph().parse(pad, format="turtle").triples((d, None, None)):
                            ctx.add(t)
                    except Exception as e:
                        print(f"  onleesbaar: {url} ({e.__class__.__name__})")
        print(f"{k['naam']}: {len(mijn)} doelen")
    for d in doelen:
        if (d, RDF.type, SKOS.Concept) not in ctx:
            ontbreekt.append(str(d))
    ctx.serialize(uit, format="turtle")
    print(f"context: {len(ctx)} triples -> {uit}")
    if ontbreekt:
        print(f"NIET GEVONDEN als skos:Concept ({len(ontbreekt)}; geven SHACL-violations):")
        for d in sorted(ontbreekt):
            print("  ", d)


if __name__ == "__main__":
    {"voorstellen": voorstellen, "context": context}[sys.argv[1]](*sys.argv[2:5])
