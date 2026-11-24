# RQ-01 — Prior-art architecture and clean-room boundaries

Status: Round 1 active
Decision unblocked: Runtime ownership model, entity/view lifecycle, retained vs immediate rendering boundary, and what may be clean-room reimplemented from GPUI.
Budget: Maximum 3 research rounds. Stop when further research would not change the decision.

## Required angles

1. GPUI/Zed primary design material and source architecture: entities, windows, elements, retained state, frame scheduling, actions/keymaps and rendering ownership.
2. Cross-framework comparison: Slint, Iced, Xilem, Masonry, Flutter/Skia, Dear ImGui and Qt as relevant; focus on concepts transferable without copying implementation.

## Decision-driving questions

- Which state lives in Python, which lives in Rust, and how are updates propagated without Python per frame?
- What is the smallest coherent hybrid immediate/retained model that supports reusable views and incremental rendering?
- Which GPUI concepts are safe to describe and reimplement clean-room, and which source-derived assets/code require Apache-2.0 provenance, headers and NOTICE treatment?
- What lifecycle and reentrancy rules prevent deadlocks, ref cycles and stale handles across the FFI boundary?

## Required output per researcher

Write only the assigned dated research file with: question, decision unblocked, dated primary sources, findings, claim-level confidence (`verified` / `plausible` / `unverified`), contradictions, recommendation, and exact evidence gaps. Distinguish source facts from inference. Do not copy source code into the repository.
