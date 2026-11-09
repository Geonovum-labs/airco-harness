"""Stap 3 — inventaris.json + keuzes -> NL-SBB-begrippenkader (Turtle). Deterministisch.

Gebruik: python genereer.py werk/inventaris.json project.yaml uit/kader.ttl
Schrijft daarnaast uit/beslissingen.md (log) en uit/termen.tsv (alle termen, voor de LLM-review).

Exitcode 2 = er zijn open beslissingen (bv. waarde met gelijke naam en andere definitie zonder
splitsing). Die staan op stdout; leg ze voor aan de gebruiker, vul project.yaml aan en draai opnieuw.
"""
import csv
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rdflib import RDF, RDFS, Graph, Literal, Namespace, URIRef  # noqa: E402
from rdflib.namespace import DCTERMS as DCT, FOAF, SKOS, XSD  # noqa: E402

from kern import (Termen, bron_tag, clean_def, def_key, herkomst, indeling, laad_inventaris, laad_keuzes,  # noqa: E402
                  local_name, uri)  # noqa: E402

ISOTHES = Namespace("http://purl.org/iso25964/skos-thes#")


def context_term(base, ctx):
    """Attribuutterm met objecttype-context. Is de context een keuze ('afstand of geometrie van de overige
    contour') en is het attribuut een van de alternatieven, dan wordt het 'afstand van de overige contour';
    zonder 'van ...': 'stof bij keuze stof of stofcategorie'. Anders: '{base} {ctx}'."""
    if base.lower() == ctx.lower() or base.lower().endswith(" " + ctx.lower()):
        return base  # 'type scheiding' bij Scheiding: de context staat er al in
    m = re.fullmatch(r"(?P<alt>.+? of .+?)(?P<staart> (?:van|voor|bij|in|op) .+)?", ctx)
    if m and base.lower() in [x.strip().lower() for x in re.split(r",\s*(?:of\s+)?|\s+of\s+", m.group("alt"))]:
        return base + (m.group("staart") or f" bij keuze {ctx}")
    return f"{base} {ctx}"


