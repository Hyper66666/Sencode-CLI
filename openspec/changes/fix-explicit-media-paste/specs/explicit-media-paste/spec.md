## ADDED Requirements

### Requirement: Explicit leading media paths preserve the task
The CLI SHALL treat a leading sequence of quoted local image or video paths as
explicit attachments and SHALL preserve trailing task text.

#### Scenario: Adjacent quoted paths and Chinese task text
- **WHEN** a user pastes adjacent quoted video and image paths followed directly by Chinese task text
- **THEN** the valid selected files become actual visual attachments and the task text is retained.

#### Scenario: A path is merely mentioned in prose
- **WHEN** ordinary prose, code, imported history or model output mentions a local path
- **THEN** the CLI does not implicitly read or attach that file.

#### Scenario: Selected media cannot be read
- **WHEN** an explicitly selected media file is missing, unsupported, malformed or exceeds limits
- **THEN** the CLI retains the original draft and explains the local failure before provider submission.

### Requirement: Bounded local video frame analysis
The CLI SHALL sample local video into timestamped image frames using a bounded
decoder child process and SHALL identify the frames as a sparse visual sample.

#### Scenario: Analyze a supported local video
- **WHEN** a user explicitly selects a supported local video for a vision-capable model
- **THEN** selected frames are sent as real image content with timestamps and a statement that audio was not analyzed.

#### Scenario: Decoder deadline or failure
- **WHEN** decoding fails or exceeds its operation deadline
- **THEN** the child is stopped, selected originals remain unchanged, and the unsent draft remains available.
