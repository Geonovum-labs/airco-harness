"""Stap 1 — XMI (UML) -> inventaris.json. Deterministisch, geen keuzes.

Gebruik: python inventaris.py model.xmi werk/inventaris.json [--package NAAM ...] [--zonder NAAM ...]

Ondersteunt XMI 2.x én XMI 1.1 (UML 1.3, de 'Enterprise Architect XMI/UML 1.3'-export die
in het Geonovum-register veel voorkomt). --package (herhaalbaar, inclusief subpackages)
beperkt de omzetting tot die packages; de rest telt als externe klassen. Een naam mag een pad
zijn (`Ouder/Kind`); --zonder sluit (sub)packages uit. Bij een XMI 1.1-
export met meerdere modellen (bv. ook NEN 3610, ISO, MIM-datatypen) toont het script zonder
--package de packageboom en stopt het (exitcode 1).

Leest klassen, datatypen, waardelijsten (codelists/enumeraties), attributen, literals,
generalisaties, stereotypen, aliassen, definities en tagged values. Ondersteunt
Enterprise Architect (xmi:Extension) en generieke UML-XMI (ownedComment, ownedLiteral,
stereotype-applicaties met base_Class/base_Property). XMI- en UML-namespaceversies
worden automatisch herkend.
"""
import argparse
import json
import re
import sys
from collections import Counter

from lxml import etree


def local(tag):
    return tag.split("}", 1)[-1] if isinstance(tag, str) else ""


def tagwaarde(v):
    """EA zet na '#NOTES#' de beschrijving van de tag; bij memo-tags ('<memo>#NOTES#tekst') is dat de waarde."""
    v = v or ""
    if v.startswith("<memo>#NOTES#"):
        return v[len("<memo>#NOTES#"):]
    return v.split("#NOTES#")[0]


def past(pad, naam):
    """Package-pad eindigt op 'naam' (een naam of een pad als 'Ouder/Kind')."""
    delen = naam.strip("/").split("/")
    return list(pad[-len(delen):]) == delen


def gekozen_pad(pad, packages, zonder):
    """Valt een package-pad binnen de keuze (een prefix past op --package, geen prefix op --zonder)?"""
    pre = [pad[:n] for n in range(1, len(pad) + 1)]
    return any(past(p, n) for p in pre for n in packages) and not any(past(p, n) for p in pre for n in zonder)


def eaid(guid):
    return "EAID_" + (guid or "").strip("{}").replace("-", "_")


UMLTYPE11 = {"Class": "uml:Class", "Enumeration": "uml:Enumeration", "DataType": "uml:DataType",
             "Interface": "uml:Interface"}


