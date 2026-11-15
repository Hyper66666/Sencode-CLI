# Implementation and verification

- [x] Reproduce the screenshot's adjacent quoted media paths with trailing task.
- [x] Preserve explicit image selections and task text, with visible failure and no arbitrary-prose scanning.
- [x] Implement and qualify bounded system video decoding and timestamped frames (sgmedia r4 gate, 21 checks).
- [x] Isolate decoder helpers with process deadlines; preserve originals and clean failed temporary artifacts (video attachment fixture, actual 30-second kill/reap).
- [x] Verify exact screenshot-shaped input, Unicode, malformed/missing files and limits (image/video-paste-qualified reports; ordinary Chinese/English single-word regression also passed).
- [x] Verify actual multimodal wire bytes and existing image grant/capability rejection (qualified native suite and fullscreen-accepted, 27 checks).
- [x] Verify frontend selection, preference fixes and same-candidate host regressions (33 scroll/target and 28 session/permission checks).
- [x] Run strict OpenSpec checks and record exact candidate/tool/source identities (41 items; build-result-qualified, unchanged inputs; installed hash a794de2c...).
