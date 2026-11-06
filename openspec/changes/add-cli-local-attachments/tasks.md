# Tasks (foundations and encoders implemented; attachment UX pending)

- [ ] Review exact asset/public-history compatibility with the desktop integration owner.
- [x] Qualify generic bounded snapshot/header APIs from the sibling Sengoo change.
- [x] Add three-protocol ordered image golden fixtures and text/tool continuation regressions.
- [x] Add zero-outbound preflight refusal and exact transport-limit fixtures.
- [ ] Implement session-scoped capture, immutable references, retry/discard and restart verification.
- [x] Implement capability-aware Provider encoders without changing text-only behavior.
- [ ] Verify shared DB/assets, idle desktop handoff and stale execution fencing in isolation.
- [ ] Add responsive explicit TUI attachment controls and visible unsupported/missing states.
- [ ] Qualify a named PDF engine/submission path before claiming PDF acceptance.
- [ ] Verify copy budgets, cancellation, installed offline use and live endpoint compatibility where authorized.
- [ ] Reconcile the umbrella media gate only after all required implementation evidence exists.

Spec validation alone does not complete any item above. PNG/JPEG headers and PDF
capability detection are useful foundations, not full multimodal delivery.

Windows evidence: `sencode-cli/target/provider-media/{native2.log,protocol-native.log,transport-native2.log}`.
The loopback capture covers three ~1.5MiB actual PNG bodies and9 local refusals
with zero extra outbound requests. The explicit-capability encoder is internal;
no attachment picker, shared media schema or live endpoint was qualified.