def xmi11(root, packages, zonder=()):
    """XMI 1.1 / UML 1.3 (Enterprise Architect). Definities en eigenschappen staan in tagged values."""
    U = "{omg.org/UML1.3}"

    def tags(el):
        tv = el.find(U + "ModelElement.taggedValue")
        return {} if tv is None else {t.get("tag"): (t.get("value") or "") for t in tv.findall(U + "TaggedValue")}

    def eigen_tags(el):
        """Door de gebruiker gedefinieerde tagged values hebben een xmi.id; EA-interne niet."""
        tv = el.find(U + "ModelElement.taggedValue")
        return {} if tv is None else {t.get("tag"): memo11(t) for t in tv.findall(U + "TaggedValue") if t.get("xmi.id")}

    def memo11(t):
        """XMI 1.1: bij memo-tags staat de tekst in XMI.extension/UML:Comment@name."""
        v = tagwaarde(t.get("value"))
        if v == "<memo>":
            c = t.find("XMI.extension/" + U + "Comment")
            if c is not None and c.get("name") and not re.match(r"\s*(Default|Description):", c.get("name")):
                return c.get("name").strip()
        return v

    def stereo(el, tg):
        st = el.find(U + "ModelElement.stereotype/" + U + "Stereotype")
        return tg.get("stereotype") or (st.get("name") if st is not None else None) or None

    pkgs = []      # (pad, element) in documentvolgorde
    elems, gens, refs = {}, [], {}

    def walk(el, path, gekozen):
        for ns in el.findall(U + "Namespace.ownedElement"):
            for c in ns:
                t = local(c.tag)
                if t == "Package":
                    p = path + [c.get("name")]
                    pkgs.append(p)
                    walk(c, p, gekozen_pad(p, packages, zonder) if packages else True)
                elif t in ("Class", "DataType", "Interface", "Enumeration") and c.get("name"):
                    tg = tags(c)
                    ty = UMLTYPE11.get(tg.get("ea_stype"), "uml:" + t if "uml:" + t in UMLTYPE11.values() else None)
                    if ty is None or c.get("name") == "EARootClass":
                        continue
                    st = stereo(c, tg)
                    if (st or "").lower() == "enumeration":  # EA exporteert enumeraties als Class «enumeration»
                        ty, st = "uml:Enumeration", None
                    i = c.get("xmi.id")
                    refs[i] = c.get("name")
                    if not gekozen:
                        continue
                    attrs = []
                    for a in c.findall(U + "Classifier.feature/" + U + "Attribute"):
                        at = tags(a)
                        tref = a.find(U + "StructuralFeature.type/" + U + "Classifier")
                        tid = tref.get("xmi.idref") if tref is not None else None
                        attrs.append(dict(id=eaid(at.get("ea_guid")), name=a.get("name") or "",
                                          doc=at.get("description", ""),
                                          type_id=tid if tid and not tid.startswith("eaxmiid") else None,
                                          type=at.get("type") or None, stereo=stereo(a, at),
                                          lower=at.get("lowerBound"), upper=at.get("upperBound"),
                                          tags=eigen_tags(a),
                                          alias=at.get("style") or None, _pos=int(at.get("position") or 0)))
                    attrs.sort(key=lambda a: (a.pop("_pos"), a["name"]))
                    elems[i] = dict(name=c.get("name"), type=ty, doc=tg.get("documentation", ""),
                                    alias=tg.get("alias") or None, stereo=st,
                                    pkg=path[-1] if path else None, pkg_path=path,
                                    abstract=c.get("isAbstract") == "true",
                                    tags=eigen_tags(c), attrs=attrs, gens=[],
                                    _tpos=int(tg.get("tpos") or 0))
                elif t == "Generalization":
                    gens.append((c.get("subtype"), c.get("supertype")))
    model = root.find("XMI.content/" + U + "Model")
    walk(model if model is not None else root, [], not packages)
    # tagged values die EA los onder XMI.content zet, met een verwijzing naar het element
    for tv in root.iter(U + "TaggedValue"):
        me = tv.get("modelElement")
        if me in elems and tv.get("tag"):
            elems[me]["tags"].setdefault(tv.get("tag"), tagwaarde(tv.get("value")))
    for el in root.iter(U + "Generalization"):
        g = (el.get("subtype"), el.get("supertype"))
        if g not in gens:
            gens.append(g)
    return pkgs, elems, gens, refs


def main_xmi11(root, src, out, packages, zonder):
    pkgs, elems, gens, refs = xmi11(root, packages, zonder)
    if not packages:
        print("Kies met --package welke package(s) worden omgezet. Packageboom (aantal klassen):")
        for p in pkgs:
            print("  " * (len(p) - 1) + p[-1])
        sys.exit(1)
    if not elems:
        sys.exit(f"Geen klassen gevonden in package(s) {packages}")
    # volgorde zoals EA: packageboom, dan tpos en naam (gelijk aan inventaris_eap.py)
    prang = {tuple(p): n for n, p in enumerate(pkgs)}
    elems = {k: elems[k] for k in sorted(elems, key=lambda k: (prang.get(tuple(elems[k]["pkg_path"]), 1e9),
                                                               elems[k]["_tpos"], elems[k]["name"]))}
    externe = {}
    for sub, sup in gens:
        if sub in elems:
            elems[sub]["gens"].append(sup)
            if sup not in elems and sup in refs:
                externe[sup] = refs[sup]
    for c in elems.values():
        c.pop("_tpos")
        for a in c["attrs"]:
            if a["type_id"] and a["type_id"] not in elems and a["type_id"] in refs:
                externe.setdefault(a["type_id"], refs[a["type_id"]])
    return elems, externe


