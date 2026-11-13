# Subsurface models

Seven draft questions use GeoTOP and REGIS at RD (155000, 463000). The local reference bundle is version `2026-11`; its manifest SHA-256 and model identifiers are in `testset.json`. The bundle is distributed separately and is not included in this repository. A manifest hash identifies the manifest; verifying the files themselves requires checking their checksums against it.

| Sample | Question |
| --- | --- |
| subsurface-01 | Surface elevation and upper GeoTOP units |
| subsurface-02 | Most probable lithoclass in a GeoTOP voxel |
| subsurface-03 | Eem formation in REGIS |
| subsurface-04 | Lithoclass probabilities absent from REGIS |
| subsurface-05 | GeoTOP cross-section picture |
| subsurface-06 | GeoTOP vertical column for an Appelboor |
| subsurface-07 | Limits of line-of-sight evidence for confinement |

The cross-section is scored from the successful `section-plot` call and its JSON and PNG result, not by inspecting the picture. That tool produces a complete plot and has no pagination; `section` is a different, paginated data tool. The vertical-column question scores a `trace` result, not an Appelboor drawing, because the server does not draw one. The scores check selected properties, not all cells or the geological interpretation.

These are test designs, not a deployment configuration: the harness does not yet start the subsurface server, connect Claude Code to it, attribute its calls as an authoritative source, or report response-size metrics. Until that integration is added, run variant `0` only; tool-dependent samples cannot pass on that variant. The `fields` samples can be answered without tools, so an answer from the tool-free model can still be parseable. The reference values and the server's behavior need review before approving the samples.
