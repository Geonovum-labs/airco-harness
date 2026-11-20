# Configuring the metadata model and sources

This is a profile read by the agent, not a plugin manifest, runtime service, or client-specific settings file. Configure the **model for interpreting metadata** separately from the **sources in which to find metadata, schemas and datasets**.

## Select one profile

1. Use the JSON file explicitly selected by the user for the task.
2. Otherwise use `metadata.config.json` in the active workspace root, when known and present.
3. Otherwise use the [built-in conceptual model](./conceptual-model.md) and no configured sources or manifest locations. User-supplied artifacts and authoritative public sources can still be read. The experimental profile is never automatically selected.

Profiles replace one another; do not merge them. Read only the chosen profile. Resolve relative paths against **that file's directory**, not the skill or working directory. Credentials, client installation settings and executable commands do not belong in this file. Repository-local copies named `metadata.config.json` are gitignored.

## Profile format (version 1)

| Key | Meaning |
| --- | --- |
| `version` | Required integer `1`. |
| `metadata_model` | Required object: `kind` is `builtin`, `file`, or `url`. For `file` and `url`, supply `location` (a local path or HTTPS URL respectively), plus optional `name` and `version` as expected identity. For `builtin`, omit `location`. |
| `sources` | Required ordered array (may be empty). Each source has a unique `id`, `kind` (`file` or `url`), `location`, and non-empty `roles` chosen from `data_catalog`, `metadata`, `metadata_model`, `domain_model`, `vocabulary`, `data`, `standards_register`. Optional `status` and `notes` describe scope or maturity; they are not instructions. |
| `standard_manifests` | Optional ordered array (may be empty). Each entry has `standard_id` (canonical IRI or publisher-defined identifier), optional `standard_version`, `kind` (`file` or `url`), and `location`. These are leads for [manifest discovery](./standards-manifests.md), not authoritative matches on their own. |

Load only the model and sources relevant to the question. For an external metadata model, keep its roles, terms and mappings separate from source assertions. Use it as the interpretation lens only when the resource is readable and is demonstrably a **metadata model**, not simply a domain model, vocabulary, or search page. If an expected identity or version is supplied, verify it before applying the model. A source with role `metadata_model` is a **place to look**, not an automatic model selection.

User-supplied task evidence comes first. Choose discovery sources by what the question needs: `vocabulary` or `domain_model` for meanings and classifications, `data_catalog` for dataset records and coverage, and relevant `metadata` or `data` sources for access descriptions. These are entry points, not a mandatory order. Modeldesk may be a useful starting point for model questions, while PDOK can help find dataset records and distributions. Within a discovery step, try relevant sources in listed order, but use the evidence whose scope, authority, and version fit the question. `data` marks a place to find datasets or access routes, not permission to query protected data or download payloads. MCP connectivity remains a client responsibility; a profile can point to publisher documentation but does not configure a server.

If a selected configuration cannot be read, is invalid, or specifies a model that cannot be verified or interpreted, state what failed. Use the built-in model as an **explicit fallback** and ignore an invalid profile rather than trying it partially. For a valid profile with an unavailable model, its independently configured sources can still be used. If a relevant configured source fails or has no suitable artifact, report the limitation and continue to the next suitable source or official publication.

## Modeldesk experiment

Select [`modeldesk.experimental.json`](../examples/config/modeldesk.experimental.json) by path, or copy it to `metadata.config.json` at the workspace root. It follows the discovery order in [skills-mim PR #1](https://github.com/Geonovum-labs/skills-mim/pull/1/changes): the public [Geonovum catalog on Modeldesk](https://catalog.modeldesk.io/geonovum) is an experimental first place to look for metadata, information models, vocabularies, and a metadata model if one is published there. Official Geonovum model and concept services and the publisher's dataset catalog are separate sources.

The public PR confirms a catalog of **domain** models and vocabularies, not a specific published metadata-model artifact or Modeldesk API. The example therefore ships with the built-in metadata model. To switch, find the actual metadata-model artifact in Modeldesk (or another source) and set `metadata_model` to its direct URL or local export, with its expected identity/version where available. Do not use the catalog landing page as the model itself. Label experimental working versions and verify any dataset-to-model binding separately.