def main(inv_pad, project, uit):
    cfg = laad_keuzes(project)
    if not cfg["kader"].get("uri"):
        sys.exit("kader.uri ontbreekt in project.yaml")
    inv = laad_inventaris(inv_pad, cfg)
    T = Termen(cfg)
    taal = cfg["kader"].get("taal", "nl")
    log, open_beslissingen = [], []

    def lit(s):
        return Literal(s, lang=taal)

    g = Graph()
    for p, ns in [("skos", SKOS), ("dct", DCT), ("isothes", ISOTHES)]:
        g.bind(p, ns)
    for p, ns in (cfg.get("prefixen") or {}).items():
        g.bind(p, Namespace(ns))
    for k in cfg.get("externe_kaders") or []:
        if k.get("prefix"):
            g.bind(k["prefix"], Namespace(k["namespace"]))

    SCHEME = URIRef(cfg["kader"]["uri"])
    titel = cfg["kader"].get("titel") or "Begrippenkader"
    g.add((SCHEME, RDF.type, SKOS.ConceptScheme))
    g.add((SCHEME, DCT.title, lit(titel)))
    g.add((SCHEME, SKOS.prefLabel, lit(titel)))
    if cfg["kader"].get("omschrijving"):
        g.add((SCHEME, RDFS.comment, lit(cfg["kader"]["omschrijving"])))

    # ---------- bronnen ----------
    bronnen = {}

    def bron(tag):
        url = None
        if tag and re.fullmatch(r"https?://\S+", tag.strip()):
            # herkomst is een URL: brondocument met foaf:page (profiel eist een titel bij het brondocument)
            url = tag.strip()
            r = (local_name(re.sub(r"^https?://(www\.)?", "", url)), url)
        else:
            r = herkomst(tag, cfg)
        if r is None:
            return None
        if r == "ONBEKEND":
            log.append(f"Onbekende herkomst-tag '{tag}', niet als bron opgenomen")
            return None
        key, title = r
        u = URIRef(uri(cfg, "bron", key))
        if key not in bronnen:
            bronnen[key] = u
            g.add((u, DCT.title, lit(title)))
            g.add((u, RDFS.label, lit(title)))
            g.add((u, DCT.bibliographicCitation, Literal(title, datatype=XSD.string)))
            if url:
                g.add((u, FOAF.page, URIRef(url)))
        return u

    # ---------- begrippen ----------
    concepts, used_labels = {}, {}
    soort, notaties = {}, {}

    def concept(label, definition, kind, notation=None, source_tag=None, alt=(), alt_lang=(), toelichting=""):
        u = URIRef(uri(cfg, "begrip", local_name(label)))
        if u in concepts:
            raise SystemExit(f"URI-botsing {u} ({label}); pas termen aan in project.yaml")
        concepts[u] = label
        used_labels[label.lower()] = u
        soort[u], notaties[u] = kind, notation or ""
        g.add((u, RDF.type, SKOS.Concept))
        g.add((u, SKOS.inScheme, SCHEME))
        g.add((u, SKOS.prefLabel, lit(label)))
        d = clean_def(definition)
        if d:
            g.add((u, SKOS.definition, lit(d)))
        else:
            log.append(f"Geen definitie in het model: '{label}' ({notation})")
        if notation:
            g.add((u, SKOS.notation, Literal(notation)))
        t = clean_def(toelichting)
        if t:
            g.add((u, SKOS.scopeNote, lit(t)))
        for a in alt:
            if a and a != label:
                g.add((u, SKOS.altLabel, lit(a)))
        for a, lang in alt_lang:
            g.add((u, SKOS.altLabel, Literal(a, lang=lang)))
        b = bron(source_tag)
        if b:
            g.add((u, DCT.source, b))
        return u

    rel = cfg["relaties"]

    def broader(narrow, broad):
        if rel["generalisatie"] == "geen":
            return
        g.add((narrow, SKOS.broader, broad))
        g.add((broad, SKOS.narrower, narrow))
        if rel["generalisatie"] == "broaderGeneric":
            g.add((narrow, ISOTHES.broaderGeneric, broad))
            g.add((broad, ISOTHES.narrowerGeneric, narrow))

    def related(a, b):
        g.add((a, SKOS.related, b))
        g.add((b, SKOS.related, a))

    obj, dat, codelists, _ = indeling(inv, cfg)
    klassen = {**obj, **dat}
    klassen = {k: inv["elementen"][k] for k in inv["elementen"] if k in klassen}  # inventarisvolgorde
    ext_namen = inv.get("externe_klassen") or {}
    term_lang = cfg["termen"].get("alias_naam_als_altlabel")
    alias_st0 = {s.lower() for s in cfg["termen"].get("alias_als_voorkeursterm") or []}

    def eigen_term(el):
        """Voorkeursterm uit het model zelf: tag (termen.term_tag) of alias (alias_als_voorkeursterm)."""
        if el["name"].strip().lower() in T.vast:
            return T.vast[el["name"].strip().lower()]
        if el.get("term"):
            return el["term"].strip()
        if el.get("alias") and ("*" in alias_st0 or (el.get("stereo") or "").lower() in alias_st0):
            return el["alias"].strip()
        return None
    genegeerd = defaultdict(int)
    for c in inv["elementen"].values():
        for el in [c] + c["attrs"]:
            for kop in el.get("secties_genegeerd") or []:
                genegeerd[kop] += 1
    for kop, n in sorted(genegeerd.items()):
        log.append(f"Notitiesectie '--{kop}--' niet overgenomen ({n}x); voeg toe aan definities.sectie_* om te gebruiken")

    # 1. objecttypen en datatypen
    alias_st = {s.lower() for s in cfg["termen"].get("alias_als_voorkeursterm") or []}
    alias_lang = cfg["termen"].get("alias_naam_als_altlabel")
    cls_uri = {}
    for k, c in klassen.items():
        alt_lang = []
        if c["name"].strip().lower() in T.vast:
            label = T.vast[c["name"].strip().lower()]
        elif c.get("term"):
            label = c["term"]
            if term_lang:
                alt_lang = [(c["name"], term_lang)]
        elif c["alias"] and ("*" in alias_st or (c["stereo"] or "").lower() in alias_st):
            label = T.humanize(c["alias"])
            if alias_lang and c["name"].lstrip("_") != label:
                alt_lang = [(c["name"].lstrip("_"), alias_lang)]
        else:
            label = T.humanize(c["name"])
        cls_uri[k] = concept(label, c["doc"], "datatype" if k in dat else "objecttype", notation=c["name"],
                             source_tag=bron_tag(c, cfg), alt_lang=alt_lang, toelichting=c.get("toelichting", ""))

    # generalisaties
    by_name = {c["name"]: k for k, c in klassen.items()}
    wortel = by_name.get(rel.get("wortel")) if rel.get("wortel") else None
    if rel.get("wortel") and wortel is None:
        sys.exit(f"relaties.wortel '{rel['wortel']}' bestaat niet in het model")
    zelfstandig = {by_name[n] for n in rel.get("zelfstandig") or [] if n in by_name}
    tops = []
    for k, c in klassen.items():
        supers = [gid for gid in c["gens"] if gid in klassen and gid != k]
        if not supers and k != wortel and k not in dat and k not in zelfstandig:
            tgt = None
            if rel.get("externe_superklasse_op_naam", True):
                tgt = next((by_name[ext_namen[gid]] for gid in c["gens"]
                            if ext_namen.get(gid) in by_name and by_name[ext_namen[gid]] != k), None)
            if tgt:
                supers.append(tgt)
            elif wortel:
                supers.append(wortel)
            else:
                tops.append(k)
        for s in supers:
            broader(cls_uri[k], cls_uri[s])
    tops += ([wortel] if wortel else []) + sorted(zelfstandig) + (list(dat) if rel.get("datatypen_topbegrip", True) else [])
    for t in dict.fromkeys(tops):
        g.add((SCHEME, SKOS.hasTopConcept, cls_uri[t]))
        g.add((cls_uri[t], SKOS.topConceptOf, SCHEME))

    # 2. attributen
    ac = cfg["attributen"]
    attr_uri = defaultdict(list)  # (klasse, attribuut) -> uri
    if cfg["scope"].get("attributen", True):
        ctx_always = set(ac.get("context_altijd") or [])
        groups = defaultdict(list)
        for k, c in klassen.items():
            for a in c["attrs"]:
                key = def_key(a["doc"]) if ac.get("samenvoegen") == "naam_en_definitie" else k
                groups[(a["name"], key)].append((k, a))
        base_count = defaultdict(set)
        for (name, dk), lst in groups.items():
            base_count[eigen_term(lst[0][1]) or T.humanize(name)].add(dk)
        class_labels = {concepts[u].lower() for u in cls_uri.values()}
        corr = ac.get("term_correcties") or {}
        for (name, dk), lst in sorted(groups.items()):
            base = corr.get(name) or eigen_term(lst[0][1]) or T.humanize(name)
            if name in corr:
                log.append(f"Attribuut '{name}': voorkeursterm '{base}' via term_correcties; notatie ongewijzigd")
            first = lst[0][0]
            ctx = concepts[cls_uri[first]]
            needs = (base in ctx_always
                     or (ac.get("context_bij_dubbele_naam", True)
                         and len(base_count[eigen_term(lst[0][1]) or T.humanize(name)]) > 1)
                     or (ac.get("context_bij_botsing_met_klasse", True) and base.lower() in class_labels))
            label = context_term(base, ctx) if needs else base
            for p, v in (ac.get("prefix_term") or {}).items():
                if name.startswith(p):
                    label = v + label
                    break
            if label.lower() in used_labels and label != ctx:
                # botsing: de context nog eens achterplakken geeft 'type scheiding scheiding'. Onderscheid dan
                # op het verwijderde UML-prefix ('type scheiding (plus)'), anders pas op de context.
                pref = next((p for p in T.prefixen if name.startswith(p)), None)
                if pref:
                    label = f"{label} ({pref.strip('-_ ')})"
                elif not label.lower().endswith(ctx.lower()):
                    label = f"{label} {ctx}"
                else:
                    label = f"{label} ({klassen[first]['name']}.{name})"
                log.append(f"Attribuut '{klassen[first]['name']}.{name}': term botste met een ander begrip; "
                           f"wordt '{label}' (aanpassen met attributen.term_correcties['{klassen[first]['name']}.{name}'])")
            vol = next((corr[f"{klassen[k]['name']}.{name}"] for k, _ in lst if f"{klassen[k]['name']}.{name}" in corr), None)
            if vol:  # term_correcties met sleutel Klasse.attribuut: volledige term, zonder contextregel
                label = vol
                log.append(f"Attribuut '{klassen[first]['name']}.{name}': voorkeursterm '{vol}' via term_correcties")
            elif re.search(r"\b(\w+) \1\b", label):
                log.append(f"Attribuut '{klassen[first]['name']}.{name}': term '{label}' bevat een herhaald woord; "
                           f"corrigeer eventueel met attributen.term_correcties['{klassen[first]['name']}.{name}']")
            a = lst[0][1]
            u = concept(label, a["doc"], "attribuut",
                        notation=ac["notatie"].format(klasse=klassen[first]["name"], attribuut=name),
                        source_tag=bron_tag(a, cfg), toelichting=a.get("toelichting", ""),
                        alt=[name] if name != label and not (eigen_term(a) and term_lang) else [],
                        alt_lang=[(name, term_lang)] if eigen_term(a) and term_lang and name != label else [])
            for k, _ in lst:
                if rel.get("attribuut_objecttype") == "related":
                    related(u, cls_uri[k])
                attr_uri[(klassen[k]["name"], name)].append(u)
            if len(lst) > 1:
                log.append(f"Attribuut '{name}' komt met dezelfde definitie voor in "
                           f"{', '.join(klassen[k]['name'] for k, _ in lst)}: één begrip")

    # 3. waarden uit waardelijsten
    wc = cfg["waarden"]
    split = {k.lower(): v for k, v in (wc.get("splitsingen") or {}).items()}
    hernoem = {k.lower(): v for k, v in (wc.get("hernoem") or {}).items()}
    val_groups = defaultdict(list)
    split_orig = defaultdict(set)
    for k, c in codelists.items():
        for a in c["attrs"]:
            nm = a["name"].strip()
            lab = split.get(f"{nm.lower()}|{c['name'].lower()}")
            if lab is not None:
                split_orig[lab].add(T.waarde(nm))
            else:
                lab = hernoem.get(nm.lower()) or eigen_term(a) or T.waarde(nm)
            key = lab if wc.get("samenvoegen") == "naam_en_definitie" else (lab, c["name"])
            val_groups[key].append((k, a))

    # automatisch splitsen (waarden.automatisch_splitsen = patroon met {waarde} en {lijst})
    auto = wc.get("automatisch_splitsen")
    zelfde = {z.lower() for z in wc.get("zelfde_begrip") or []}
    if auto:
        for key in list(val_groups):
            lst = val_groups[key]
            lab = key if isinstance(key, str) else key[0]
            if lab.lower() in zelfde or len({def_key(a["doc"]) for _, a in lst}) < 2:
                continue
            del val_groups[key]
            for k, a in lst:
                nieuw = auto.format(waarde=lab, lijst=T.humanize(codelists[k]["name"]))
                split_orig[nieuw].add(lab)
                val_groups[nieuw if isinstance(key, str) else (nieuw, key[1])].append((k, a))
            log.append(f"Waarde '{lab}': verschillende definities per lijst; automatisch gesplitst volgens '{auto}'")

    val_uri = {}
    for key, lst in sorted(val_groups.items(), key=lambda kv: str(kv[0])):
        lab = key if isinstance(key, str) else key[0]
        keys = {def_key(a["doc"]) for _, a in lst}
        variants = {clean_def(a["doc"]) for _, a in lst}
        if lab.lower() in zelfde and len(keys) > 1:
            from collections import Counter
            d0 = Counter(clean_def(a["doc"]) for _, a in lst).most_common(1)[0][0]
            log.append(f"Waarde '{lab}': {len(keys)} definitievarianten samengevoegd (waarden.zelfde_begrip); "
                       f"definitie = meest voorkomende variant")
            keys, variants = {def_key(d0)}, {d0}
        if len(keys) > 1 or (len(variants) > 1 and not wc.get("leestekenverschil_samenvoegen", True)):
            open_beslissingen.append(
                f"Waarde '{lab}' heeft verschillende definities in: " + "; ".join(
                    f"{codelists[k]['name']}: \"{clean_def(a['doc'])[:120]}\"" for k, a in lst))
            continue
        if len(variants) > 1:
            log.append(f"Waarde '{lab}': definities verschilden alleen in leestekens/entiteiten; samengevoegd")
        d = sorted(variants, key=lambda s: (not s.endswith("."), ";" in s, len(s)))[0]
        label = lab
        if label.lower() in used_labels:
            label = f"{label}{wc.get('botsing_achtervoegsel', ' waarde')}"
            log.append(f"Waarde '{lab}' botst met bestaand begrip; voorkeursterm '{label}'")
        names = sorted({a["name"].strip() for _, a in lst})
        k0, a0 = lst[0]
        nt = a0["tags"].get(wc["notatie_tag"]) if wc.get("notatie_tag") else None
        u = concept(label, d, "waarde", notation=nt or None,
                    source_tag=bron_tag(a0, cfg) or bron_tag(codelists[k0], cfg), toelichting=a0.get("toelichting", ""),
                    alt=[n for n in names if n.lower() != label.lower()] + sorted(split_orig.get(lab, ())))
        for k, a in lst:
            val_uri[(k, a["name"].strip())] = u
        if len(lst) > 1:
            log.append(f"Waarde '{label}' staat in {len(lst)} waardelijsten: "
                       f"{', '.join(codelists[k]['name'] for k, _ in lst)}")

    if open_beslissingen:
        print("OPEN BESLISSINGEN (voeg waarden.splitsingen toe in project.yaml of kies waarden.samenvoegen: nooit):")
        for b in open_beslissingen:
            print("  -", b)
        sys.exit(2)

    # collecties per waardelijst
    cl_by_name = {c["name"]: k for k, c in codelists.items()}
    if cfg["collecties"].get("per_waardelijst", True):
        for k, c in codelists.items():
            if not c["attrs"]:
                log.append(f"Waardelijst '{c['name']}' heeft geen waarden in het model (extern beheerd?"
                           f"{' Locatie: ' + c['tags']['Locatie'] if c['tags'].get('Locatie') else ''}); geen collectie")
                continue
            cnaam = c["name"] if re.fullmatch(r"[\w.-]+", c["name"], re.A) else local_name(c["name"])
            cu = URIRef(uri(cfg, "collectie", cnaam))
            g.add((cu, RDF.type, SKOS.Collection))
            g.add((cu, SKOS.prefLabel, lit(T.humanize(c["name"]))))
            g.add((cu, SKOS.notation, Literal(c["name"])))
            d = clean_def(c["doc"])
            if d:
                g.add((cu, RDFS.comment, lit(d)))
            for a in c["attrs"]:
                g.add((cu, SKOS.member, val_uri[(k, a["name"].strip())]))

    # waarde -> attribuut (of objecttype)
    gebruik = defaultdict(list)
    for k, c in klassen.items():  # automatisch: attribuuttype = waardelijst
        for a in c["attrs"]:
            if a.get("type") in cl_by_name:
                gebruik[a["type"]].append((c["name"], a["name"]))
    cfg_gebruik = rel.get("gebruik") or {}
    for k, c in codelists.items():
        if not c["attrs"]:
            continue
        if c["name"] in cfg_gebruik:
            use = cfg_gebruik[c["name"]]
            targets = [] if use is None else [tuple(use)]
            if use is None:
                log.append(f"Waardelijst '{c['name']}' wordt in het model door geen attribuut gebruikt; waarden niet gerelateerd")
        elif gebruik.get(c["name"]):
            targets = gebruik[c["name"]]
        else:
            log.append(f"Waardelijst '{c['name']}' heeft geen gebruik-koppeling; waarden niet gerelateerd")
            continue
        if rel.get("waarde_attribuut") != "related":
            continue
        for cls_name, attr in targets:
            if attr is None:
                if cls_name not in by_name:
                    sys.exit(f"relaties.gebruik: klasse '{cls_name}' bestaat niet")
                tgts = [cls_uri[by_name[cls_name]]]
                log.append(f"Waardelijst '{c['name']}': geen attribuut in het model; "
                           f"waarden related aan objecttype '{concepts[tgts[0]]}'")
            else:
                tgts = attr_uri.get((cls_name, attr))
                if not tgts:
                    sys.exit(f"relaties.gebruik: attribuut '{cls_name}.{attr}' bestaat niet")
            for t in tgts:
                for a in c["attrs"]:
                    related(val_uri[(k, a["name"].strip())], t)

    # bovenliggende waarden via tagged value (bv. Plus-waarde -> BGT-waarde)
    ptag, psep = rel.get("waarde_parent_tag"), rel.get("parent_scheiding") or ";"
    if ptag:
        for k, c in codelists.items():
            parent_list = (c["tags"].get(ptag) or "").strip()
            for a in c["attrs"]:
                for p in [x.strip() for x in (a["tags"].get(ptag) or "").split(psep) if x.strip()]:
                    cands = [pk for pk in ([cl_by_name[parent_list]] if parent_list in cl_by_name else codelists)
                             if (pk, p) in val_uri]
                    if not cands:
                        cands = [pk for pk in codelists if (pk, p) in val_uri]
                    if not cands:
                        log.append(f"Parent '{p}' van '{a['name']}' ({c['name']}) niet gevonden")
                        continue
                    child, par = val_uri[(k, a["name"].strip())], val_uri[(cands[0], p)]
                    if child != par:
                        broader(child, par)

    # ---------- harmonisatierelaties ----------
    lab2uri = {lab: u for u, lab in concepts.items()}
    for m in cfg.get("matches") or []:
        if m["term"] not in lab2uri:
            log.append(f"Match niet gelegd: begrip '{m['term']}' bestaat niet")
            continue
        g.add((lab2uri[m["term"]], SKOS[m["relatie"]], URIRef(m["uri"])))

    os.makedirs(os.path.dirname(os.path.abspath(uit)), exist_ok=True)
    g.serialize(uit, format="turtle")
    basis = os.path.dirname(os.path.abspath(uit))
    with open(os.path.join(basis, "beslissingen.md"), "w") as f:
        f.write("# Beslissingen en afwijkingen (genereer.py)\n\n" + "\n".join(f"- {l}" for l in log) + "\n")
    with open(os.path.join(basis, "termen.tsv"), "w", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["soort", "voorkeursterm", "notatie", "altLabels", "definitie", "uri"])
        for u, lab in sorted(concepts.items(), key=lambda kv: (soort[kv[0]], kv[1].lower())):
            w.writerow([soort[u], lab, notaties[u],
                        " | ".join(f"{a}@{a.language}" for a in g.objects(u, SKOS.altLabel)),
                        str(g.value(u, SKOS.definition) or ""), str(u)])
    tel = defaultdict(int)
    for s in soort.values():
        tel[s] += 1
    print(f"begrippen: {len(concepts)} ({', '.join(f'{k} {v}' for k, v in sorted(tel.items()))}); "
          f"collecties {sum(1 for c in codelists.values() if c['attrs'])}; topbegrippen {len(set(tops))}; bronnen {len(bronnen)}; "
          f"matches {len(cfg.get('matches') or [])}; triples {len(g)}")
    print(f"log: {len(log)} regels in beslissingen.md; termen in termen.tsv")


if __name__ == "__main__":
    main(*sys.argv[1:4])
