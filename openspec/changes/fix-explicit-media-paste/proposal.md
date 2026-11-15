# Recognize explicit media selections and sample local video

## Problem

An explicit paste such as `"clip.mp4""first.jpg""second.jpg"inspect these`
is treated as ordinary text. A video in a complete path list also rejects all
valid images. Consequently the provider receives paths without visual content.

## Capabilities

Recognize a leading sequence of explicitly quoted media paths with following
task text, and preserve both. Send actual validated image bytes through existing
model capability checks and session grants. Sample three timestamped frames from
an explicitly selected local video using Windows system decoders. Isolate media
decoding in a bounded child process. Keep UI feedback and draft on failure.

## Non-Goals and ownership

Do not scan arbitrary prose, code, imported history or model output for files.
Do not claim full video playback, audio transcription, or native video-provider
support. `sgmedia` in Sengoo owns generic OS decoding; the CLI owns selection,
sampling, temporary artifacts and model-facing metadata. Existing image grants,
digest validation, protocol encoders and user state ownership remain unchanged.
