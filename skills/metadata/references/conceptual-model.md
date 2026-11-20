# Conceptual model for reading metadata

These are working roles, not a new ontology or a required publication profile. Normalize by meaning so different standards can support the same discovery task. Retain the source terms, link direction, scope, profile, and version; mappings can be partial or lossy and do not imply formal equivalence.

This is the built-in model. A [configuration profile](./configuration.md) can select a different metadata model without changing the catalog or dataset being interpreted.

| View | Roles and metadata to look for | Question it can answer |
| --- | --- | --- |
| Discovery and governance | Catalog, catalog record, described resource, identifier, title, description, publisher, contact, theme, coverage, version, rights and access conditions | What is this, who maintains it, and can I use it? |
| Data and access | Dataset (possibly series/member), distribution or representation, service, endpoint, API contract, format, media type, access and download mechanism | Which snapshot, file or interface answers the question? |
| Meaning and structure | Concept scheme, concept, conceptual information model, logical model, technical schema, object/attribute/relationship, implementation field | What does the data mean and how is that meaning represented? |
| Specifications and mappings | Standard, profile, specification, model release, explicit model-to-data or field mapping | What is declared to apply, to which resource and version? |
| Quality and lineage | Measurement, metric, annotation, policy, source, derivation, generating activity and responsible agent | Is this evidence fit for this use, and where did it come from? |

## Model levels (MIM framing)

| Level | Distinction | Illustrative evidence |
| --- | --- | --- |
| 1 — Begrippenmodel | Domain vocabulary and meaning | Concepts, preferred labels, definitions, and semantic relations in a concept scheme |
| 2 — Conceptueel informatiemodel | Information about domain objects and their relationships, independent of how data is represented | Semantic object types, relationships and business constraints |
| 3 — Logisch informatiemodel | Structures and constraints of the data representation independent of concrete technology | Data-oriented attributes, data types, identifiers and logical relationships |
| 4 — Fysiek datamodel / technically implemented representation | Concrete technology-specific implementation | API schema, database DDL, XML/JSON schema or encoding-specific shapes, where they actually describe the implementation |

Use declared purpose, abstraction and provenance rather than extension, UML/RDF notation, granularity, or publication system. A diagram or RDF graph can carry multiple levels. A shape used only to validate catalog metadata is not the dataset's level-4 model. An endpoint or dataset is not itself a model: inspect its contract or schema. MIM primarily standardizes modeling at levels 2 and 3; levels 1 and 4 are context, not claims that those artifacts follow MIM. A level can remain undetermined even if an information model is known to use MIM.

## Connecting claims

Think in possible paths, not a mandatory stack:

```text
catalog registry → catalog → catalog entry → dataset → distribution → access route
data service → served dataset
access route → API collection / operation, MCP tool / resource, or data file → source metadata / schema
dataset / distribution / service → applicable specification or model (if documented)
API operation / field → technical schema element → logical / conceptual element → concept (if mapped)
data resource → quality claim or provenance evidence (check scope)
```

Look in catalog records, publisher landing pages, service descriptions, model and vocabulary registries, versioned schema repositories and explicit mapping documents. Travel back from a model registry by publisher-documented references or an identifier search; a search result is a candidate, not an asserted inverse. Check scope for series vs member, dataset vs distribution, record vs resource, logical model vs schema release, and API operation vs whole service. An asserted relationship is not permission to propagate licenses, derivation, quality scores, or conformance along the path.
