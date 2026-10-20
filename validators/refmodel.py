"""Reference model of a standard, generated from its MIM model and used to detect invented terms.

    uv run airco-refmodel   # regenerate reference-models/imgeo-2.2/

The IMGeo 2.2 MIM model is an Enterprise Architect XMI 1.1 export. The
reference model is a dict with English keys; names, definitions and values are
as in the model. refmodel_files stores it as MIM-XML with the codelist values
in SKOS. Codelist values are sorted by value, because a SKOS concept scheme
has no order. A codelist value gets the URI of the concept in the IMGeo
concept register with the same preferred label, and an object type the one
with the same name.

What the catalogs publish is not part of the stored model: ReferenceModel reads
the domain values from the vendored catalogs when it needs them, so that a
value the catalogs publish but the model lacks counts as known. The lock file
sources.lock.json pins those files.
"""

from __future__ import annotations

import argparse
import html
import re
import unicodedata
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

from lxml import html as lxml_html
from rdflib import Graph
from rdflib.namespace import RDF, SKOS

from . import refmodel_files, sources

UML = "{omg.org/UML1.3}"
REFERENCE_MODELS = Path(__file__).resolve().parent.parent / "reference-models"
IMGEO = "imgeo-2.2"
MODEL_SOURCE = "imgeo-2.2/imgeo2.2-mim-logisch.xml"
CONCEPT_REGISTER = "imgeo-2.2/concept-register-imgeo.ttl"
# The catalog files and the chapter that publishes their domain values.
DOMAIN_CHAPTERS = {"imgeo-2.2/catalog-bgt.html": 9, "imgeo-2.2/catalog-imgeo.html": 8}
MODEL_PACKAGES = {"Informatiemodel Geografie (IMGeo)", "Codelijsten", "Onderdelen"}
YES = {"ja", "true"}
AGGREGATION = {"composite": "Compositie", "shared": "Gedeeld"}


def _tags(element: ET.Element) -> dict[str, str]:
    tags: dict[str, str] = {}
    for tv in element.findall(f"{UML}ModelElement.taggedValue/{UML}TaggedValue"):
        tags.setdefault(tv.get("tag", ""), tv.get("value") or "")
    return tags


def _text(value: str | None) -> str:
    # EA stores some text with doubly escaped entities, such as &amp;#233;.
    return html.unescape(html.unescape(value or "")).strip()


def _cardinality(tags: dict[str, str]) -> str:
    low, high = tags.get("lowerBound", "1"), tags.get("upperBound", "1")
    return low if low == high else f"{low}..{high}"


def _attribute(tags: dict[str, str]) -> dict[str, object]:
    return {
        "type": tags.get("type", ""),
        "cardinality": _cardinality(tags),
        "authentic": tags.get("Authentiek") or None,
        "material_history": tags.get("Indicatie materiële historie", "").lower() in YES,
        "formal_history": tags.get("Indicatie formele historie", "").lower() in YES,
        "possibly_no_value": tags.get("Mogelijk geen waarde", "").lower() in YES,
        "origin": tags.get("Herkomst") or None,
        "definition": _text(tags.get("description")),
        "origin_definition": tags.get("Herkomst definitie") or None,
        "date_added": tags.get("Datum opname") or None,
        "classifying": tags.get("Indicatie classificerend", "").lower() in YES,
        "derivable": tags.get("derived") == "1",
    }


def _register_concepts() -> tuple[dict[str, str], dict[str, list[str]]]:
    """Concept URIs in the IMGeo concept register, by lower-case local name and by normalized preferred label."""
    graph = Graph().parse(sources.path(CONCEPT_REGISTER), format="turtle")
    by_name: dict[str, str] = {}
    by_label: dict[str, list[str]] = {}
    for s in graph.subjects(RDF.type, SKOS.Concept):
        uri = str(s)
        by_name[uri.removeprefix(refmodel_files.REGISTER_BASE).lower()] = uri
        for label in graph.objects(s, SKOS.prefLabel):
            by_label.setdefault(normalize(str(label)), []).append(uri)
    return by_name, by_label


