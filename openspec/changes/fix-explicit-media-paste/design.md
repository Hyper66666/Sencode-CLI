# Explicit media flow

A leading quoted media path is an explicit selection. Consecutive quotes and
spaces/newlines between selections are supported; following prose remains the
task. Existing complete unquoted path lists remain supported. Paths appearing
later in ordinary prose and unterminated quoted text remain ordinary text.

Selection validation is atomic. Missing, malformed, unreadable or oversized
selected files keep the original text and produce a local explanation rather
than silently dropping valid siblings or telling the provider it saw media.
The overall eight-image and 8 MiB image-byte budgets still apply.

The CLI samples a bounded set of three local-video frames using a separate copy
of its own executable, fixed helper operations and native process arguments.
The helper owns decoder state and can be terminated on a 30-second operation
deadline; decoding does not invoke a command shell or require FFmpeg. Local
Windows Media Foundation/WIC providers supply codec support. Unsupported media
is a visible local failure. Source video remains untouched. Generated PNGs live
under a unique system TEMP directory for subsequent hash/grant-based history
reads, never under the project. Failed selections clean only their own temporary
files and empty directories. A successful attachment includes actual timestamps
and states that it represents sparse frames without audio.

The frontend inserts image chips and task text together. This applies to explicit
clipboard file selection and terminal paste. Normal explicit image history is
hydrated only after vision capability and session grants pass.
