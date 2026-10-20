# Reference model

The reference model of a standard is the list of everything the standard names: object types, attributes, data types, codelists and their values. The scoring rules use it to tell a wrong answer from an invented one. `airco-refmodel` writes the reference model of IMGeo 2.2 from the MIM model and the concept register, as two files in `reference-models/imgeo-2.2/`, and `ReferenceModel.load()` in `validators/refmodel.py` reads them back into one dict.

| File | Content |
| --- | --- |
| `model.mim.xml` | Object types, data types, codelists and relations in MIM-XML 1.1.1, with relatiesoort leidend |
| `codelists.ttl` | The values of each codelist in SKOS |

What the catalogs publish is not stored. `ReferenceModel.published_domains` reads the domain values per list from the vendored catalogs, which `sources/sources.lock.json` pins, so that a value the catalogs publish but the MIM model lacks, such as `historie` in StatusPlus, counts as known.

## MIM-XML

The file has one `Domein` per package of the MIM model. It validates against the MIM 1.1.1 XSD in `sources/mim-1.1.1/`; `tests/test_refmodel.py` checks that.

| In the MIM model | In MIM-XML |
| --- | --- |
| Object type | `Objecttype`. `begrip` is the URI of the concept with the same name in the concept register |
| Attribute | `Attribuutsoort`, or `Gegevensgroep` if its type is a Gegevensgroeptype |
| Codelist | `Codelijst`. `locatie` is the URI of its concept scheme in `codelists.ttl` |
| Keuze | `Keuze` with `keuzeDatatypen`: per option a `Datatype` with the option name as `label` |
| NEN3610ID | `GestructureerdDatatype` with `dataElementen` |
| Association | `Relatiesoort` |

Required MIM metadata that the MIM model leaves empty, such as `herkomst` of an object type, is an empty element. MIM-XML has no place for the definition of a Keuze option, so the file leaves those out.

## SKOS

Each codelist is a `skos:ConceptScheme` with the URI `urn:airco-harness:imgeo-2.2:list_<codelist>` and a `dct:title`. Each value is a `skos:Concept` with the URI `urn:airco-harness:imgeo-2.2:<codelist>_<value>`, and a top concept of its scheme. In both URIs, every character other than a letter, a digit, `_` or `-` becomes `_`.

| Property | Content |
| --- | --- |
| `skos:prefLabel`, `skos:definition` | Value and definition from the MIM model, in Dutch |
| `skos:broadMatch` | For a plus value, the BGT values it refines, in the codelist without `Plus` |
| `skos:exactMatch` | The concept in the IMGeo concept register with the same preferred label |
| `skos:notation` | The code, for the two values that have one |

SKOS has no order, so the dict lists the values of each codelist sorted by value.