def catalog_domains(catalog_html: str, chapter: int) -> dict[str, list[str]]:
    """Domain values per list from the domain chapter of a catalog.

    The rendered tables put the first value of a BGT list in the table header,
    so header and body rows are read alike; IMGeo tables have a real header
    row starting with "waarde", which is skipped.
    """
    doc = lxml_html.fromstring(catalog_html)
    domains: dict[str, list[str]] = {}
    for heading in doc.xpath(f'//h3[starts-with(@id, "x{chapter}-")]'):
        name = re.sub(rf"^{chapter}\.\d+\s+", "", heading.text_content().strip())
        tables = heading.getparent().xpath(".//table")
        rows = tables[0].xpath(".//tr") if tables else []
        cells = [r.xpath("./th|./td")[0].text_content().strip() for r in rows if r.xpath("./th|./td")]
        domains[name] = [c for c in cells if c and c != "waarde"]
    return domains


def generate() -> dict[str, object]:
    root = ET.parse(sources.path(MODEL_SOURCE)).getroot()
    classes = {c.get("xmi.id"): c for c in root.iter(f"{UML}Class")}
    names = {cid: c.get("name") for cid, c in classes.items()}
    supertypes: dict[str, list[str]] = {}
    for g in root.iter(f"{UML}Generalization"):
        sub, sup = names.get(g.get("subtype")), names.get(g.get("supertype"))
        if sub and sup:
            supertypes.setdefault(sub, []).append(sup)
    by_name, by_label = _register_concepts()

    object_types: dict[str, object] = {}
    data_types: dict[str, object] = {}
    lists: dict[str, dict[str, object]] = {}
    model_ids = {cid for cid, c in classes.items() if _tags(c).get("package_name") in MODEL_PACKAGES}
    for c in sorted(classes.values(), key=lambda c: c.get("name", "")):
        tags = _tags(c)
        if tags.get("package_name") not in MODEL_PACKAGES:
            continue
        name, stereotype = c.get("name", ""), tags.get("stereotype", "")
        features = c.findall(f"{UML}Classifier.feature/{UML}Attribute")
        package = tags["package_name"]
        if stereotype == "Codelijst":
            values = []
            for a in features:
                at = _tags(a)
                concepts = by_label.get(normalize(a.get("name")), [])
                if len(concepts) > 1:
                    concepts = [c for c in concepts if c.lower().endswith("_" + name.lower())]
                values.append(
                    {
                        "value": a.get("name"),
                        "definition": _text(at.get("description")),
                        **({"parents": sorted(p.strip() for p in at["parent"].split(";"))} if at.get("parent") else {}),
                        **({"code": at["Code"]} if at.get("Code") else {}),
                        **({"concept": concepts[0]} if len(concepts) == 1 else {}),
                    }
                )
            lists[name] = {
                "stereotype": stereotype,
                "package": package,
                "definition": _text(tags.get("documentation")),
                "values": sorted(values, key=lambda v: v["value"]),
            }
            continue
        if stereotype == "Keuze":
            # MIM-XML gives each option of a choice between data types only a label and a type.
            options = {a.get("name", ""): {"type": _tags(a).get("type", "")} for a in features}
            data_types[name] = {"stereotype": stereotype, "package": package, "definition": _text(tags.get("documentation")), "attributes": options}
            continue
        attributes = {a.get("name", ""): _attribute(_tags(a)) for a in features}
        entry = {"stereotype": stereotype, "package": package, "definition": _text(tags.get("documentation")), "attributes": attributes}
        if stereotype == "Objecttype":
            object_types[name] = {
                **entry,
                "abstract": c.get("isAbstract") == "true",
                "supertypes": sorted(supertypes.get(name, [])),
                **({"concept": by_name[name.lower()]} if name.lower() in by_name else {}),
            }
        else:
            data_types[name] = entry

    relations = []
    for assoc in root.iter(f"{UML}Association"):
        ends = assoc.findall(f".//{UML}AssociationEnd")
        if len(ends) == 2 and {e.get("type") for e in ends} <= model_ids:
            src, dst = ends
            tags = _tags(assoc)
            relations.append(
                {
                    "name": assoc.get("name"),
                    "source": names.get(src.get("type")),
                    "target": names.get(dst.get("type")),
                    "cardinality": dst.get("multiplicity"),
                    "source_cardinality": src.get("multiplicity"),
                    "stereotype": tags.get("stereotype"),
                    "aggregation": next((AGGREGATION[e.get("aggregation")] for e in ends if e.get("aggregation") in AGGREGATION), "Geen"),
                    "authentic": tags.get("Authentiek") or None,
                    "material_history": tags.get("Indicatie materiële historie", "").lower() in YES,
                    "formal_history": tags.get("Indicatie formele historie", "").lower() in YES,
                    "possibly_no_value": tags.get("Mogelijk geen waarde", "").lower() in YES,
                    "origin": tags.get("Herkomst") or None,
                    "origin_definition": tags.get("Herkomst definitie") or None,
                    "date_added": tags.get("Datum opname") or None,
                    "definition": _text(tags.get("documentation")),
                }
            )

    return {
        "standard": IMGEO,
        "name": next(p.get("name") for p in root.iter(f"{UML}Package") if _tags(p).get("stereotype") == "Basismodel"),
        "object_types": object_types,
        "data_types": data_types,
        "domains": dict(sorted(lists.items())),
        "relations": sorted(relations, key=lambda r: (r["source"] or "", r["name"] or "")),
    }


