"""The reference model as two files in reference-models/<standard>/.

    model.mim.xml   object types, data types, codelists and relations in MIM-XML 1.1.1
    codelists.ttl   one SKOS concept scheme per codelist, following NL-SBB

`read` returns the dict that `refmodel.generate` builds, so the files carry the
whole reference model. A Codelijst in MIM-XML has no values; its `locatie` is
the URI of its concept scheme. Required MIM metadata that the source model
leaves empty is written as an empty element, as the MIM sample models do.
"""

from __future__ import annotations

import re
from pathlib import Path

from lxml import etree
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, RDF, SKOS

NS = {
    "mim": "http://www.geostandaarden.nl/mim/mim-core/1.1",
    "mim-ref": "http://www.geostandaarden.nl/mim/mim-ref/1.0",
    "xlink": "http://www.w3.org/1999/xlink",
    "xhtml": "http://www.w3.org/1999/xhtml",
}
REGISTER_BASE = "http://definities.geostandaarden.nl/imgeo/id/begrip/"
FILES = ("model.mim.xml", "codelists.ttl")
# Fields of a dict attribute that the MIM element for it may not carry, with the value they then have.
ATTRIBUTE_DEFAULTS = {
    "authentic": None, "material_history": False, "formal_history": False, "possibly_no_value": False,
    "origin": None, "definition": "", "origin_definition": None, "date_added": None, "classifying": False, "derivable": False,
}  # fmt: skip


def namespace(standard: str) -> Namespace:
    """Namespace for URIs the harness mints, such as concept schemes; not an official publication."""
    return Namespace(f"urn:airco-harness:{standard}:")


def local_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]", "_", name)


def scheme_uri(standard: str, codelist: str) -> URIRef:
    return namespace(standard)[local_name(f"list_{codelist}")]


def value_uri(standard: str, codelist: str, value: str) -> URIRef:
    return namespace(standard)[local_name(f"{codelist}_{value}")]


def paths(directory: Path) -> dict[str, Path]:
    return {name: directory / name for name in FILES}


def write(model: dict, directory: Path) -> dict[str, Path]:
    files = paths(directory)
    files["model.mim.xml"].write_bytes(to_mim_xml(model))
    files["codelists.ttl"].write_text(to_skos(model), encoding="utf-8")
    return files


def read(directory: Path) -> dict:
    """The reference model of the standard that the folder is named after."""
    files = paths(directory)
    model = {"standard": directory.name, **from_mim_xml(files["model.mim.xml"].read_bytes())}
    values = codelist_values(files["codelists.ttl"].read_text(encoding="utf-8"))
    for entry in model["domains"].values():
        entry["values"] = values[entry.pop("scheme")]
    return model


# MIM-XML


def _q(tag: str) -> str:
    prefix, _, local = tag.partition(":")
    return f"{{{NS[prefix]}}}{local}"


def _add(parent: etree._Element, tag: str, value: str | bool | None = None, **attrib: str) -> etree._Element:
    el = etree.SubElement(parent, _q(tag), attrib)
    if isinstance(value, bool):
        el.text = "true" if value else "false"
    elif value:
        el.text = value
    return el


def _definition(parent: etree._Element, text: str) -> None:
    el = _add(parent, "mim:definitie")
    if text:
        _add(_add(el, "xhtml:body"), "xhtml:p", text)


