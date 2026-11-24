# RQ-04B — IME, accessibility and cross-platform distribution

| Field | Value |
|---|---|
| Task | P0-R04B, Round 1, attempt 1 |
| Researcher | Researcher-Platform instance B |
| Date / evidence cutoff | 2026-11-24 |
| Status | Complete — research only |
| Scope | IME lifecycle, keyboard/focus, AccessKit ownership, abi3 wheels, CI, signing/notarization, Linux packaging |
| Related question | `.harness/RESEARCH/RQ-04-platform-input-accessibility-distribution.md` |
| Local authority | `.harness/STATE.md`, assigned handoff, `.harness/PROCESS.md` |

## Bottom line

Use Rust as the sole owner of native window/input/accessibility state and of a canonical accessibility mirror; let Python describe semantics and receive actions, but do not call Python from platform accessibility threads. Treat IME as the only text-input path for editable controls, keep an explicit composition/focus state machine, and require real OS tests before claiming IME or accessibility support. Ship GIL-enabled `abi3` wheels per OS/architecture, not one universal wheel. Native wheel builds do not require signing credentials, but public macOS app signing/notarization, Windows Authenticode signing, store submission and PyPI publishing are blocked until the user supplies the relevant accounts and credentials.

The conservative first public support claim should be **macOS 26 on both Intel and Apple Silicon, Windows 11 25H2/26H2 x64, and Ubuntu 24.04 LTS x86_64 with GNOME Wayland plus X11**, using CPython 3.11–3.15 GIL builds and `abi3-py311`. This is a proposed support policy, not a tested compatibility claim.

## Evidence labels

Labels follow `.harness/PROCESS.md`:

- **verified** — supported by a dated primary source or reproducible local observation.
- **plausible** — indirect evidence or an integration inference; requires a validation task.
- **unverified** — assumption, stale evidence, or not yet tested.

Living documentation is cited with its version/date where available and an access date of 2026-11-24. Open issues are evidence of reported limitations, not proof that every installation fails.

## Claim register