def main(src, out, packages=(), zonder=()):
    tree = etree.parse(src)
    root = tree.getroot()
    if root.tag == "XMI" and root.get("xmi.version", "").startswith("1."):
        elems, externe = main_xmi11(root, src, out, list(packages), list(zonder))
        schrijf(src, out, elems, externe)
        return
    XMI = root.nsmap.get("xmi") or next(
        (v for v in root.nsmap.values() if v and "XMI" in v), "http://www.omg.org/spec/XMI/20131001")
    X = "{%s}" % XMI
    model = next((e for e in root.iter() if local(e.tag) == "Model"), root)

    elems = {}   # id -> klasse/datatype/enumeratie
    props = {}   # id van attribuut -> (klasse-id, index)

    def comment(el):
        return " ".join((c.get("body") or (c.findtext("body") or "")).strip()
                        for c in el.findall("ownedComment")).strip()

    def walk(el, pkg_path):
        for c in el:
            if local(c.tag) != "packagedElement":
                continue
            t = c.get(X + "type")
            if t == "uml:Package":
                walk(c, pkg_path + [c.get("name")])
            elif t in ("uml:Class", "uml:Enumeration", "uml:DataType", "uml:Interface") and c.get("name"):
                # naamloze klassen zijn tekenhulpmiddelen (bv. EA-boundaries)
                i = c.get(X + "id")
                attrs = []
                for a in c.findall("ownedAttribute"):
                    if a.get("association") is not None:
                        continue
                    ty = a.find("type")
                    attrs.append(dict(id=a.get(X + "id"), name=a.get("name") or "", doc=comment(a),
                                      type_id=(ty.get(X + "idref") if ty is not None else a.get("type")),
                                      type=None, stereo=None, lower=None, upper=None, tags={}, alias=None))
                for lit in c.findall("ownedLiteral"):
                    attrs.append(dict(id=lit.get(X + "id"), name=lit.get("name") or "", doc=comment(lit),
                                      type_id=None, type=None, stereo=None, lower=None, upper=None,
                                      tags={}, alias=None))
                elems[i] = dict(name=c.get("name") or "", type=t, doc=comment(c), alias=None, stereo=None,
                                pkg=pkg_path[-1] if pkg_path else None, pkg_path=pkg_path,
                                abstract=c.get("isAbstract") == "true", tags={}, attrs=attrs,
                                gens=[g.get("general") for g in c.findall("generalization")])
                for n, a in enumerate(attrs):
                    props[a["id"]] = (i, n)
    walk(model, [])

    # stereotype-applicaties buiten het model (generieke XMI-profielen)
    for e in root:
        for base in ("base_Class", "base_Property", "base_Enumeration", "base_DataType", "base_EnumerationLiteral"):
            ref = e.get(base)
            if ref in elems and not elems[ref]["stereo"]:
                elems[ref]["stereo"] = local(e.tag)
            elif ref in props:
                ci, n = props[ref]
                elems[ci]["attrs"][n]["stereo"] = elems[ci]["attrs"][n]["stereo"] or local(e.tag)

    externe_klassen = {}
    ext = root.find(X + "Extension")
    if ext is not None:  # Enterprise Architect
        def tagdict(el):
            def w(t):
                v, n = tagwaarde(t.get("value")), (t.get("notes") or "").strip()
                # memo-tag: tekst in @notes (tenzij dat de beschrijving van de tag is)
                return n if v == "<memo>" and n and not re.match(r"(Default|Description):", n) else v
            return {t.get("name"): w(t) for t in el.findall("tags/tag")}

        for e in ext.findall("elements/element"):
            i = e.get(X + "idref")
            if i not in elems:
                continue
            c = elems[i]
            p = e.find("properties")
            if p is not None:
                c["doc"] = p.get("documentation") or c["doc"]
                c["alias"] = p.get("alias") or None
                c["stereo"] = p.get("stereotype") or c["stereo"]
                c["abstract"] = c["abstract"] or p.get("isAbstract") == "true"
            ep = e.find("extendedProperties")
            if ep is not None and ep.get("package_name"):
                c["pkg"] = ep.get("package_name")
            c["tags"] = tagdict(e)
            by_id = {a["id"]: a for a in c["attrs"]}
            for a in e.findall("attributes/attribute"):
                tgt = by_id.get(a.get(X + "idref"))
                if tgt is None:
                    continue
                d, pr, st, b, sty = (a.find(x) for x in ("documentation", "properties", "stereotype", "bounds", "style"))
                if d is not None and d.get("value"):
                    tgt["doc"] = d.get("value")
                if pr is not None:
                    tgt["type"] = pr.get("type")
                if st is not None:
                    tgt["stereo"] = st.get("stereotype")
                if b is not None:
                    tgt["lower"], tgt["upper"] = b.get("lower"), b.get("upper")
                if sty is not None:
                    tgt["alias"] = sty.get("value") or None
                tgt["tags"] = tagdict(a)
        # volgorde van EA aanhouden (bepaalt welke klasse 'eerste' is bij gedeelde attributen)
        pos = {e.get(X + "idref"): n for n, e in enumerate(ext.findall("elements/element"))}
        elems = {k: elems[k] for k in sorted(elems, key=lambda k: pos.get(k, len(pos)))}
        # namen van klassen buiten het model (bv. CityGML-superklassen) uit connectoren
        for con in ext.findall("connectors/connector"):
            for end in ("source", "target"):
                n = con.find(end)
                if n is None:
                    continue
                ref, m = n.get(X + "idref"), n.find("model")
                if ref and ref not in elems and m is not None and m.get("name"):
                    externe_klassen[ref] = m.get("name")

    # attribuuttypen oplossen naar namen
    for c in elems.values():
        for a in c["attrs"]:
            if not a["type"] and a["type_id"] in elems:
                a["type"] = elems[a["type_id"]]["name"]
            elif not a["type"] and a["type_id"] in externe_klassen:
                a["type"] = externe_klassen[a["type_id"]]

    if packages:
        keep = {k for k, c in elems.items() if gekozen_pad(c["pkg_path"], packages, zonder)}
        for k in list(elems):
            if k not in keep:
                externe_klassen[k] = elems.pop(k)["name"]
        if not elems:
            sys.exit(f"Geen klassen gevonden in package(s) {list(packages)}")
    schrijf(src, out, elems, externe_klassen)


def schrijf(src, out, elems, externe_klassen):
    json.dump(dict(bron=src, elementen=elems, externe_klassen=externe_klassen),
              open(out, "w"), ensure_ascii=False, indent=1)
    print(f"{len(elems)} elementen, {sum(len(c['attrs']) for c in elems.values())} attributen/waarden, "
          f"{len(externe_klassen)} externe klassen")
    for (t, s), n in sorted(Counter((c["type"], c["stereo"]) for c in elems.values()).items(), key=str):
        print(f"  {t:16} {str(s):20} {n}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("bron")
    ap.add_argument("uit")
    ap.add_argument("--package", action="append", default=[])
    ap.add_argument("--zonder", action="append", default=[])
    a = ap.parse_args()
    main(a.bron, a.uit, a.package, a.zonder)
