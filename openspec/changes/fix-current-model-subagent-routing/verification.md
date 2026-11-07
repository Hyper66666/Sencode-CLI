# Verification — 2026-11-07

Host: `DESKTOP-FUAQMFB`, Windows x64. Existing unrelated working-tree changes
were retained; these are internal source-development candidates, not releases.

## Inputs and candidate

- CLI baseline: `b2b85ef2c8f369f2fd69ef8729ab420cc420959a`.
- Sengoo baseline: `86c6f87975646b91c9cf2d7d069ac06ee4243b9b`.
- Compiler SHA256: `cc280b3bf0ec0bf17650b0745500c72e205ee2d2073af8ea7ed552045570f1b0`.
- Final O2 executable SHA256: `05361fb9f77f263b13491665c09a72b60c24482a9a481057accb0e853c38cf85`.
- ZIP SHA256: `efeadcae585504b10c6fec15ee80bff6f24565c4d6d5ab1ab18d0ba3096fcb67`.

Build inputs, complete source hashes, logs and evidence are retained under
`target/model-routing-20261107/`; candidate-3 is the installed final candidate.
Agent logic, search, routing and identity are implemented in Sengoo. This repair
required no additional compiler/runtime API changes.

## Executed checks

`native-final-evidence.json`: eight gate cases passed: model_routing,
model_selection, core, engine, controller_recovery, controller_tool_batch,
children, consult. After refining the invalid-native-protocol diagnostic,
`routing-final-evidence.json` reran the focused gate against final source,
including the new diagnostic assertion. Other gate implementations are unchanged.

`production-final-evidence.json`: all eight production cases passed on the
final executable: model_routing_host, engine_host, workbench_controls,
session_policy_wait, agent_recall_selection, responses_tools,
request_recovery_host, managed_host. This includes actual hidden Windows console
interaction, SQLite admission, process cancellation and synthetic loopback
services; it is not live-provider qualification.

The routing fixture made 42 requests across Chat Completions, Responses and
Messages. It verified default/current divergence, configuration changes during a
parent request, cross-provider IDs/labels/fragments, ambiguity, discovered-only
exclusion, unsupported accounts, invalid configuration, missing credentials,
automatic protocol detection, Plan-safe discovery, switch/resume identity and
the absence of host identity metadata in durable public history.

## Installation

`candidate-3/install-smoke.json` passed isolated installation with system-only
PATH, Unicode paths, bare-command forwarders, resume, running-image updates,
checksum rejection and rollback. `candidate-3/local-install-evidence.json`
verified all 15 installed payloads and six direct/bare/forwarder entrypoints.
The local prefix is `D:/SencodeCLI`; PATH was unchanged. The prior executable
`498085a677f7d8c66d3afcccf233b23f4e73125d0e3d0b1245afd7ceee75363d`
has a checksum-verified rollback package.

No paid/live model calls, fresh-VM qualification or public release was performed.
Native subagents still cannot invoke managed account runtimes; the public model
directory reports that limitation. Private clipboard integration remains outside
this repair's scope; console selection was tested without touching user clipboard.