def _id(stereotype: str, name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", f"{stereotype} {name}".lower()).strip("-")


class _Writer:
    def __init__(self, model: dict):
        self.model = model
        self.stereotypes = {name: e["stereotype"] for group in ("object_types", "data_types", "domains") for name, e in model[group].items()}

    def ref(self, parent: etree._Element, tag: str, name: str) -> None:
        _add(parent, tag, name).set(_q("xlink:href"), f"#{_id(self.stereotypes[name], name)}")

    def type(self, parent: etree._Element, name: str) -> None:
        el = _add(parent, "mim:type")
        stereotype = self.stereotypes.get(name)
        if stereotype == "Keuze":
            self.ref(el, "mim-ref:KeuzeRef", name)
        elif stereotype in ("Codelijst", "Gestructureerd datatype"):
            self.ref(el, "mim-ref:DatatypeRef", name)
        else:
            _add(el, "mim:Datatype", name)

    def attributes(self, parent: etree._Element, attributes: dict) -> None:
        """Attribuutsoorten, and Gegevensgroepen for attributes whose type is a Gegevensgroeptype."""
        plain = {n: a for n, a in attributes.items() if self.stereotypes.get(a["type"]) != "Gegevensgroeptype"}
        groups = {n: a for n, a in attributes.items() if n not in plain}
        if plain:
            container = _add(parent, "mim:attribuutsoorten")
            for name, a in plain.items():
                el = _add(container, "mim:Attribuutsoort")
                _add(el, "mim:naam", name)
                _add(el, "mim:herkomst", a["origin"])
                _definition(el, a["definition"])
                _add(el, "mim:herkomstDefinitie", a["origin_definition"])
                _add(el, "mim:datumOpname", a["date_added"])
                self.type(el, a["type"])
                _add(el, "mim:indicatieMaterieleHistorie", a["material_history"])
                _add(el, "mim:indicatieFormeleHistorie", a["formal_history"])
                _add(el, "mim:kardinaliteit", a["cardinality"])
                _add(el, "mim:authentiek", a["authentic"])
                _add(el, "mim:indicatieAfleidbaar", a["derivable"])
                _add(el, "mim:indicatieClassificerend", a["classifying"])
                _add(el, "mim:mogelijkGeenWaarde", a["possibly_no_value"])
        if groups:
            container = _add(parent, "mim:gegevensgroepen")
            for name, a in groups.items():
                el = _add(container, "mim:Gegevensgroep")
                _add(el, "mim:naam", name)
                _add(el, "mim:herkomst", a["origin"])
                _definition(el, a["definition"])
                _add(el, "mim:herkomstDefinitie", a["origin_definition"])
                _add(el, "mim:datumOpname", a["date_added"])
                _add(el, "mim:indicatieMaterieleHistorie", a["material_history"])
                _add(el, "mim:indicatieFormeleHistorie", a["formal_history"])
                _add(el, "mim:kardinaliteit", a["cardinality"])
                _add(el, "mim:authentiek", a["authentic"])
                self.ref(_add(el, "mim:gegevensgroeptype"), "mim-ref:GegevensgroeptypeRef", a["type"])

    def object_type(self, parent: etree._Element, name: str, entry: dict) -> None:
        el = _add(parent, "mim:Objecttype", id=_id("Objecttype", name))
        _add(el, "mim:naam", name)
        if entry.get("concept"):
            _add(el, "mim:begrip", entry["concept"])
        _add(el, "mim:herkomst")
        _definition(el, entry["definition"])
        _add(el, "mim:herkomstDefinitie")
        _add(el, "mim:datumOpname")
        _add(el, "mim:indicatieAbstractObject", entry["abstract"])
        if entry["supertypes"]:
            supertypes = _add(el, "mim:supertypen")
            for sup in entry["supertypes"]:
                generalization = _add(supertypes, "mim:GeneralisatieObjecttypen")
                _add(generalization, "mim:datumOpname")
                self.ref(_add(generalization, "mim:supertype"), "mim-ref:ObjecttypeRef", sup)
        self.attributes(el, entry["attributes"])
        relations = [r for r in self.model["relations"] if r["source"] == name]
        if relations:
            container = _add(el, "mim:relatiesoorten")
            for r in relations:
                rel = _add(container, "mim:Relatiesoort")
                _add(rel, "mim:naam", r["name"])
                _add(rel, "mim:herkomst", r["origin"])
                _definition(rel, r["definition"])
                _add(rel, "mim:herkomstDefinitie", r["origin_definition"])
                _add(rel, "mim:datumOpname", r["date_added"])
                _add(rel, "mim:indicatieMaterieleHistorie", r["material_history"])
                _add(rel, "mim:indicatieFormeleHistorie", r["formal_history"])
                _add(rel, "mim:kardinaliteit", r["cardinality"])
                _add(rel, "mim:kardinaliteitBron", r["source_cardinality"])
                _add(rel, "mim:authentiek", r["authentic"])
                _add(rel, "mim:indicatieAfleidbaar", False)
                _add(rel, "mim:mogelijkGeenWaarde", r["possibly_no_value"])
                _add(rel, "mim:unidirectioneel", "Ja")
                _add(rel, "mim:aggregatietype", r["aggregation"])
                self.ref(_add(rel, "mim:doel"), "mim-ref:ObjecttypeRef", r["target"])

    def data_type(self, parent: etree._Element, name: str, entry: dict) -> None:
        stereotype = entry["stereotype"]
        tag = {"Gegevensgroeptype": "mim:Gegevensgroeptype", "Keuze": "mim:Keuze", "Gestructureerd datatype": "mim:GestructureerdDatatype"}[stereotype]
        el = _add(parent, tag, id=_id(stereotype, name))
        _add(el, "mim:naam", name)
        if stereotype == "Gegevensgroeptype":
            _add(el, "mim:herkomst")
            _definition(el, entry["definition"])
            _add(el, "mim:herkomstDefinitie")
            _add(el, "mim:datumOpname")
            self.attributes(el, entry["attributes"])
            return
        if entry["definition"]:
            _definition(el, entry["definition"])
        _add(el, "mim:datumOpname")
        if stereotype == "Keuze":
            choices = _add(el, "mim:keuzeDatatypen")
            for option, a in entry["attributes"].items():
                _add(choices, "mim:Datatype", a["type"], label=option)
            return
        elements = _add(el, "mim:dataElementen")
        for element_name, a in entry["attributes"].items():
            de = _add(elements, "mim:DataElement")
            _add(de, "mim:naam", element_name)
            if a["origin"]:
                _add(de, "mim:herkomst", a["origin"])
            if a["definition"]:
                _definition(de, a["definition"])
            if a["origin_definition"]:
                _add(de, "mim:herkomstDefinitie", a["origin_definition"])
            _add(de, "mim:datumOpname", a["date_added"])
            self.type(de, a["type"])
            _add(de, "mim:kardinaliteit", a["cardinality"])

    def codelist(self, parent: etree._Element, name: str, entry: dict) -> None:
        el = _add(parent, "mim:Codelijst", id=_id("Codelijst", name))
        _add(el, "mim:naam", name)
        _add(el, "mim:herkomst")
        _definition(el, entry["definition"])
        _add(el, "mim:herkomstDefinitie")
        _add(el, "mim:datumOpname")
        _add(el, "mim:locatie", str(scheme_uri(self.model["standard"], name)))

    def document(self) -> etree._Element:
        model = self.model
        root = etree.Element(_q("mim:Informatiemodel"), nsmap=NS)
        _add(root, "mim:naam", model["name"])
        _add(root, "mim:herkomst")
        _definition(root, "")
        _add(root, "mim:herkomstDefinitie")
        _add(root, "mim:datumOpname")
        _add(root, "mim:informatiemodeltype", "Logisch")
        _add(root, "mim:informatiedomein")
        _add(root, "mim:relatiemodelleringtype", "Relatiesoort leidend")
        _add(root, "mim:MIMVersie", "1.1.1")
        _add(root, "mim:MIMTaal", "NL")
        packages = _add(root, "mim:packages")
        groups = ("object_types", "data_types", "domains")
        for package in dict.fromkeys(e["package"] for g in groups for e in model[g].values()):
            domein = _add(packages, "mim:Domein", id=_id("Domein", package))
            _add(domein, "mim:naam", package)
            _add(domein, "mim:herkomst")
            _definition(domein, "")
            _add(domein, "mim:herkomstDefinitie")
            _add(domein, "mim:datumOpname")
            members = {g: {n: e for n, e in model[g].items() if e["package"] == package} for g in groups}
            structured = {n: e for n, e in members["data_types"].items() if e["stereotype"] == "Gestructureerd datatype"}
            if members["domains"] or structured:
                datatypen = _add(domein, "mim:datatypen")
                for name, entry in structured.items():
                    self.data_type(datatypen, name, entry)
                for name, entry in members["domains"].items():
                    self.codelist(datatypen, name, entry)
            for container, stereotype in (("mim:objecttypen", "Objecttype"), ("mim:gegevensgroeptypen", "Gegevensgroeptype"), ("mim:keuzen", "Keuze")):
                entries = {n: e for g in ("object_types", "data_types") for n, e in members[g].items() if e["stereotype"] == stereotype}
                if entries:
                    el = _add(domein, container)
                    for name, entry in entries.items():
                        (self.object_type if stereotype == "Objecttype" else self.data_type)(el, name, entry)
        return root


def to_mim_xml(model: dict) -> bytes:
    return etree.tostring(_Writer(model).document(), xml_declaration=True, encoding="UTF-8", pretty_print=True)


def _text(el: etree._Element, tag: str) -> str | None:
    """Text of a child element: None if it is missing, "" if it is empty."""
    child = el.find(tag, NS)
    if child is None:
        return None
    if tag == "mim:definitie":
        return "".join(child.find("xhtml:body/xhtml:p", NS).itertext()) if len(child) else ""
    return child.text or ""


def _bool(el: etree._Element, tag: str) -> bool:
    return _text(el, tag) == "true"


def _type(el: etree._Element) -> str:
    return el.find("mim:type/*", NS).text or ""


def _attribute(el: etree._Element, **fields: object) -> dict:
    return {
        **ATTRIBUTE_DEFAULTS,
        "cardinality": _text(el, "mim:kardinaliteit"),
        "origin": _text(el, "mim:herkomst") or None,
        "definition": _text(el, "mim:definitie") or "",
        "origin_definition": _text(el, "mim:herkomstDefinitie") or None,
        "date_added": _text(el, "mim:datumOpname") or None,
        **fields,
    }


def _attributes(el: etree._Element) -> dict[str, dict]:
    attributes = {}
    for a in el.iterfind("mim:attribuutsoorten/mim:Attribuutsoort", NS):
        attributes[_text(a, "mim:naam")] = _attribute(
            a,
            type=_type(a),
            authentic=_text(a, "mim:authentiek") or None,
            material_history=_bool(a, "mim:indicatieMaterieleHistorie"),
            formal_history=_bool(a, "mim:indicatieFormeleHistorie"),
            possibly_no_value=_bool(a, "mim:mogelijkGeenWaarde"),
            classifying=_bool(a, "mim:indicatieClassificerend"),
            derivable=_bool(a, "mim:indicatieAfleidbaar"),
        )
    for g in el.iterfind("mim:gegevensgroepen/mim:Gegevensgroep", NS):
        attributes[_text(g, "mim:naam")] = _attribute(
            g,
            type=g.find("mim:gegevensgroeptype/mim-ref:GegevensgroeptypeRef", NS).text,
            authentic=_text(g, "mim:authentiek") or None,
            material_history=_bool(g, "mim:indicatieMaterieleHistorie"),
            formal_history=_bool(g, "mim:indicatieFormeleHistorie"),
        )
    return attributes


def from_mim_xml(data: bytes) -> dict:
    """The model part of the reference model; each codelist has `scheme` instead of `values`."""
    root = etree.fromstring(data, etree.XMLParser(no_network=True, resolve_entities=False))
    object_types, data_types, domains, relations = {}, {}, {}, []
    for domein in root.iterfind("mim:packages/mim:Domein", NS):
        package = _text(domein, "mim:naam")
        for ot in domein.iterfind("mim:objecttypen/mim:Objecttype", NS):
            name = _text(ot, "mim:naam")
            object_types[name] = {
                "stereotype": "Objecttype",
                "package": package,
                "definition": _text(ot, "mim:definitie"),
                "abstract": _bool(ot, "mim:indicatieAbstractObject"),
                "supertypes": [r.text for r in ot.iterfind("mim:supertypen/mim:GeneralisatieObjecttypen/mim:supertype/mim-ref:ObjecttypeRef", NS)],
                "attributes": _attributes(ot),
                **({"concept": _text(ot, "mim:begrip")} if _text(ot, "mim:begrip") else {}),
            }
            for r in ot.iterfind("mim:relatiesoorten/mim:Relatiesoort", NS):
                relations.append(
                    {
                        "name": _text(r, "mim:naam"),
                        "source": name,
                        "target": r.find("mim:doel/mim-ref:ObjecttypeRef", NS).text,
                        "cardinality": _text(r, "mim:kardinaliteit"),
                        "source_cardinality": _text(r, "mim:kardinaliteitBron"),
                        "stereotype": "Relatiesoort",
                        "aggregation": _text(r, "mim:aggregatietype"),
                        "authentic": _text(r, "mim:authentiek") or None,
                        "material_history": _bool(r, "mim:indicatieMaterieleHistorie"),
                        "formal_history": _bool(r, "mim:indicatieFormeleHistorie"),
                        "possibly_no_value": _bool(r, "mim:mogelijkGeenWaarde"),
                        "origin": _text(r, "mim:herkomst") or None,
                        "origin_definition": _text(r, "mim:herkomstDefinitie") or None,
                        "date_added": _text(r, "mim:datumOpname") or None,
                        "definition": _text(r, "mim:definitie"),
                    }
                )
        for g in domein.iterfind("mim:gegevensgroeptypen/mim:Gegevensgroeptype", NS):
            data_types[_text(g, "mim:naam")] = {
                "stereotype": "Gegevensgroeptype",
                "package": package,
                "definition": _text(g, "mim:definitie"),
                "attributes": _attributes(g),
            }
        for k in domein.iterfind("mim:keuzen/mim:Keuze", NS):
            data_types[_text(k, "mim:naam")] = {
                "stereotype": "Keuze",
                "package": package,
                "definition": _text(k, "mim:definitie") or "",
                "attributes": {d.get("label"): {"type": d.text} for d in k.iterfind("mim:keuzeDatatypen/mim:Datatype", NS)},
            }
        for s in domein.iterfind("mim:datatypen/mim:GestructureerdDatatype", NS):
            data_types[_text(s, "mim:naam")] = {
                "stereotype": "Gestructureerd datatype",
                "package": package,
                "definition": _text(s, "mim:definitie") or "",
                "attributes": {_text(d, "mim:naam"): _attribute(d, type=_type(d)) for d in s.iterfind("mim:dataElementen/mim:DataElement", NS)},
            }
        for c in domein.iterfind("mim:datatypen/mim:Codelijst", NS):
            domains[_text(c, "mim:naam")] = {
                "stereotype": "Codelijst",
                "package": package,
                "definition": _text(c, "mim:definitie"),
                "scheme": _text(c, "mim:locatie"),
            }
    return {
        "name": _text(root, "mim:naam"),
        "object_types": object_types,
        "data_types": data_types,
        "domains": domains,
        "relations": sorted(relations, key=lambda r: (r["source"], r["name"])),
    }


# SKOS


def to_skos(model: dict) -> str:
    standard = model["standard"]
    graph = Graph()
    graph.bind("skos", SKOS)
    graph.bind("airco", namespace(standard))
    graph.bind("begrip", REGISTER_BASE)
    for name, entry in model["domains"].items():
        scheme = scheme_uri(standard, name)
        graph.add((scheme, RDF.type, SKOS.ConceptScheme))
        graph.add((scheme, DCTERMS.title, Literal(name, lang="nl")))
        for v in entry["values"]:
            concept = value_uri(standard, name, v["value"])
            graph.add((concept, RDF.type, SKOS.Concept))
            graph.add((concept, SKOS.prefLabel, Literal(v["value"], lang="nl")))
            graph.add((concept, SKOS.definition, Literal(v["definition"], lang="nl")))
            graph.add((concept, SKOS.inScheme, scheme))
            graph.add((concept, SKOS.topConceptOf, scheme))
            for parent in v.get("parents", []):
                graph.add((concept, SKOS.broadMatch, value_uri(standard, name.removesuffix("Plus"), parent)))
            if "code" in v:
                graph.add((concept, SKOS.notation, Literal(v["code"])))
            if "concept" in v:
                graph.add((concept, SKOS.exactMatch, URIRef(v["concept"])))
    return graph.serialize(format="turtle")


def codelist_values(text: str) -> dict[str, list[dict]]:
    """Values per concept scheme URI, sorted by value, as `refmodel.generate` sorts them."""
    graph = Graph().parse(data=text, format="turtle")
    values: dict[str, list[dict]] = {}
    for scheme in graph.subjects(RDF.type, SKOS.ConceptScheme):
        entries = []
        for concept in graph.subjects(SKOS.inScheme, scheme):
            parents = sorted(str(graph.value(p, SKOS.prefLabel)) for p in graph.objects(concept, SKOS.broadMatch))
            code, match = graph.value(concept, SKOS.notation), graph.value(concept, SKOS.exactMatch)
            entries.append(
                {
                    "value": str(graph.value(concept, SKOS.prefLabel)),
                    "definition": str(graph.value(concept, SKOS.definition)),
                    **({"parents": parents} if parents else {}),
                    **({"code": str(code)} if code is not None else {}),
                    **({"concept": str(match)} if match is not None else {}),
                }
            )
        values[str(scheme)] = sorted(entries, key=lambda v: v["value"])
    return values
