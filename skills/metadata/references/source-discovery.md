# Finding metadata and routing to sources

Start from the question and search the metadata most likely to answer it. A glossary, model repository, data catalog, service description or supplied artifact can be the entry point; no one source type is required.

## Find and connect metadata

- **Meaning or classification:** Look for glossaries, model repositories and value lists. Search definitions, object types, attributes and permitted values, not just titles. For `verharding`, `verhard` and `fysiek voorkomen` are search leads, not automatically synonyms. Check the model version and where the value applies.
- **Dataset discovery:** Search configured or publisher catalogs, including those listed in a registry or aggregated elsewhere, using topic, identifiers, official labels and alternate terms. Check publisher, coverage, period, version, rights and links. Prefer publisher records over potentially stale harvested copies.
- **Access or capability:** Start with the known service, collection, tool or file description. If the schema alone does not explain an element's meaning, trace back to the dataset, model, glossary or value list where documented.

Work in either direction. Starting from a concept or model element, look for a publisher mapping, linked specification, or dataset/service documentation citing that model or version; then verify the applicable distribution, collection or field. If no direct link is available, search on verified model identifiers and official terms, marking matches as candidates until the binding is supported. A glossary term is not a dataset field, a permitted model value is not an observed record, and a model-to-dataset link is not a field mapping. If one source type does not answer the question, try another relevant one. If the question is answered at the concept or model level, an access route is optional.

## Inspect each plausible access route

Compare routes by dataset identity, required capability, access and suitability. A service landing page, tool listing, or schema title alone does not establish a binding to the target data.

| Route | Look for metadata at the source | Verify before recommending use |
| --- | --- | --- |
| **MCP** | In an already connected, permitted server, inspect available tool and resource descriptions, tool input schemas, declared output schemas if provided, and linked dataset or service documentation. Otherwise use publisher documentation and mark the route unverified in the current client. | Exact server/tool or resource, what it serves, parameters, read-only suitability, and availability. A tool input schema is not the dataset's schema. Do not connect or install a server based on a catalog or manifest link. |
| **OGC API** | Follow advertised links from the landing page to the API definition, conformance declarations and collections as applicable. Read the target collection's metadata; look for queryables, a data schema, and operation/response descriptions where advertised. | Collection ID, extent, operation, formats, supported CRS and filters relevant to the task. Queryables describe filterable properties, not necessarily every field returned. Do not assume optional endpoints or invent a collection URL. |
| **Other API, download or local source** | Inspect the contract, publisher data dictionary or sidecar metadata, GIS layer metadata, or a provided schema. Examples include OpenAPI, JSON Schema, XSD and documented tabular columns. | Exact distribution, version, fields/types and units, access conditions and documented operations. Do not infer the schema from the format alone or download a full dataset just to infer its structure. |

Keep dataset, access mechanism and technical description distinct. A catalog, API and MCP tool may point to the same dataset, or to different subsets/releases; check the evidence before treating them as interchangeable. Revisit discovery if a route cannot answer the question. If one route is unavailable, cite the alternate route or the missing prerequisite rather than claiming success. Where source metadata reveals another relevant standard, check its [manifest](./standards-manifests.md) without making the manifest a gate to access.

Pass on the relevant catalog record, dataset and distribution/collection identifiers, exact service or tool, the metadata links, applicable rights and any unresolved field/scope questions. This lets the next agent act without guessing which source or schema to use.
