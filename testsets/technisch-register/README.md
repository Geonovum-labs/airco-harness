# Test set technisch-register

Questions an agent answers to make the metadata of one repository: [Geonovum/technisch-register-2019](https://github.com/Geonovum/technisch-register-2019), the PHP site of register.geostandaarden.nl. The metadata are an SBOM, following the 2026 CISA minimum elements in CycloneDX 1.7, and a publiccode.yml, following version 0.7 of the standard.

| Sample | Question | Rule |
| --- | --- | --- |
| `sbom-01` | Which third-party components the repository bundles or its pages load, with their versions | `components` |
| `sbom-02` | The VEX status of three CVEs of the bundled jQuery 1.9.1 | `fields` |
| `publiccode-01` | License, copyright owner, software type and landing URL for publiccode.yml | `fields` |

Every question names commit `7cc32f9`, the last commit before the repository got a publiccode.yml and SBOMs in [Geonovum/technisch-register-2019#13](https://github.com/Geonovum/technisch-register-2019/pull/13). The files the expected answers come from are vendored at that commit in `sources/technisch-register-2019/`, and `tests/test_testset.py` checks each expected answer against them. The SBOM and the publiccode.yml in #13 hold the answers, so the allowlist counts a retrieval of them, or of the fork they were made in, as non-authoritative.

The expected answers are the results of the skill `geonovum-sbom` ([fterpstra/skill-SBOM](https://github.com/fterpstra/skill-SBOM)), whose eval `vendored-php-no-lockfile` uses the same repository, and of the publiccode.yml that the repo-docs-generator made, with the license corrected by hand. The samples have `status: draft` and name no defect, because the defects G1 to G13 belong to the IMGeo test set note. The version is in `testset.json`.