def published_domains() -> dict[str, list[str]]:
    """Domain values per list as the vendored BGT and IMGeo catalogs publish them."""
    domains: dict[str, list[str]] = {}
    for catalog, chapter in DOMAIN_CHAPTERS.items():
        domains.update(catalog_domains(sources.path(catalog).read_text(encoding="utf-8"), chapter))
    return dict(sorted(domains.items()))


def normalize(term: str) -> str:
    """Compare form for terms: Unicode NFKC, any dash as '-', single spaces, lower case."""
    t = unicodedata.normalize("NFKC", term)
    t = re.sub(r"[‐-―−]", "-", t)
    return re.sub(r"\s+", " ", t).strip().lower()


@dataclass(frozen=True)
class ReferenceModel:
    data: dict

    @classmethod
    def load(cls, standard: str = IMGEO) -> ReferenceModel:
        return cls(refmodel_files.read(REFERENCE_MODELS / standard))

    @cached_property
    def published_domains(self) -> dict[str, list[str]]:
        return published_domains()

    def values(self, domain: str) -> list[str]:
        return [v["value"] for v in self.data["domains"][domain]["values"]]

    def attribute(self, object_type: str, name: str) -> dict:
        return self.data["object_types"][object_type]["attributes"][name]

    @cached_property
    def all_values(self) -> dict[str, set[str]]:
        """Normalized domain value to the lists it occurs in, in the model or in the published catalogs."""
        index: dict[str, set[str]] = {}
        for domain, entry in self.data["domains"].items():
            for v in entry["values"]:
                index.setdefault(normalize(v["value"]), set()).add(domain)
        for domain, values in self.published_domains.items():
            for v in values:
                index.setdefault(normalize(v), set()).add(domain)
        return index

    @cached_property
    def all_terms(self) -> set[str]:
        """Every normalized name the model knows: object types, data types, attributes, lists, values."""
        terms = set(self.all_values)
        for group in ("object_types", "data_types"):
            for name, entry in self.data[group].items():
                terms.add(normalize(name))
                terms.update(normalize(a) for a in entry["attributes"])
                terms.update(normalize(a["type"]) for a in entry["attributes"].values() if a["type"])
        terms.update(normalize(d) for d in self.data["domains"])
        return terms


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(prog="airco-refmodel", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)


def main() -> None:
    build_parser().parse_args()
    model = generate()
    target = REFERENCE_MODELS / model["standard"]
    target.mkdir(parents=True, exist_ok=True)
    files = refmodel_files.write(model, target)
    print(
        f"{', '.join(str(f.relative_to(REFERENCE_MODELS.parent)) for f in files.values())}: {len(model['object_types'])} object types, "
        f"{len(model['domains'])} domains, source sha256 {sources.lock()[MODEL_SOURCE]['sha256'][:12]}"
    )
