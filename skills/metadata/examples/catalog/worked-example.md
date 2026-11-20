# Worked example: Municipal trees

**Question:** “Where is the trees API described, what does `speciesCode` mean, and what does the 92% quality figure tell me?”

All sources are local and fictional. `trees.example` identifiers are labels for the fixture; do not try to fetch them. Read [catalog.ttl](./catalog.ttl), [openapi.json](./openapi.json) (the fixture for `ex:openapi.json`), and [model-notes.md](./model-notes.md).

## What you can answer

The API contract describes `GET /trees` in API version `2026.1`, which can return a string property `speciesCode` on each record. It is not marked required by this response schema. The logical model has a likely related attribute, `Tree.taxonCode`, but no published bridge in this fixture confirms that it is the same field or gives the API code domain. The 92% is the fraction with a non-empty `speciesCode` in the API distribution on 2026-10-01, not a measure of correctness or overall dataset completeness. No live endpoint was tested.

## Evidence

| Status | Trace | Scope or limitation |
| --- | --- | --- |
| Documented | `trees-record` → `foaf:primaryTopic` → `trees` | The record's modification date is not the dataset's update date. |
| Documented | `trees` → `dcat:distribution` → `tree-api-view` → `dcat:accessService` → `tree-api` → `dcat:endpointDescription` → `openapi.json` | The service also declares `dcat:servesDataset trees`; the contract, not the endpoint itself, is level 4. |
| Documented | `tree-api` → `dct:conformsTo` → `service-spec-v1` | The CSSV entry describes a service specification, not the tree dataset or a field mapping. Its catalog listing via `dcat:dataset` does not change that role. The specification itself is not supplied. |
| Documented | `trees` → `dct:conformsTo` → `tree-logical-v2` → `dct:references` → `tree-conceptual-v1` → `dct:references` → `tree-terms` | The latter links are references; they do not themselves assert equivalence, conformance or a field mapping. Model level labels come from publisher notes. |
| Inferred; binding unresolved | API `speciesCode` → logical `Tree.taxonCode` | Plausible by context but not asserted. Ask the publisher for a release-specific field mapping and versioned code list. |
| Documented | `species-coverage` → `dqv:computedOn` → `tree-api-view` | Metric `species-field-fill`; value `0.92`; scope is the distribution and date, not every distribution or current API behavior. |
| Documented | `trees` → `prov:wasDerivedFrom` → `survey-2026` | Dataset-level derivation claim; the activity, methodology and responsible agent are not supplied. |

## Optional handoffs

- **Level 1:** read NL-SBB/SKOS guidance for `tree-taxon` and its definition. This is a SKOS concept scheme with no NL-SBB declaration; do not invoke a full review.
- **Levels 2–3:** the excerpts can be read locally. For detailed interpretation with a substantive MIM artifact, pass the publisher's versions and the `Tree.taxonCode` question to MIM Interpret. The fixture is not itself a full MIM model, and the skill cannot confirm a missing bridge.
- **Level 4:** read the contract directly, or use an installed OpenAPI skill to interpret `GET /trees`, API version `2026.1`, and the `speciesCode` path.
