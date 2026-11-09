"""Optioneel — vergelijk het gegenereerde kader met een gepubliceerd kader. Deterministisch.

Gebruik: python vergelijk.py uit/kader.ttl <gepubliceerd.ttl of URL> uit/vergelijking.csv

Koppelt per gepubliceerd begrip: op URI, op term + definitie, op term (andere definitie),
alleen op definitie, of geen match. Als term telt de prefLabel (of rdfs:label), ook zonder
kwalificatie tussen haakjes ('1 (Bovenbouwcode)' -> '1' en 'bovenbouwcode 1'), en de
skos:notation, altLabels en hiddenLabels van het gepubliceerde begrip. Print tellingen en de lijsten voor het rapport.
"""
import collections
import csv
import html
import re
import sys
import os
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rdflib  # noqa: E402
from rdflib import RDF, RDFS  # noqa: E402
from rdflib.namespace import SKOS  # noqa: E402

from kern import haal  # noqa: E402


def laad(bron):
    g = rdflib.Graph()
    if re.match(r"https?://", bron):
        pad = os.path.join(tempfile.mkdtemp(), "gepubliceerd.ttl")
        if not haal(bron, pad):
            sys.exit(f"Niet op te halen: {bron}")
        g.parse(pad, format="turtle")
    else:
        g.parse(bron)
    return g


def main(ons_pad, pub_bron, uit):
    O, P = laad(ons_pad), laad(pub_bron)
    norm = lambda s: re.sub(r"[\W_]+", "", html.unescape(html.unescape(str(s))).lower())  # noqa: E731
    pc, oc = set(P.subjects(RDF.type, SKOS.Concept)), set(O.subjects(RDF.type, SKOS.Concept))
    idx = collections.defaultdict(set)
    for c in oc:
        for p in (SKOS.prefLabel, SKOS.altLabel, SKOS.notation):
            for l in O.objects(c, p):
                idx[norm(l)].add(c)
                idx[norm(str(l).split(".")[-1])].add(c)
    pdef = {c: norm(P.value(c, SKOS.definition) or "") for c in pc}
    odef = {c: norm(O.value(c, SKOS.definition) or "") for c in oc}
    odef_idx = collections.defaultdict(set)
    for c, d in odef.items():
        odef_idx[d].add(c)
    rows, matched, stats = [], set(), collections.Counter()

    def termen(c):
        """Alle sleutels waarop een gepubliceerd begrip gezocht wordt, in volgorde van voorkeur."""
        uit = []
        for l in list(P.objects(c, SKOS.prefLabel)) + list(P.objects(c, RDFS.label)):
            l = str(l)
            uit.append(l)
            mm = re.fullmatch(r"\s*(.+?)\s*\((.+)\)\s*", l)
            if mm:  # kwalificatie: '1 (Bovenbouwcode)'
                uit += [f"{mm.group(2)} {mm.group(1)}", f"{mm.group(1)} {mm.group(2)}", mm.group(1)]
        for p in (SKOS.notation, SKOS.altLabel, SKOS.hiddenLabel):
            uit += [str(x) for x in P.objects(c, p)]
        return uit

    for c in sorted(pc):
        lab = str(P.value(c, SKOS.prefLabel) or P.value(c, RDFS.label) or c)
        how, m = None, set()
        if c in oc:
            how, m = "URI", {c}
        if not m:
            cand = set()
            for t in termen(c):
                cand = idx.get(norm(t), set())
                if cand and pdef[c] and any(odef[x] == pdef[c] for x in cand):
                    break
            if not cand:
                for t in termen(c):
                    cand = idx.get(norm(t), set())
                    if cand:
                        break
            same = {x for x in cand if odef[x] == pdef[c]}
            if same and pdef[c]:
                how, m = "term+definitie", same
            elif same:
                how, m = "term (beide zonder definitie)", same
            elif cand:
                how, m = "term (andere definitie)", cand
        if not m and pdef[c] and pdef[c] in odef_idx:
            how, m = "alleen definitie", odef_idx[pdef[c]]
        how = how or "geen match"
        stats[how] += 1
        matched |= m
        rows.append([str(c), lab, how, "; ".join(str(O.value(x, SKOS.prefLabel)) for x in m),
                     any(odef[x] == pdef[c] and pdef[c] for x in m) if m else ""])
    with open(uit, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["gepubliceerd", "term gepubliceerd", "match", "ons begrip", "definitie gelijk"])
        w.writerows(rows)

    def tel(g):
        return dict(begrippen=len(set(g.subjects(RDF.type, SKOS.Concept))),
                    collecties=len(set(g.subjects(RDF.type, SKOS.Collection))),
                    topbegrippen=len(set(g.objects(None, SKOS.hasTopConcept)) | set(g.subjects(SKOS.topConceptOf, None))),
                    broader=len(set(g.subject_objects(SKOS.broader))),
                    related=len(set(g.subject_objects(SKOS.related))) // 2,
                    matches=sum(len(set(g.subject_objects(SKOS[p]))) for p in
                                ("exactMatch", "closeMatch", "broadMatch", "narrowMatch", "relatedMatch")),
                    bronnen=len(set(g.subject_objects(rdflib.namespace.DCTERMS.source))))
    print("gepubliceerd:", tel(P))
    print("ons:         ", tel(O))
    print("koppeling:", dict(stats), "| definitie gelijk bij", sum(1 for r in rows if r[4] is True), "van",
          sum(1 for r in rows if r[2] != "geen match"))
    def gegroepeerd(regels):
        """Gelijke regels één keer, met een telling ('transitie (13x)')."""
        for regel, n in collections.Counter(regels).items():
            print("  ", regel + (f"   ({n}x)" if n > 1 else ""))

    geen = [r for r in rows if r[2] == "geen match"]
    print(f"\n== gepubliceerd zonder tegenhanger ({len(geen)}) ==")
    gegroepeerd(f"{r[1]} | {str(P.value(rdflib.URIRef(r[0]), SKOS.definition))[:90]}" for r in geen)
    anders = [r for r in rows if r[2] == "term (andere definitie)"]
    print(f"\n== zelfde term, andere definitie ({len(anders)}) ==")
    gegroepeerd(f"{r[1]} -> {r[3]}" for r in anders)
    rest = sorted(str(O.value(c, SKOS.prefLabel)) for c in oc - matched)
    print(f"\n== ons zonder tegenhanger ({len(rest)}) ==\n  ", rest)
    pl = collections.Counter(norm(P.value(c, SKOS.prefLabel) or "") for c in pc if P.value(c, SKOS.prefLabel))
    print("\ndubbele voorkeurstermen in gepubliceerd kader:", sum(1 for v in pl.values() if v > 1))
    print("collecties met rdfs:label i.p.v. skos:prefLabel (gepubliceerd):",
          sum(1 for c in P.subjects(RDF.type, SKOS.Collection) if not P.value(c, SKOS.prefLabel) and P.value(c, RDFS.label)))


if __name__ == "__main__":
    main(*sys.argv[1:4])
