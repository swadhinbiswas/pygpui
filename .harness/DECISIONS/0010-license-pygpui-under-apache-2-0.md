# ADR 0010: License pygpui under Apache-2.0

Status: Accepted
Date: 2026-11-24
Deciders: Architect (P0-AR01), under Orchestrator delegation; any future relicensing requires User approval and a superseding ADR.

## Context

ADR 0009 decides provenance and third-party license closure, but it does not license pygpui itself. The supplied mission text ends at the Phase 0 heading and states no project license, so this is a conservative product-policy decision rather than an existing user requirement. The planned artifact is a reusable Python/Rust UI framework distributed as wheels and an sdist. The verified direct dependency baseline is permissive (Apache-2.0, MIT, dual MIT/Apache-2.0 and Zlib), although the transitive graph and Wayland protocol content remain unaudited. A project license should permit broad downstream reuse, provide clear contribution and redistribution terms, and fit the existing provenance process without creating an unnecessary copyleft or dual-license burden.

## Decision

- License pygpui-authored source code, documentation, examples, tests and generated public stubs under **Apache-2.0 only**, using the SPDX identifier `Apache-2.0`.
- Add the complete official Apache-2.0 text as `LICENSE`. The project owner must supply the correct copyright holder notice before first distribution; this ADR does not invent one. Add a project `NOTICE` only when the project has actual attributions to propagate, and keep third-party attributions in `THIRD_PARTY_NOTICES` under ADR 0009.
- Set every workspace crate to `license = "Apache-2.0"` with `license-files = ["LICENSE"]`. Publish Python Core Metadata `License-Expression: Apache-2.0` and `License-File: LICENSE` under PEP 639, and include the license files in both wheel and sdist.
- Accept external contributions under Apache-2.0, with contributors retaining copyright. No separate CLA is selected by this ADR; contribution terms must state the inbound license before external contributions are accepted.
- Third-party code, fonts, assets and generated bindings retain their own licenses and notices. Apache-2.0 for pygpui does not relicense dependencies, resolve the Wayland mixed-license question, grant trademark rights or establish patent clearance.
- Source-derived exceptions remain governed by ADR 0009, including exact provenance, modified-file notices and any applicable upstream NOTICE. Distribution still requires the ADR 0009 artifact audit.

## Alternatives considered

- **MIT only:** simpler and widely used, but lacks Apache-2.0's explicit contributor patent grant and provides less uniform alignment with several selected dual-licensed/Apache dependencies. It remains a reasonable future choice if minimal obligations outweigh patent clarity.
- **Dual `MIT OR Apache-2.0`:** common in the Rust ecosystem and gives downstream license choice, but creates two project license paths and complicates a single contribution, NOTICE and release-metadata policy without a demonstrated need.
- **GPL/AGPL or another copyleft license:** would impose reciprocal distribution terms on downstream users and complicate combination with permissive dependencies; that is a poor conservative default for a reusable framework distributed as ordinary Python wheels.
- **Proprietary/source-available terms:** would constrain the reuse and community contribution assumed by the wheel/sdist plan and require a separate business and legal decision.
- **Leave the project unlicensed pending release:** rejected because ambiguity blocks safe contribution, reuse and distribution; an explicit permissive default is easier to revisit than implicit all-rights-reserved status.

## Consequences

- **Positive:** downstream users can incorporate pygpui into proprietary or open products without copyleft relicensing; contributors receive explicit patent-license terms; redistribution and NOTICE handling match ADR 0009 and PEP 639.
- **Negative:** the project must maintain license files, metadata, contribution terms and notices; Apache-2.0's patent grant has termination conditions and is not a warranty of non-infringement; others may create competing offerings from the code.
- The choice does not make every distributed artifact permissively licensed: transitive dependencies, fonts and the unresolved Wayland content still control their own obligations and can block a release lane.

## Evidence links

- [Apache License 2.0 — grants, redistribution, NOTICE and trademark terms](https://www.apache.org/licenses/LICENSE-2.0).
- [RQ-01A C-26–C-32 — verified Apache-2.0 obligations and clean-room limits](../RESEARCH/2026-11-24-rq-01-gpui-internals.md#6-clean-room-and-apache-20-boundaries).
- [RQ-02A — direct permissive licenses and unresolved transitive/Wayland scope](../RESEARCH/2026-11-24-rq-02-core-rust-stack.md#license-and-notice-implications).
- [RQ-02B C36 and PEP 639 — license expression/files in package metadata](https://peps.python.org/pep-0639/).
- [ADR 0007 — wheel/sdist release evidence](0007-abi3-strict-typing-wheel-and-release-evidence.md) and [ADR 0009 — provenance and artifact closure](0009-clean-room-license-and-provenance-policy.md).
- [`.harness/OPEN_QUESTIONS.md` OQ-01/OQ-08/OQ-13](../OPEN_QUESTIONS.md).

## Validation gates

- **AR10-G1 — repository metadata:** `cargo metadata --no-deps --format-version 1` and built-wheel metadata checks exit zero with `Apache-2.0` for every pygpui workspace crate and Python `License-Expression`; the packaged `LICENSE` matches the pinned official Apache-2.0 text and the owner-supplied copyright notice.
- **AR10-G2 — artifact contents:** wheel and sdist content audits exit zero, proving `LICENSE`, any project `NOTICE`, `THIRD_PARTY_NOTICES`, PEP 639 metadata and the ADR 0009 SBOM are present and consistent; no third-party file is relicensed to Apache-2.0.
- **AR10-G3 — scope and contributions:** a repository audit exits zero with every authored file covered by Apache-2.0 or an explicit approved exception; contribution documentation states the Apache-2.0 inbound license before external contributions are accepted.
- **AR10-G4 — compatibility and wording:** ADR 0009's dependency/notice gates pass for each artifact; release documentation makes no patent-clearance, trademark, worldwide-clean-room or permissive-only Wayland claim. The Wayland distribution block remains independent of this project license.

## Revisit when

User requirements call for a different licensing or business model; downstream adoption shows a concrete need for dual licensing; a dependency/asset requires incompatible terms; or qualified counsel recommends a change. Relicensing requires a superseding ADR, copyright-holder approval and a migration plan for existing contributions and distributed artifacts.
