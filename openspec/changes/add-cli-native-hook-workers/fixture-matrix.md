# Executable fixture matrix

| Vector | Required observation |
| --- | --- |
| register/inspect/list | Disabled metadata only; child side-effect sentinel absent |
| trust change | Changed manifest or executable requires review; no spawn |
| hostile path/id/unknown tool | Traversal, reparse, shell string and shadowing rejected |
| UTF-8 | Chinese, emoji and escaped Unicode round-trip in fragmented JSONL |
| wire rejection | Wrong version/id/event, malformed/oversized/extra frames fail closed |
| host_call | Explicit unsupported response; no shell/MCP/model activity |
| fresh approval | Queued/stale approval cannot run a worker; current nonce can |
| Plan/child/no controller | Executable sentinel never created; parent is not silently run |
| policy | Worker continue cannot approve otherwise denied parent tool |
| before block/failure | Original tool sentinel absent; worker effects/outcome truthful |
| after unknown | No after worker when original result or cleanup is uncertain |
| FIFO | Alias cwd converges; two effectful workers and normal write never overlap |
| parent ordering | Before worker releases permit before parent tool acquires it |
| cancellation | Parent cancel interrupts worker and descendants; permit released |
| pipes | Simultaneous stdout/stderr pressure and partial stdin never deadlock |
| Drop | Abandoned worker handle terminates owned descendants |
| terminal result | Result then nonzero exit or live grandchild is not success |
| no replay | Crash after durable admission, duplicate call and reopen never rerun |
| fencing | Stale execution cannot admit/finish or publish terminal hook events |
| Goal | Failure pauses; request/token counters do not decrease or bypass budget |
| public surfaces | Real list/enable/slash capability, first Enter fill, second execute |
| source-free | Installed worker/CLI independently run without compiler/source paths |

Each executed row must cite its named test and actual candidate hashes in
`evidence.md`. An independent probe is not public-route evidence.
