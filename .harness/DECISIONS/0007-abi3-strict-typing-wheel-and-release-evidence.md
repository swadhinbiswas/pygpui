# ADR 0007: Ship GIL-enabled abi3 wheels with reviewed strict stubs

Status: Accepted
Date: 2026-11-24
Deciders: Architect (P0-AR01), under Orchestrator delegation; User retains OQ-03/OQ-04/OQ-10/OQ-11 release approvals.

## Context

`abi3` removes the CPython-minor build dimension, not the OS/architecture dimension. PyO3 0.30.1 defaults to a free-threaded-safety declaration that is not justified for an unaudited UI runtime. Generated stubs exist but are still active development. Maturin can repair wheels and produce attestations, but its ad-hoc Mach-O signing is not Developer ID signing or notarization. No wheel, release channel, remote or signing credential exists.

## Decision

- Target **GIL-enabled CPython 3.11–3.15** provisionally with `requires-python = ">=3.11"`, PyO3 `abi3-py311` and `#[pymodule(gil_used = true)]`. Free-threaded 3.13t/3.14t and `abi3t` are **unsupported and not shipped**.
- Publish one `cp311-abi3` wheel per OS/architecture candidate, plus one rebuildable sdist. Candidate tags are `cp311-abi3-manylinux_2_28_x86_64`, `cp311-abi3-win_amd64` and `cp311-abi3-macosx_26_0_arm64`; actual filenames must be confirmed from pinned maturin output. No Intel/universal2 macOS wheel is planned.
- Package a typed `pygpui/` facade, private `_native` extension, `py.typed`, hand-reviewed public `.pyi` and a private boundary stub. Explicit `__all__` is the public contract. Generated stubs may be produced only as a reviewed diff using the disabled-by-default `stubs` feature.
- Gate typing with mypy 2.4.1 `--strict --disallow-any-explicit --python-version 3.11`, clean installed-wheel consumer tests, and `stubtest` with a tiny reviewed allowlist. No broad `ignore_missing_imports` or package-wide `ignore_errors`.
- No default async runtime or `await app.run()` API. A later non-UI awaitable adapter requires a dedicated main-thread/cancellation spike; it must never schedule Python per frame.
- Build in native OS lanes and the manylinux_2_28 container; repair/audit native dependencies, then test the **same wheel** on CPython 3.11, 3.12, 3.13, 3.14 and 3.15 GIL builds. Linux import tests may include Ubuntu 22.04/24.04, but GUI support remains limited to ADR 0005 candidates.
- Release evidence contains toolchain/lockfile hashes, commands and logs, wheel/sdist SHA-256, tag/suffix inspection, `abi3audit`, repair reports, clean-install/runtime results, SBOM, license files and NOTICE inventory. Use PEP 639 license metadata.
- Wheel/sdist is the first artifact. No app bundle, store submission, PyPI upload, Developer ID/notarization or Authenticode operation is authorized. PyPI Trusted Publishing/attestations, if later enabled, provide provenance, **not OS executable trust**. Local ad-hoc/self-signed tests are explicitly non-release evidence.

## Alternatives considered

- **One universal wheel:** rejected because native OS/architecture artifacts and repair remain necessary.
- **A wheel per CPython minor as the default:** deferred; it multiplies artifacts without a demonstrated `abi3` blocker.
- **Free-threaded launch support:** rejected for the first release pending a separate safety audit, ABI family and interpreter matrix.
- **Unreviewed generated stubs as source of truth:** rejected because the generator can emit incomplete or version-dependent output.
- **Tokio/asyncio owning the desktop loop:** deferred because main-thread co-driving and cancellation are unverified.
- **Treat maturin repair signing as public signing:** rejected; ad-hoc signatures and attestations do not establish Gatekeeper/Authenticode trust.

## Consequences

- One wheel can serve multiple GIL-enabled minors only after each minor is tested; Stable ABI is not a complete behavioral guarantee.
- Manual stubs and consumer fixtures add maintenance but prevent implementation types and `Any` from leaking.
- Public trust and publishing remain blocked independently of build success.
- The provisional Python range and macOS architecture remain product approvals, not achieved support claims.

## Evidence links

- [Skeptic §6 — abi3/typing/release decisions](../REVIEWS/phase-0-research-skeptic.md#6-verified-decision-set-for-architect) and [§8 — Python/release defaults](../REVIEWS/phase-0-research-skeptic.md#8-residual-uncertainties-and-conservative-defaults).
- [RQ-02B C03–C10 — ABI/GIL policy](../RESEARCH/2026-11-24-rq-02-python-abi3-typing.md#b-gil-and-free-threaded-behavior).
- [RQ-02B — strict typing gates](../RESEARCH/2026-11-24-rq-02-python-abi3-typing.md#d-strict-typing-and-public-api-strategy).
- [RQ-02B C28–C36 — repair, signing and attestations](../RESEARCH/2026-11-24-rq-02-python-abi3-typing.md#f-wheel-build-repair-and-signing-constraints).
- [RQ-04B — distribution/signing blockers](../RESEARCH/2026-11-24-rq-04-ime-a11y-distribution.md#credential--or-infrastructure-dependent-operations--blocked).

## Validation gates

- **AR07-G1 — wheel matrix:** pinned maturin builds the three candidate wheels and one sdist; tag/suffix inspection, `abi3audit`, repair/audit and content checks exit zero. No free-threaded or universal2 artifact is present.
- **AR07-G2 — clean installs:** the same wheel imports and runs the Counter smoke test in clean CPython 3.11–3.15 GIL environments on each candidate OS; `py.typed`, stubs and license files are present.
- **AR07-G3 — typing:** mypy strict/explicit-Any and `stubtest` commands exit zero; negative consumer fixtures fail type checking as expected; generated-stub diffs contain no unreviewed `Any`/`Incomplete`.
- **AR07-G4 — runtime:** installed wheels pass ADR 0005 platform gates and ADR 0001 callback gates; an editable/source-tree run is not accepted as release evidence.
- **AR07-G5 — release bundle:** a reproducibility check exits zero and archives hashes, logs, SBOM, notices and test reports. Public signing/publishing remains a separate blocked gate until User supplies channel and credential owners.

## Revisit when

User approves a different Python/OS/architecture floor; a free-threaded safety audit completes; `abi3` testing finds a blocker; or a concrete app-bundle/signing channel is chosen. ABI-family, architecture or signing changes require a superseding ADR and new artifacts/tests.
