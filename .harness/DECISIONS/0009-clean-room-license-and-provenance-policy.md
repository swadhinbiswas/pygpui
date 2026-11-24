# ADR 0009: Require clean-room provenance and artifact-level license closure

Status: Accepted
Date: 2026-11-24
Deciders: Architect (P0-AR01), under Orchestrator delegation; User/counsel retain OQ-08/OQ-13 distribution decisions.

## Context

GPUI and the reviewed frameworks provide architectural prior art, but their source expressions and licenses differ. GPUI is Apache-2.0 at the pinned commit while most Zed source is GPL; no upstream GPUI NOTICE file was found in that snapshot. Direct selected crates have permissive manifests, but the transitive graph is not audited. Winit's Wayland feature includes protocol XML marked LGPL-2.1-or-later despite MIT crate metadata, and the legal effect is unresolved.

## Decision

- Implement from documented behavior and independently written design notes. Do **not** copy or transliterate GPUI or other framework source, comments, shaders, tests, fixtures or assets without an approved provenance exception. Use pygpui-specific names where practical.
- Treat a substantial translation/port or generated derivation as source-derived unless qualified counsel determines otherwise. This is conservative process guidance, not a legal conclusion or a worldwide non-infringement guarantee.
- Any exception requires a provenance record with upstream URL, exact commit/release, path, original copyright/license, modification notice, retained attributions and applicable NOTICE treatment before merge. Restrict study inputs to appropriately licensed components; GPL/AGPL-derived code needs separate explicit approval.
- Maintain `THIRD_PARTY_NOTICES` and a machine-readable provenance/SBOM ledger for direct and transitive code, fonts, assets, generated bindings and any bundled compiler/runtime. Package SPDX/PEP 639 license metadata and required texts.
- Generate the definitive inventory from the committed production lockfile and **actual target/feature artifacts**, not crate metadata alone. No binary distribution occurs until every artifact passes the audit.
- Wayland-enabled binaries are **not license-cleared for a permissive-only distribution** until upstream clarification or qualified counsel plus the artifact audit resolves the mixed-license protocol content. An X11-only preview may reduce scope but is not a general Linux support claim.
- Do not depend on GPUI source or binary. Concept reuse does not waive obligations if source is later copied; Apache-2.0 license/change notices and any actual upstream NOTICE must then be propagated.
- Public signing, notarization and publishing remain blocked under ADR 0007; provenance/attestations do not substitute for OS trust or license review.

## Alternatives considered

- **Copy selected GPUI implementations to move faster:** rejected because it triggers provenance and Apache-2.0 obligations and expands the unaudited dependency boundary.
- **Infer license safety from repository labels or crate manifests alone:** rejected because file-level and transitive licenses differ, as the Wayland XML discrepancy demonstrates.
- **Ship Wayland with a “permissive-only” claim before review:** rejected; the legal effect is unresolved.
- **Defer all notice work until release:** rejected because provenance cannot be reconstructed reliably after implementation.
- **Claim legal clearance from this ADR:** rejected; the policy is a risk control, not legal advice.

## Consequences

- Clean-room implementation may be less idiomatic than adapting upstream code and requires disciplined design notes.
- Every dependency, font, asset and generated artifact adds audit work; the Wayland question can block a Linux distribution lane.
- Source-derived exceptions become slower and review-heavy, which is intentional.
- No current transitive license closure, NOTICE inventory or legal sign-off exists.

## Evidence links

- [RQ-01A C-25–C-32 — clean-room and Apache-2.0 boundaries](../RESEARCH/2026-11-24-rq-01-gpui-internals.md#6-clean-room-and-apache-20-boundaries).
- [RQ-01B R7 — file-level prior-art licenses](../RESEARCH/2026-11-24-rq-01-cross-framework.md#recommendation).
- [RQ-02A — license/NOTICE implications and Wayland discrepancy](../RESEARCH/2026-11-24-rq-02-core-rust-stack.md#license-and-notice-implications).
- [Skeptic §8 — clean-room, transitive audit and Wayland defaults](../REVIEWS/phase-0-research-skeptic.md#8-residual-uncertainties-and-conservative-defaults).
- [`.harness/OPEN_QUESTIONS.md` OQ-08/OQ-13](../OPEN_QUESTIONS.md).

## Validation gates

- **AR09-G1 — provenance review:** a pre-merge audit exits zero with a complete ledger; any source-derived file links to an approved exception containing the required fields. Unapproved copied/translated expression blocks merge.
- **AR09-G2 — dependency closure:** `cargo metadata --locked` feeds a pinned license/advisory scanner and artifact SBOM generator; the command exits zero with no unreviewed license, source or advisory exception for each target/feature build.
- **AR09-G3 — notices:** a wheel/sdist content audit exits zero, proving required license/copyright texts, `THIRD_PARTY_NOTICES`, font/asset licenses and PEP 639 metadata are present and match the SBOM.
- **AR09-G4 — Wayland distribution:** permissive-only Wayland publication remains blocked until documented upstream clarification or qualified-counsel review and AR09-G2/G3 evidence are archived.
- **AR09-G5 — source exception:** any future copied/adapted code requires legal/provenance approval, modified-file notices and a recheck of the exact upstream archive for NOTICE before merge or distribution.

## Revisit when

A dependency, font, asset, compiler bundle or feature changes; an artifact scanner finds a new license; upstream resolves the Wayland protocol question; or source reuse is proposed. License closure is per artifact and must be repeated after repair, stripping, bundling or repacking.
