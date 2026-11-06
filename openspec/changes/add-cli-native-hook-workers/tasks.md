# Native hook worker gates

- [x] Validate manifest/wire contracts and deterministic fixture vectors.
- [x] Implement isolated schema-1 registry, fingerprint trust and durable invocation admission.
- [x] Implement bounded owned-worker client and minimal Sengoo worker helper/example.
- [x] Verify fresh approval, Plan/read-only refusal, no-controller denial and fingerprint changes before spawn.
- [ ] Verify one canonical cwd FIFO permit, cancellation, no replay, Drop and real owned process-tree cleanup.
- [x] Integrate before/after controller boundary without nested permits or after-hook unknown outcomes.
- [ ] Connect root-owned public/slash handlers and reconcile command capability gates.
- [ ] Record full source/compiler/binary identities, named Windows fixtures and installed source-free acceptance.

No entire P4/SDK completion is implied by this slice. Unrun platform, fixture,
live provider and installed gates stay open.

Named isolated Windows checks and exact identities: [evidence.md](evidence.md).
The remaining process verification task includes fault injection of abandoned
Drop/uncertified native cleanup and concurrent multi-worker overlap stress;
existing explicit timeout/tree, controller cancellation and canonical FIFO
checks do not substitute for those remaining vectors.
