# Interpretation skill registry

The repositories below are independent optional companions. No skill is fetched, installed, or executed automatically by this package. Look up the exact skill `name` in the client's installed skills; a repository, plugin and skill can have different names. Use the supported skill mechanism and never claim a handoff ran when it did not.

Use this registry when source documentation does not settle an interpretation question and a [standards manifest](./standards-manifests.md) does not identify a suitable, available skill. A skill can explain a schema; an MCP tool or API can expose a dataset. Keep interpretation separate from finding and checking the [data access route](./source-discovery.md). A manifest link cannot override scope or permission checks.

| Route | Companion | Read-first remit and fallback |
| --- | --- | --- |
| Level 1: concepts and definitions | [`geonovum-nl-sbb-review`](https://github.com/Geonovum/skills-nl-sbb/blob/main/skills/geonovum-nl-sbb-review/SKILL.md) ([repository](https://github.com/Geonovum/skills-nl-sbb)) | Use NL-SBB/SKOS reading guidance for concepts, definition sources and relations. The available upstream skill is for **review**, not a lookup-only skill: for exploration, consult its [reading reference](https://github.com/Geonovum/skills-nl-sbb/blob/main/skills/geonovum-nl-sbb-review/reference.md) or the official standard rather than initiating a review. Activate the full upstream skill only for an explicitly requested review and leave optional validation and source checks subject to its own workflow and permissions. If unavailable, read the supplied vocabulary and state which profile claims are unverified. |
| Levels 2–3: conceptual and logical information models | [`geonovum-mim-interpret`](https://github.com/Geonovum-labs/skills-mim/blob/main/mim-interpret/SKILL.md) ([repository](https://github.com/Geonovum-labs/skills-mim)) | Interpret model elements, constraints and evidence-backed field bindings. Do not route to the implementation stub, or ask it to author or validate models. If unavailable, cite the publisher's model and evidence; leave undocumented bindings unresolved. |
| Level 4: implementation | An installed skill for reading the relevant API, schema, or format, e.g. OpenAPI, OGC API, JSON Schema, XML Schema or SQL | Interpret the applicable contract, operation, version and field path. No default level-4 skill is bundled. If no match is installed, read the source contract or published schema directly and state limits. Do not generate or deploy an implementation. |
| Additional metadata | An installed skill for interpreting a geospatial profile, data quality claims, or provenance | Use only where the question requires more depth than catalog triage. If no match, cite the observed assertions and scope. |

## Handoff packet

Provide the minimum information the interpretation skill needs:

- The user's bounded question and read-only scope.
- Resource, artifact and element identifiers, source URLs or file references, and the relevant publisher, version and profile.
- Level and evidence supporting that level; the relevant asserted or proposed links, with status.
- The expected result: interpretation, citations, and unresolved assumptions. Explicitly exclude edits, writes and unrelated checks.

Return the result to the original evidence chain rather than treating skill output as an independent authoritative source. Keep a multi-level task coordinated here; for example, ask a schema reader about `GET /buildings/{id}` and a MIM reader about a named attribute, then report whether a published bridge actually connects them.

## When domain judgment is needed

An interpretation skill can establish that a dataset records pavement type. It cannot establish from that fact alone whether pavement type predicts water accumulation. Report what the metadata supports and identify what a domain expert, such as a hydrologist, would need to assess. Recommend consultation; do not contact anyone.

## Adding an interpretation skill

Maintain this registry outside the agent workflow: add a row or narrow an existing route with the exact installed skill name, upstream URL, technology/profile signals, question scope, prerequisites and no-skill fallback. Check that the companion reads or interprets existing resources and does not require authoring. Prefer the narrowest applicable match. Add a case to the [behavioral evals](../evals/evals.json) for the new route or its failure path.