| ID | Label | Claim | Primary evidence | Decision consequence |
|---|---|---|---|---|
| IME-01 | **verified** | winit IME is opt-in through `Window::set_ime_allowed`. The documented lifecycle is `Enabled`, zero or more `Preedit`, a `Commit`, then `Disabled`; a commit is preceded by an empty preedit. During preedit, winit documents that `KeyboardInput` is suppressed. macOS requires IME for combined dead-key text. X11 supports IME position but not the cursor-area size. | S01, S02 | Model these states explicitly; never insert text from raw key events while an editable target owns IME. |
| IME-02 | **verified** | The current Windows implementation does not uniformly satisfy the documented suppression rule: winit issue #4508 reports `KeyboardInput` during IME composition on Windows 11 25H2 with winit 0.30.13 and remains open. | S05 | Do not rely on the generic documentation as a cross-platform guarantee. Filter/gate raw key handling and test Windows composition. |
| IME-03 | **verified** | Current macOS 0.30.13 evidence includes an open Kotoeri conversion/commit-loss report (#4807) and an open active-composition window-teardown abort report (#4626). The latter reports that disabling IME before teardown prevented the abort in 20/20 runs. | S06, S07 | Full Japanese IME and close-during-composition support cannot be claimed without physical-Mac tests and an explicit teardown workaround. |
| IME-04 | **verified** | For an input-target or text-caret change during composition, winit maintainers recommend disable/enable rather than only moving the cursor area. Issue #4220 was closed after `request_ime_update` work, but that work is not present in the inspected stable 0.30.13 API. | S02, S08 | On stable 0.30.13, use a sequenced disable → clear → re-enable flow with an application request token; validate race behavior on each OS. |
| IME-05 | **verified** | `Ime::Preedit` cursor offsets are UTF-8 byte offsets, not Python code-point indices or UTF-16 indices. An empty preedit clears the composing text; `None` means hide the cursor. | S01 | Convert Python/editor offsets to UTF-8 bytes exactly once at the Rust boundary. Include CJK and emoji tests. |
| KBD-01 | **verified** | `WindowEvent::Focused` and `Window::has_focus` expose the same native window-focus state. Synthetic press/release reconciliation on focus transitions is documented only for X11 and Windows. | S02, S03 | Clear pressed-key and composition state on every focus loss; do not depend on synthetic releases on macOS or Wayland. |
| KBD-02 | **verified** | `physical_key` is layout-independent; `logical_key` is affected by modifiers except Ctrl and is layout-sensitive. winit recommends configurable keybinds. Windows can emit unmarked fake key events for Shift/NumLock behavior. | S03 | Use physical keys only where position-based input is intended, logical keys for shortcuts, and provide remapping. Test NumLock/Shift separately. |
| A11Y-01 | **verified** | AccessKit's provider pushes an initial full tree and then incremental `TreeUpdate`s. Only the platform adapter needs to retain the complete tree. Stable `NodeId`s are required; `TreeUpdate.focus` must carry the latest focus on every update. | S09, S10, S12, S13 | Rust should maintain stable node identity, focus and diffing. Python may provide semantic snapshots, but must not become the OS-tree owner. |
| A11Y-02 | **verified** | `accesskit_winit::Adapter` must be created before the window is first shown, and `process_event` must be called for every window event before application handling. Constructors panic if the window is already visible. | S14 | Create windows invisible, attach AccessKit, then show. Forward events in one centralized Rust event boundary. |
| A11Y-03 | **verified** | Initial-tree requests may repeat. An asynchronous full tree is due no later than the next display refresh. Activation/action/deactivation callbacks may run on platform-dependent threads; action requests may be queued and asynchronous handling is preferred. | S11, S14, S15 | Prefer an event-loop proxy initially so Python is never called on an arbitrary adapter thread. Send the full tree immediately on request; benchmark a direct/mixed activation handler later if needed. |
| A11Y-04 | **plausible** | A safe Python/Rust split is: Python declares roles, labels, values, bounds and supported actions; Rust owns node IDs, focus, IME, adapter lifetime, tree diffing and action dispatch; accessibility actions return to the main event loop before Python is invoked. | Inference from S09–S15 | This avoids cross-thread Python calls and duplicate focus state, but needs a prototype and latency tests. |
| A11Y-05 | **verified** | AccessKit adapters are explicitly best-effort and do not cover every platform API. A current open Windows issue (#840) reports missing `UIA_HeadingLevelPropertyId`, preventing Narrator heading navigation despite a heading role and level. | S10, S16 | Integrating AccessKit is not a WCAG/conformance claim. Test concrete roles/properties/actions with real assistive technology. |
| A11Y-06 | **unverified** | The current Linux adapter may still lazily wait for AT-SPI `IsEnabled`; a January 2025 maintainer discussion records Accerciser not activating the tree and Orca doing so. The discussion does not establish the behavior of accesskit_unix 0.24.1 in November 2026. | S17; version inspected in S18 | Test both Orca and an inspector on the pinned version. Do not treat an empty inspector tree as proof that the provider sent no tree. |
| DIST-01 | **verified** | `abi3` removes the CPython-minor dimension only. PyO3 states that one copy is needed for each OS/architecture; platform tags still encode OS, minimum system version and architecture. | S19, S21 | Build separate macOS, Windows and Linux wheels; `abi3` is not a universal binary format. |
| DIST-02 | **verified** | Free-threaded CPython cannot load GIL `abi3` wheels. Current PyO3/maturin documentation describes version-specific free-threaded wheels and a newer `abi3t` path with version-specific availability. | S19, S20 | Exclude all free-threaded (`3.14t`/`3.15t`) and `abi3t` artifacts from the first release. Pin a compatible PyO3/maturin pair before implementation. |
| DIST-03 | **verified** | PyO3 extension filenames differ by OS: `.so` on macOS/Linux and `.pyd` on Windows. macOS extension modules do not link `libpython`; Windows uses MSVC/raw-dylib-oriented tooling. macOS supports `universal2`; Windows ARM64 is marked experimental by cibuildwheel. | S19, S23 | Keep native build recipes and smoke tests OS-specific. Start with Windows x64 and macOS universal2. |
| DIST-04 | **verified** | Public Linux wheels use manylinux/musllinux policies and dependency auditing. Maturin says a plain `linux` tag is rejected by PyPI. PEP 600 explicitly excludes CUDA/external-dependency policy from manylinux's scope. | S20, S36 | Build in a manylinux container and audit dependencies. A manylinux tag does not certify GPU drivers, X11/Wayland, IME or accessibility. |
| CI-01 | **verified** | cibuildwheel requires macOS builds to run on macOS with Xcode tools and Windows builds on Windows with MSVC; Linux builds run in Docker/Podman. | S23 | Do not make Linux the sole build host for the release matrix. Cross-compilation is not a substitute for native runtime tests. |
| CI-02 | **verified** | Current GitHub-hosted runner documentation includes `macos-26`/`macos-latest` on arm64, `macos-26-intel`, `windows-2025`, `windows-11-arm`, and Ubuntu 22.04/24.04/26.04 labels. It also warns that community actions may not support arm64 macOS. | S24 | Pin explicit runner labels and audit third-party actions; do not rely on `latest` aliases for reproducibility. |
| CI-03 | **plausible** | Hosted build/import jobs cannot prove real IME, VoiceOver/Narrator/Orca behavior, candidate-window placement or multi-display HiDPI correctness. | Inference from S01–S18 and S31–S33 | Use hosted runners for reproducible builds and clean imports; use physical/self-hosted interactive desktops for certification. |
| SIGN-01 | **verified** | Apple direct distribution requires Developer ID signing, hardened runtime, a secure timestamp and notarization. `notarytool` or the Notary API submits software; the ticket must be stapled to the distributed container for offline Gatekeeper use. | S25–S27 | A public macOS app bundle/DMG/PKG is not release-ready merely because its wheel built successfully. |
| SIGN-02 | **verified** | Apple silicon requires all executable code to be signed; an ad-hoc signature is sufficient for local execution but cannot pass Gatekeeper. Modifying a binary after linking can require re-signing. | S28 | Verify signatures after repair/strip/packaging steps, for both universal2 architectures. |
| SIGN-03 | **verified** | Microsoft recommends signing every supported executable artifact, not only the installer. SignTool needs a code-signing certificate/private key and RFC 3161 timestamp; warnings should fail release automation unless reviewed. Self-signed certificates are for development/testing, not public distribution. | S29, S30 | Sign EXE/DLL/installer artifacts and verify them on a clean Windows machine. Do not equate a self-signed local test with public trust. |
| SIGN-04 | **verified** | PyPI Trusted Publishing uses OIDC short-lived credentials and avoids long-lived API tokens. PyPI supports publish/SLSA attestations, and the official publish action generates them by default. | S34, S35 | Prefer a protected GitHub release environment plus PyPI Trusted Publishing; still blocked until the project/publisher exists. |
| BLOCK-01 | **verified** | The supplied handoff states that no signing/notarization/store credentials or remote release infrastructure were provided; `STATE.md` records no Git remote. | L01, L02 | Actual signing, notarization, store submission, PyPI upload and remote CI execution are blocked, not silently assumed. |
| REL-01 | **plausible** | The narrow credible first support matrix is macOS 26 universal2, Windows 11 25H2/26H2 x64, Ubuntu 24.04 LTS x86_64 GNOME Wayland/X11, CPython 3.11–3.15 GIL, `abi3-py311`, manylinux_2_28. | Policy inference from S19–S24, S37, S38 | Architect/User must approve. Certify only these configurations; broader installability is not a support promise. |
| LINUX-01 | **verified** | A Python wheel is an installable package archive, not a complete desktop application bundle. Freedesktop desktop entries are a separate standard for launch/menu integration. | S22, S39 | First Linux release should be sdist + audited wheel. Defer AppImage/Flatpak/deb/rpm and desktop integration until there is a concrete end-user app requirement. |
| REL-02 | **plausible** | The final macOS application bundler, not the Python wheel build alone, owns final nested-code signing and notarization. | Inference from S20 and S25–S28 | Define a separate signed-app release lane. Do not claim a PyPI wheel is notarized. |

## Technical requirements versus blocked operations

### Technical requirements — implementable without release credentials

These are future engineering requirements. None was implemented in this research task, and Phase 0 still prohibits feature implementation.

| Requirement | Minimum acceptance evidence |
|---|---|
| Central Rust input boundary | Every winit event reaches one owner; `Focused`, `KeyboardInput`, `Ime`, resize/scale and destroy events update one state machine. |
| IME state machine | Explicit enabled/preedit/commit/disabled state, UTF-8 byte offsets, direct-commit handling, focus-transfer sequencing, external-disable handling, and pre-close IME disable. |
| Keyboard/focus reconciliation | Pressed-key set clears on focus loss on every platform; repeats and synthetic events are identified; shortcuts are configurable; text insertion never duplicates `Ime::Commit`. |
| AccessKit provider/adapter split | Adapter exists before show; every event is forwarded before app handling; initial full tree and incremental updates are correct; action requests are queued to the main loop. |
| Stable accessibility identity | Node IDs survive updates; removal of a focused node moves focus to a valid node; reading/navigation order is intentional; labels do not become tab stops merely to make them readable. |
| Platform wheel builds | Native macOS/Windows builds and manylinux container build produce the expected tags and extension suffixes; dependency repair/audit succeeds. |
| Clean artifact tests | Install the built wheel, not an editable tree, into a clean environment; import and open a real window on minimum and maximum supported CPython. |
| Unsigned/ad-hoc local packaging | Local app/installer artifacts can be built and exercised with development-only signatures where required. These are not public-release artifacts. |
| Supply-chain metadata | Locked dependencies, build logs, hashes, SBOM and provenance/attestation generation can be prepared without owning release accounts. |

### Credential- or infrastructure-dependent operations — blocked

| Operation | Missing dependency | Current status |
|---|---|---|
| Developer ID signing and Apple notarization | Apple Developer Program/Account Holder, Developer ID Application/Installer certificates and private keys, `notarytool` app-specific password or App Store Connect API key/issuer/team ID | **Blocked — not attempted** |
| Mac App Store submission | App Store Connect access, bundle ID, distribution certificate/provisioning/profile, store metadata and review account | **Blocked — out of first-release scope** |
| Windows Authenticode public signing | Trusted code-signing certificate/private key or managed signing account, timestamp/network policy, protected CI secret storage | **Blocked — not attempted** |
| Microsoft Store/MSIX submission | Partner Center account, package identity, listing and certification setup | **Blocked — out of first-release scope** |
| PyPI publication | PyPI project ownership and Trusted Publisher configuration, or a project API token; GitHub repository/remote and protected release environment | **Blocked — no remote or project configured** |
| Linux repository/store publication | Target repository/Flatpak/AppImage store account and signing keys; distro maintainer process | **Blocked — not attempted; no standalone Linux bundle planned** |
| Interactive certification runners | Physical Macs on both architectures, Windows 11 desktop, Linux GNOME/KDE desktops, configured IMEs and assistive technologies | **Blocked as infrastructure; local/manual evidence required** |

A development self-signed certificate or ad-hoc signature may exercise local mechanics, but it must not be recorded as public signing/notarization success.

## IME and focus integration contract

1. **Editable target owns IME.** On focus entering an editable control, enable IME and publish the caret/candidate area in one consistent coordinate system. Update the area after caret movement, scrolling, resize and scale-factor changes. On focus leaving, disable IME and clear preedit.
2. **Text has one source.** While IME is allowed, insert text only from `Ime::Commit`. `KeyboardInput` may drive non-text controls, but it must not also insert text. This is required because current Windows behavior contradicts the generic winit documentation (IME-02).
3. **Composition gates action keys.** Candidate selection, Enter, Space, arrows and Backspace must not simultaneously activate application shortcuts or move the editor cursor. The exact gate must be tested per IME because an empty `Preedit` is ambiguous and direct commits are possible.
4. **Focus transfer is sequenced.** For stable winit 0.30.13, use a request generation: mark the old target inactive, request IME disable, clear pending preedit, handle `Disabled`, then enable the new target and set its caret area. Ignore stale events from an older generation. This is a **plausible** integration design until tested.
5. **Focus loss is a hard reset.** Clear pressed keys and preedit even if the OS does not send synthetic releases. Preserve the application's selected focus target so focus can be restored, but do not claim native focus while `Focused(false)` is current.
6. **Teardown is explicit.** Before dropping a macOS window with active composition, call `set_ime_allowed(false)` while the window is still alive. This is a reported workaround for #4626, not an upstream fix.
7. **Offset contract is UTF-8 bytes.** Document this at the Python/Rust boundary. Convert from Python string indices in Rust and test non-BMP characters, combining marks and CJK text.

## Accessibility-tree ownership

### Recommended ownership boundary

| Layer | Owns | Must not own |
|---|---|---|
| Python application | Declarative semantics, labels, values, action intent, application focus policy | Native adapter lifetime, OS focus, raw IME state, direct calls from AT threads |
| Rust framework | Window/event loop, IME state, native focus reconciliation, stable `NodeId`s, bounds in the required coordinate space, full/incremental `TreeUpdate`s, action validation and dispatch | Python object mutation on arbitrary threads |
| AccessKit adapter | Platform accessibility bridge and retained complete tree | Application semantics or business logic |

This split is **plausible** and should be prototyped before becoming an ADR. It follows AccessKit's provider/adapter model and avoids invoking Python from platform-dependent callback threads.

### Conservative adapter choice

- Prefer `accesskit_winit` because AccessKit recommends it for winit. `accesskit_xplat` is a fallback for winit-version mismatch, not the default.
- Start with `Adapter::with_event_loop_proxy`: it keeps all application handling on the winit loop. The tradeoff is a possible temporary placeholder tree; respond immediately with a full tree.
- Consider `with_mixed_handlers` only after measuring whether synchronous initial-tree generation is needed. Any direct activation handler must read an immutable Rust-owned snapshot and must not call Python.
- Do not adopt winit 0.31 beta solely for newer IME APIs in the first release. Use the stable API plus explicit sequencing, then re-evaluate after a stable release.

### Accessibility release gate

An AccessKit integration is successful only when all of the following are demonstrated on each supported OS:

- Correct role, name, value, state, bounds and supported actions in the native accessibility API.
- Keyboard-only completion of the primary workflow.
- Screen-reader navigation and action invocation, not merely a populated inspector tree.
- Focus follows application focus and returns to a valid node after removal/closure.
- Dynamic updates do not erase unchanged properties.
- Text input and IME composition remain usable with the screen reader enabled.
- A 10,000-row virtualized list has a deliberate accessible representation and usable scrolling; exposing only painted pixels is not sufficient.

The virtualized-list representation is **unverified** until designed and tested. A conservative first implementation should expose the visible range plus total row/column metadata and scroll actions, but this must be validated with VoiceOver, Narrator and Orca.

## Wheel and platform-tag defaults

| Target | Proposed artifact | Technical notes |
|---|---|---|
| macOS 26, Intel + Apple Silicon | `cp311-abi3-macosx_26_0_universal2.whl` | One `abi3` wheel per OS/arch set; verify both Mach-O slices, deployment target and signatures after repair. Lower the deployment target only after tests on those older OS versions. |
| Windows 11 x64 | `cp311-abi3-win_amd64.whl` | Build with MSVC. Do not claim Windows ARM64 while cibuildwheel marks it experimental and no native certification exists. |
| Linux x86_64 glibc | `cp311-abi3-manylinux_2_28_x86_64.whl` | Build in the official manylinux_2_28 container; run auditwheel and clean import tests. Do not publish a plain `linux_x86_64` wheel to PyPI. |
| All supported targets | One sdist | Required for source builds and downstream distro packaging. Verify the sdist can rebuild the wheel. |
| Free-threaded CPython | No first-release wheel | `cp314-cp314t-*` would be a separate version-specific artifact; `abi3t` is deferred. |
| PyPy/GraalPy/musl/32-bit/other CPU arches | No first-release claim | Add only with separate dependency, runtime and OS evidence. |

The exact filenames are proposed defaults, not observed build outputs. Confirm them with the pinned maturin/PyO3 versions and `packaging.tags`/pip before publication.

## CI design and runner defaults

| Lane | Hosted runner / environment | What it proves | What it does not prove |
|---|---|---|---|
| Linux wheel build | `ubuntu-24.04` + manylinux_2_28 container | Reproducible glibc wheel, dependency audit, clean import | Wayland/X11, GPU driver, IME, Orca |
| macOS wheel build | `macos-26` arm64; `macos-26-intel` import smoke | Build, tags, both architecture import paths, repair | Physical candidate-window/IME/VoiceOver behavior |
| Windows wheel build | `windows-2025` x64 | MSVC build, dependency repair, clean import | Desktop IME, Narrator, HiDPI, clean-machine trust |
| Interactive certification | Physical/self-hosted desktops | IMEs, assistive technology, multi-display behavior, signed artifact installation | Broad distro/hardware coverage |

Use explicit runner labels rather than `macos-latest` or `windows-latest` in release workflows. Keep build jobs separate from publishing jobs, download already-built artifacts into a protected publishing environment, and use PyPI Trusted Publishing. No workflow was created or executed in this task.

## Platform-specific integration tests

### Cross-platform automated tests

| Test | Pass criterion |
|---|---|
| IME event-sequence unit tests | Enabled → Preedit → empty Preedit → Commit → Disabled produces exactly one insertion; direct Commit without prior nonempty preedit also works. |
| UTF-8 offset tests | CJK, emoji and combining-mark offsets round-trip between Python strings, Rust strings and winit byte ranges without slicing panics. |
| Focus-transfer race tests | Rapid A → B → C focus changes cannot deliver a commit/preedit to the wrong target; stale `Disabled` events do not cancel the current target. |
| Focus-loss reconciliation | Held keys do not remain stuck on macOS/Wayland when no synthetic release arrives. |
| Keyboard semantics | AZERTY/QWERTY remapping, Ctrl vs other modifiers, key repeat, Shift/NumLock fake events and physical/logical key expectations are covered. |
| AccessKit tree-state tests | Apply full and incremental updates to `accesskit_consumer::Tree`; unchanged fields remain intact; removal/addition/focus changes produce the intended tree. |
| Action routing | Unsupported actions are ignored; supported actions reach the main loop once and update state/tree without cross-thread Python calls. |
| Artifact tests | `abi3audit`, auditwheel/delocate/delvewheel checks, wheel-tag inspection, clean install/import, and minimum/maximum CPython smoke tests pass. |

### macOS — physical Intel and Apple Silicon

- Run as a real `.app` bundle so Accessibility Inspector can inspect it.
- Enable/disable VoiceOver before launch and during runtime; verify initial tree, dynamic updates, focus restoration, roles/names/states, action invocation and text editing.
- Test US dead keys, Chinese Pinyin, Japanese Kotoeri Romaji and Korean 2-Set. Include candidate navigation, commit, cancel, input-source switching and moving focus between two fields mid-composition.
- Reproduce the scenarios in winit #4807 and #4626. Close the window while marked text is active and confirm the explicit disable workaround prevents an abort.
- Move a window between Retina and non-Retina displays; verify candidate-window/caret placement and accessibility bounds after scale changes.
- For signed releases, verify `codesign`, hardened runtime, timestamps, both universal2 slices, notarization log, stapled ticket, `spctl` assessment, offline launch, translocation, upgrade and duplicate-version installation.

### Windows — Windows 11 25H2 and 26H2 x64

- Use Narrator and Accessibility Insights for Windows; inspect UI Automation properties, events and control patterns.
- Verify heading levels, text controls, focus, values/states, action invocation and the virtualized list. Track AccessKit #840 rather than assuming heading navigation works.
- Test Japanese/Chinese/Korean IMEs, direct commits, candidate selection, focus transfer and cancellation. Specifically detect raw `KeyboardInput` during composition (#4508) and ensure it never duplicates text or triggers button shortcuts.
- Test Shift/NumLock fake events, key-repeat and focus loss.
- For signed releases, run `signtool verify /pa /v` on every executable artifact, treat warnings as failures, install on a clean VM, and test upgrade/uninstall and SmartScreen/UAC behavior.

### Linux — Ubuntu 24.04 LTS x86_64, GNOME Wayland and X11

- Test IBus and Fcitx5 input methods, preedit/commit/cancel, candidate placement and focus transfer on both Wayland and X11. X11 cursor-area size is not supported, so position is the pass criterion.
- Run Orca with a real AT-SPI session bus; verify roles, names, reading order, keyboard navigation, actions, text input and dynamic updates.
- Test the inspector separately with AT-SPI `IsEnabled` set, because historical AccessKit behavior may not expose the tree to Accerciser otherwise. Record the pinned adapter version and exact workaround.
- Launch with no assistive technology and confirm the application remains usable and accessibility activation does not regress idle/frame behavior.
- Run clean manylinux-wheel import tests on Ubuntu 22.04 and 24.04 to validate the glibc promise, while limiting the public GUI support claim to Ubuntu 24.04 until broader desktops are tested.
- If a standalone Linux bundle is later required, validate the `.desktop` file with `desktop-file-validate`, install icons/metadata correctly, and test launch from the desktop environment. This is separate from wheel acceptance.

## Conservative release defaults

| Area | Default | Label |
|---|---|---|
| Python | CPython 3.11–3.15, GIL-enabled only, `abi3-py311` | **plausible** |
| macOS | macOS 26, universal2, certify Intel + Apple Silicon | **plausible** |
| Windows | Windows 11 25H2 and 26H2, x64 only | **plausible** |
| Linux | Ubuntu 24.04 LTS x86_64, GNOME Wayland + X11; manylinux_2_28 wheel | **plausible** |
| Other platforms | No first-release claim for Windows 10/24H2 Home/Pro, macOS 14/15, musl, ARM64 Windows/Linux, 32-bit, PyPy/GraalPy or free-threaded Python | **plausible** |
| winit | Stable 0.30.13 or a later stable release that passes the IME regression suite; no beta-only API dependency | **plausible** |
| AccessKit | `accesskit_winit` with the compatible stable AccessKit release; event-loop proxy first | **plausible** |
| Input | IME is the only editable-text path; explicit focus/teardown reset; UTF-8 byte offsets | **verified** requirement, **plausible** implementation |
| Accessibility | No WCAG/conformance claim from tree integration alone; real AT tests are a release gate | **verified** limitation, **plausible** gate |
| Linux packaging | sdist + audited manylinux wheel; defer standalone bundle/store packaging | **plausible** |
| Signing | Public macOS/Windows artifacts remain blocked; local ad-hoc/self-signed tests are clearly labeled non-release | **verified** blocker |
| Publishing | Protected release environment + PyPI Trusted Publishing/attestations once a remote and project exist | **verified** mechanism, **blocked** operation |

Windows 11 24H2 Home/Pro reached end of servicing in October 2026, while Enterprise servicing has a different lifecycle (S37). macOS 14/15 may remain usable, but the proposed first support claim is deliberately narrower until tested. Installability of an older-tagged wheel must not be confused with supported status.

## Contradictions and source-freshness risks

1. **winit documentation versus Windows behavior.** The generic API says preedit suppresses `KeyboardInput`; open issue #4508 demonstrates otherwise on current Windows. Code and tests must be defensive.
2. **AccessKit abstraction versus adapter coverage.** AccessKit enables one provider implementation, but adapters are best-effort and current platform-specific gaps remain, such as Windows heading levels.
3. **`abi3` wording versus reality.** “One wheel across Python versions” is true only within one OS/architecture/platform tag; it does not collapse macOS/Windows/Linux into one artifact.
4. **Wheel build versus public app trust.** A successful wheel build says nothing about Developer ID/notarization or Authenticode trust for a separately bundled desktop application.
5. **Living-document version skew.** The inspected PyO3 guide is v0.30.1, while the inspected maturin bindings page uses PyO3 0.29 examples. Pin and test a compatible pair; do not mix feature advice across versions.
6. **Historical Linux behavior.** AccessKit's January 2025 lazy-activation discussion is useful primary evidence but not proof of the pinned November 2026 adapter's behavior.

## Explicit unknowns and Round 2 triggers

| Unknown | Why it matters | Trigger / owner |
|---|---|---|
| Final OS/CPU/Python support floor | Changes wheel tags, CI and signing | Architect + User approval of REL-01 |
| Physical IME/AT test hardware and configured input methods | Blocks credible IME/a11y claims | User provides runners or manual certification evidence |
| Apple/Windows credential owner and release channel | Blocks signing/notarization/store operations | User names owner and channel |
| Accessibility conformance target | “Works with a screen reader” is not a complete production definition | Architect/User define WCAG version and supported ATs |
| AccessKit cost on 10,000-row content | Could break frame/idle targets or AT usability | Benchmark full vs visible-range tree updates |
| Current AccessKit Unix activation behavior | Inspector results may be false negatives | Reproduce on pinned 0.24.1 with Orca and Accerciser |
| Standalone application bundler | Determines final signing, update and Linux packaging responsibilities | Only needed if the first user-facing deliverable is an app rather than a Python library |
| wgpu/backend and HiDPI choices | Owned by RQ-04A; affects surface and input test stack | Reconcile with P0-R04A before ADR |

## Sources

### Local evidence

- **L01** — `.harness/STATE.md`, updated 2026-11-24.
- **L02** — `.harness/HANDOFFS/orchestrator-to-platform-P0-R04B-1.md`, attempt 1.
- **L03** — `.harness/RESEARCH/RQ-04-platform-input-accessibility-distribution.md`.
- **L04** — `.harness/PROCESS.md`.

### Primary external evidence

- **S01** — winit 0.30.13, [`Ime`](https://docs.rs/winit/0.30.13/winit/event/enum.Ime.html), published 2026-11-16.
- **S02** — winit 0.30.13, [`Window::set_ime_allowed`](https://docs.rs/winit/0.30.13/winit/window/struct.Window.html#method.set_ime_allowed), [`set_ime_cursor_area`](https://docs.rs/winit/0.30.13/winit/window/struct.Window.html#method.set_ime_cursor_area), [`focus_window`](https://docs.rs/winit/0.30.13/winit/window/struct.Window.html#method.focus_window), [`has_focus`](https://docs.rs/winit/0.30.13/winit/window/struct.Window.html#method.has_focus), published 2026-11-16.
- **S03** — winit 0.30.13, [`WindowEvent`](https://docs.rs/winit/0.30.13/winit/event/enum.WindowEvent.html) and [`KeyEvent`](https://docs.rs/winit/0.30.13/winit/event/struct.KeyEvent.html), published 2026-11-16.
- **S04** — winit 0.30.13, [changelog](https://docs.rs/winit/0.30.13/winit/changelog/), published 2026-11-16.
- **S05** — rust-windowing/winit, [issue #4508: Windows `KeyboardInput` during IME](https://github.com/rust-windowing/winit/issues/4508), opened 2026-03-11, open on access date.
- **S06** — rust-windowing/winit, [issue #4807: Kotoeri conversion commit loss](https://github.com/rust-windowing/winit/issues/4807), opened 2026-10-29, open on access date.
- **S07** — rust-windowing/winit, [issue #4626: IME teardown abort](https://github.com/rust-windowing/winit/issues/4626), opened 2026-07-13, open on access date.
- **S08** — rust-windowing/winit, [issue #4220: IME reset on input-focus change](https://github.com/rust-windowing/winit/issues/4220), opened 2025-05-10, closed 2025-11-25.
- **S09** — AccessKit, [repository README: provider/adapter model](https://github.com/AccessKit/accesskit), living document, accessed 2026-11-24.
- **S10** — AccessKit, [ARCHITECTURE.md](https://github.com/AccessKit/accesskit/blob/main/ARCHITECTURE.md), living document, accessed 2026-11-24.
- **S11** — AccessKit 0.25.2, [`ActivationHandler`](https://docs.rs/accesskit/0.25.2/accesskit/trait.ActivationHandler.html), published 2026-10-25.
- **S12** — AccessKit 0.25.2, [`TreeUpdate`](https://docs.rs/accesskit/0.25.2/accesskit/struct.TreeUpdate.html), published 2026-10-25.
- **S13** — AccessKit 0.25.2, [`NodeId`](https://docs.rs/accesskit/0.25.2/accesskit/struct.NodeId.html) and [`Node`](https://docs.rs/accesskit/0.25.2/accesskit/struct.Node.html), published 2026-10-25.
- **S14** — accesskit_winit 0.34.2, [`Adapter`](https://docs.rs/accesskit_winit/0.34.2/accesskit_winit/struct.Adapter.html), published 2026-10-25.
- **S15** — AccessKit 0.25.2, [`ActionHandler`](https://docs.rs/accesskit/0.25.2/accesskit/trait.ActionHandler.html) and [`DeactivationHandler`](https://docs.rs/accesskit/0.25.2/accesskit/trait.DeactivationHandler.html), published 2026-10-25.
- **S16** — AccessKit, [issue #840: Windows UIA heading level](https://github.com/AccessKit/accesskit/issues/840), opened 2026-10-25, open on access date.
- **S17** — AccessKit, [discussion #502: Unix lazy activation and Accerciser](https://github.com/AccessKit/accesskit/discussions/502), 2025-01-13/14.
- **S18** — accesskit_unix 0.24.1, [crate documentation](https://docs.rs/accesskit_unix/0.24.1/accesskit_unix/), published 2026-10-25.
- **S19** — PyO3 v0.30.1, [Building and distribution](https://pyo3.rs/v0.30.1/building-and-distribution), versioned guide accessed 2026-11-24.
- **S20** — Maturin, [Bindings](https://www.maturin.rs/bindings.html), [Distribution](https://www.maturin.rs/distribution.html), and [Configuration](https://www.maturin.rs/config.html), living documentation accessed 2026-11-24.
- **S21** — PyPA, [Platform compatibility tags](https://packaging.python.org/en/latest/specifications/platform-compatibility-tags/), living specification accessed 2026-11-24.
- **S22** — PyPA, [Package formats](https://packaging.python.org/en/latest/discussions/package-formats) and [wheel specification](https://packaging.python.org/en/latest/specifications/binary-distribution-format/), accessed 2026-11-24.
- **S23** — cibuildwheel, [Options](https://cibuildwheel.pypa.io/en/stable/options/), [Getting started](https://cibuildwheel.pypa.io/en/stable/setup/), and [Platforms](https://cibuildwheel.pypa.io/en/stable/platforms/), living documentation accessed 2026-11-24.
- **S24** — GitHub Docs, [GitHub-hosted runners reference](https://docs.github.com/en/actions/reference/runners/github-hosted-runners), living documentation accessed 2026-11-24.
- **S25** — Apple, [Notarizing macOS software before distribution](https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution), 2026 documentation JSON accessed 2026-11-24.
- **S26** — Apple, [Customizing the notarization workflow](https://developer.apple.com/documentation/security/customizing-the-notarization-workflow), 2026 documentation JSON accessed 2026-11-24.
- **S27** — Apple, [Packaging Mac software for distribution](https://developer.apple.com/documentation/xcode/packaging-mac-software-for-distribution), 2026 documentation JSON accessed 2026-11-24.
- **S28** — Apple, [macOS Big Sur 11.0.1 Universal Apps Release Notes — Code Signing](https://developer.apple.com/documentation/macos-release-notes/macos-big-sur-11_0_1-universal-apps-release-notes), 2020 release notes accessed 2026-11-24.
- **S29** — Microsoft Learn, [Use SignTool to sign a file](https://learn.microsoft.com/en-us/windows/win32/seccrypto/using-signtool-to-sign-a-file), updated 2026-11-20.
- **S30** — Microsoft Learn, [Code signing options for Windows app developers](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/code-signing-options), updated 2026-11-10.
- **S31** — Microsoft Learn, [Accessibility testing](https://learn.microsoft.com/en-us/windows/apps/design/accessibility/accessibility-testing), published 2026-07-22.
- **S32** — Apple, [Accessibility Inspector](https://developer.apple.com/documentation/accessibility/accessibility-inspector), 2026 documentation JSON accessed 2026-11-24.
- **S33** — GNOME Orca, [Test applications with Orca](https://orca.gnome.org/get-involved.html), living documentation accessed 2026-11-24; AccessKit, [application-developer testing notes](https://github.com/AccessKit/accesskit/blob/main/README-APPLICATION-DEVELOPERS.md), accessed 2026-11-24.
- **S34** — PyPI, [Trusted Publishing](https://docs.pypi.org/trusted-publishers/) and [adding a publisher](https://docs.pypi.org/trusted-publishers/adding-a-publisher/), living documentation accessed 2026-11-24.
- **S35** — PyPA, [Index-hosted attestations](https://packaging.python.org/en/latest/specifications/index-hosted-attestations/), updated 2026-10-12; PyPI, [Producing attestations](https://docs.pypi.org/attestations/producing-attestations), accessed 2026-11-24.
- **S36** — PEP 600, [Future manylinux platform tags](https://peps.python.org/pep-0600/), created 2019-05-03, Final, page last modified 2025-02-01.
- **S37** — Microsoft Learn, [Windows 11 release information](https://learn.microsoft.com/en-us/windows/release-health/windows11-release-information) and [Windows 10 release information](https://learn.microsoft.com/en-us/windows/release-health/release-information), current November 2026 lifecycle pages.
- **S38** — Apple Support, [Apple security releases](https://support.apple.com/en-us/100100), published 2026-10-30; [macOS Sonoma 14 updates](https://support.apple.com/en-us/109035), published 2026-08-06.
- **S39** — Freedesktop, [Desktop Entry Specification 1.5](https://specifications.freedesktop.org/desktop-entry/1.5), published 2020-04-27.

## Research completion

No feature code, task graph/state edits, commits, signing, notarization, store operations or publishing were performed. The only writes are the assigned research file, the required append-only `LOG.md` action lines, and the assigned Skeptic handoff.
