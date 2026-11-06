-- Generated from desktop baseline a468086401a0d19077b5cf0b6aea3ecff0f04c9a.

CREATE TABLE projects (
    id TEXT PRIMARY KEY,
    directory TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    archived INTEGER NOT NULL DEFAULT 0 CHECK (archived IN (0, 1)),
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    last_sent_at INTEGER,
    run_state TEXT NOT NULL DEFAULT 'idle',
    unread INTEGER NOT NULL DEFAULT 0 CHECK (unread IN (0, 1))
);
CREATE INDEX sessions_project_activity ON sessions(project_id, archived, last_sent_at DESC, created_at DESC);

CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    text TEXT NOT NULL DEFAULT '',
    reasoning TEXT NOT NULL DEFAULT '',
    created_at INTEGER NOT NULL,
    completed_at INTEGER,
    cancelled INTEGER NOT NULL DEFAULT 0 CHECK (cancelled IN (0, 1)),
    connection_id TEXT,
    model_id TEXT,
    revision INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX messages_session_revision ON messages(session_id, revision, created_at, id);

CREATE TABLE tool_calls (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    message_id TEXT NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    kind TEXT NOT NULL,
    status TEXT NOT NULL,
    safe_payload_json TEXT NOT NULL,
    started_at INTEGER NOT NULL,
    completed_at INTEGER
);
CREATE INDEX tool_calls_message ON tool_calls(message_id, started_at, id);

CREATE TABLE runtime_bindings (
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    connection_id TEXT NOT NULL,
    generation INTEGER NOT NULL,
    native_session_id TEXT NOT NULL,
    synced_revision INTEGER NOT NULL DEFAULT 0,
    updated_at INTEGER NOT NULL,
    PRIMARY KEY(session_id, connection_id)
);

CREATE TABLE connection_configs (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    profile_scope TEXT NOT NULL,
    display_name TEXT NOT NULL,
    config_json TEXT NOT NULL,
    selected_model_id TEXT,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

CREATE TABLE imports (
    source_kind TEXT NOT NULL,
    source_id TEXT NOT NULL,
    local_session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    imported_revision INTEGER NOT NULL DEFAULT 0,
    imported_at INTEGER NOT NULL,
    PRIMARY KEY(source_kind, source_id)
);

CREATE TABLE schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at INTEGER NOT NULL
);


CREATE TABLE runtime_events (
    runtime_generation INTEGER NOT NULL,
    provider_event_id TEXT NOT NULL,
    applied_at INTEGER NOT NULL,
    PRIMARY KEY(runtime_generation, provider_event_id)
);


CREATE TABLE session_usage (
    session_id TEXT PRIMARY KEY REFERENCES sessions(id) ON DELETE CASCADE,
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    terminal_events INTEGER NOT NULL DEFAULT 0
);


CREATE TABLE session_review_counts (
    session_id TEXT PRIMARY KEY REFERENCES sessions(id) ON DELETE CASCADE,
    turn_count INTEGER NOT NULL DEFAULT 0,
    file_count INTEGER NOT NULL DEFAULT 0,
    updated_at INTEGER NOT NULL
);


-- Concurrent accept paths must not share a revision within a session.
-- Deduplicate any pre-existing (session_id, revision) collisions by keeping the
-- lowest rowid and reassigning later rows to fresh revisions before the unique index.
UPDATE messages
SET revision = (
    SELECT COALESCE(MAX(m2.revision), 0)
    FROM messages m2
    WHERE m2.session_id = messages.session_id
) + (
    SELECT COUNT(*)
    FROM messages m3
    WHERE m3.session_id = messages.session_id
      AND m3.rowid <= messages.rowid
      AND EXISTS (
          SELECT 1 FROM messages d
          WHERE d.session_id = m3.session_id
            AND d.revision = m3.revision
            AND d.rowid < m3.rowid
      )
)
WHERE EXISTS (
    SELECT 1 FROM messages d
    WHERE d.session_id = messages.session_id
      AND d.revision = messages.revision
      AND d.rowid < messages.rowid
);

CREATE UNIQUE INDEX IF NOT EXISTS messages_session_revision_unique
    ON messages(session_id, revision);


CREATE TABLE app_preferences (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at INTEGER NOT NULL
);

-- Existing installs had no explicit preference. Seed it from the most recent
-- accepted turn so the first upgraded launch keeps the channel the user was using.
INSERT INTO app_preferences(key, value, updated_at)
SELECT 'preferred_connection_id', connection_id, created_at
FROM messages
WHERE connection_id IS NOT NULL AND trim(connection_id) <> ''
ORDER BY created_at DESC, revision DESC
LIMIT 1;


CREATE TABLE queued_prompts (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    connection_id TEXT NOT NULL,
    text TEXT NOT NULL,
    position INTEGER NOT NULL,
    state TEXT NOT NULL DEFAULT 'queued' CHECK (state IN ('queued', 'dispatching')),
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);
CREATE UNIQUE INDEX queued_prompts_session_position
    ON queued_prompts(session_id, position);
CREATE INDEX queued_prompts_session_state_position
    ON queued_prompts(session_id, state, position);


CREATE TABLE meeting_runs (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    topic TEXT NOT NULL,
    moderator_connection_id TEXT NOT NULL,
    moderator_model_id TEXT NOT NULL,
    source_history_revision INTEGER NOT NULL CHECK (source_history_revision >= 0),
    max_cycles INTEGER NOT NULL CHECK (max_cycles BETWEEN 1 AND 5),
    current_cycle INTEGER NOT NULL DEFAULT 0
        CHECK (current_cycle BETWEEN 0 AND 5 AND current_cycle <= max_cycles),
    state TEXT NOT NULL CHECK (state IN (
        'draft', 'compressing', 'opening', 'running', 'awaiting-advance',
        'moderating', 'paused', 'closing', 'completed', 'cancelled'
    )),
    pause_reason TEXT CHECK (pause_reason IS NULL OR pause_reason IN (
        'compression-failed', 'moderator-unavailable', 'participant-decision',
        'recovery-required', 'context-limit', 'user-hold'
    )),
    sequence_watermark INTEGER NOT NULL DEFAULT 0 CHECK (sequence_watermark >= 0),
    topic_message_id TEXT REFERENCES messages(id) ON DELETE SET NULL,
    conclusion_message_id TEXT REFERENCES messages(id) ON DELETE SET NULL,
    error_json TEXT,
    advance_deadline_at INTEGER,
    hold_reason TEXT,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    completed_at INTEGER
);
CREATE INDEX meeting_runs_session_created
    ON meeting_runs(session_id, created_at DESC, id);
CREATE INDEX meeting_runs_state_updated
    ON meeting_runs(state, updated_at, id);
CREATE UNIQUE INDEX meeting_runs_one_active_per_session
    ON meeting_runs(session_id)
    WHERE state NOT IN ('completed', 'cancelled');

CREATE TABLE meeting_contexts (
    meeting_id TEXT PRIMARY KEY REFERENCES meeting_runs(id) ON DELETE CASCADE,
    state TEXT NOT NULL CHECK (state IN ('capturing', 'compressing', 'ready', 'failed')),
    source_revision INTEGER NOT NULL CHECK (source_revision >= 0),
    source_message_count INTEGER NOT NULL DEFAULT 0 CHECK (source_message_count >= 0),
    source_message_ids_json TEXT NOT NULL DEFAULT '[]',
    estimated_tokens INTEGER NOT NULL DEFAULT 0 CHECK (estimated_tokens >= 0),
    compressed INTEGER NOT NULL DEFAULT 0 CHECK (compressed IN (0, 1)),
    target_tokens INTEGER CHECK (target_tokens IS NULL OR target_tokens >= 0),
    recent_raw_tokens INTEGER NOT NULL DEFAULT 0 CHECK (recent_raw_tokens >= 0),
    normalized_context_json TEXT NOT NULL DEFAULT '{}',
    error_json TEXT,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

CREATE TABLE meeting_seats (
    id TEXT PRIMARY KEY,
    meeting_id TEXT NOT NULL REFERENCES meeting_runs(id) ON DELETE CASCADE,
    seat_kind TEXT NOT NULL CHECK (seat_kind IN ('moderator', 'participant')),
    position INTEGER NOT NULL CHECK (position BETWEEN 0 AND 4),
    display_name TEXT NOT NULL,
    connection_id TEXT NOT NULL,
    model_id TEXT NOT NULL,
    role TEXT,
    state TEXT NOT NULL CHECK (state IN (
        'ready', 'queued', 'thinking', 'speaking', 'passed', 'waiting-next-cycle',
        'waiting-reconnect', 'removed', 'failed'
    )),
    error_json TEXT,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    UNIQUE(meeting_id, position),
    UNIQUE(meeting_id, id)
);
CREATE UNIQUE INDEX meeting_seats_one_moderator
    ON meeting_seats(meeting_id)
    WHERE seat_kind = 'moderator';
CREATE INDEX meeting_seats_meeting_state
    ON meeting_seats(meeting_id, state, position);

CREATE TABLE meeting_cycles (
    meeting_id TEXT NOT NULL REFERENCES meeting_runs(id) ON DELETE CASCADE,
    number INTEGER NOT NULL CHECK (number BETWEEN 1 AND 5),
    snapshot_sequence INTEGER NOT NULL CHECK (snapshot_sequence >= 0),
    state TEXT NOT NULL CHECK (state IN (
        'planned', 'running', 'awaiting-advance', 'moderating', 'completed', 'cancelled'
    )),
    public_snapshot_json TEXT NOT NULL,
    spoken_count INTEGER NOT NULL DEFAULT 0 CHECK (spoken_count >= 0),
    passed_count INTEGER NOT NULL DEFAULT 0 CHECK (passed_count >= 0),
    absent_count INTEGER NOT NULL DEFAULT 0 CHECK (absent_count >= 0),
    advance_deadline_at INTEGER,
    advance_held INTEGER NOT NULL DEFAULT 0 CHECK (advance_held IN (0, 1)),
    hold_reason TEXT,
    started_at INTEGER,
    completed_at INTEGER,
    PRIMARY KEY(meeting_id, number)
);
CREATE INDEX meeting_cycles_meeting_state
    ON meeting_cycles(meeting_id, state, number);

CREATE TABLE meeting_turns (
    id TEXT PRIMARY KEY,
    meeting_id TEXT NOT NULL REFERENCES meeting_runs(id) ON DELETE CASCADE,
    seat_id TEXT,
    cycle_number INTEGER,
    kind TEXT NOT NULL CHECK (kind IN (
        'compression', 'moderator-opening', 'participant',
        'moderator-checkpoint', 'moderator-conclusion'
    )),
    attempt INTEGER NOT NULL DEFAULT 1 CHECK (attempt >= 1),
    snapshot_sequence INTEGER NOT NULL CHECK (snapshot_sequence >= 0),
    idempotency_key TEXT NOT NULL UNIQUE,
    send_state TEXT NOT NULL DEFAULT 'planned' CHECK (send_state IN (
        'planned', 'sending', 'sent', 'terminal', 'interrupted'
    )),
    result TEXT NOT NULL DEFAULT 'pending' CHECK (result IN (
        'pending', 'spoken', 'passed', 'absent', 'failed', 'skipped', 'interrupted'
    )),
    text TEXT NOT NULL DEFAULT '',
    reasoning TEXT NOT NULL DEFAULT '',
    provider_event_ids_json TEXT NOT NULL DEFAULT '[]',
    safe_usage_json TEXT,
    error_json TEXT,
    created_at INTEGER NOT NULL,
    sent_at INTEGER,
    started_at INTEGER,
    completed_at INTEGER,
    FOREIGN KEY(meeting_id, seat_id)
        REFERENCES meeting_seats(meeting_id, id) ON DELETE CASCADE,
    FOREIGN KEY(meeting_id, cycle_number)
        REFERENCES meeting_cycles(meeting_id, number) ON DELETE CASCADE
);
CREATE INDEX meeting_turns_meeting_cycle_result
    ON meeting_turns(meeting_id, cycle_number, result, completed_at, id);
CREATE INDEX meeting_turns_pending
    ON meeting_turns(meeting_id, send_state, created_at, id)
    WHERE result = 'pending';

CREATE TABLE meeting_interventions (
    id TEXT PRIMARY KEY,
    meeting_id TEXT NOT NULL REFERENCES meeting_runs(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    position INTEGER NOT NULL CHECK (position >= 0),
    state TEXT NOT NULL CHECK (state IN ('queued', 'consumed', 'withdrawn', 'summary-only')),
    target_cycle INTEGER CHECK (target_cycle IS NULL OR target_cycle BETWEEN 1 AND 5),
    consumed_cycle INTEGER CHECK (consumed_cycle IS NULL OR consumed_cycle BETWEEN 1 AND 5),
    consumed_snapshot_sequence INTEGER
        CHECK (consumed_snapshot_sequence IS NULL OR consumed_snapshot_sequence >= 0),
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    consumed_at INTEGER,
    UNIQUE(meeting_id, position)
);
CREATE INDEX meeting_interventions_meeting_state_position
    ON meeting_interventions(meeting_id, state, position);

CREATE TABLE meeting_runtime_bindings (
    meeting_id TEXT NOT NULL REFERENCES meeting_runs(id) ON DELETE CASCADE,
    seat_id TEXT NOT NULL,
    connection_id TEXT NOT NULL,
    runtime_generation INTEGER NOT NULL CHECK (runtime_generation >= 0),
    local_session_id TEXT NOT NULL,
    native_session_id TEXT,
    access_policy TEXT NOT NULL CHECK (access_policy IN ('read-only', 'no-tools')),
    state TEXT NOT NULL CHECK (state IN (
        'creating', 'ready', 'disconnected', 'interrupted', 'closed'
    )),
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    PRIMARY KEY(meeting_id, seat_id),
    UNIQUE(meeting_id, local_session_id),
    FOREIGN KEY(meeting_id, seat_id)
        REFERENCES meeting_seats(meeting_id, id) ON DELETE CASCADE
);
CREATE INDEX meeting_runtime_bindings_connection_state
    ON meeting_runtime_bindings(connection_id, state, updated_at, meeting_id);


ALTER TABLE meeting_turns
    ADD COLUMN updated_at INTEGER NOT NULL DEFAULT 0;
UPDATE meeting_turns SET updated_at = created_at WHERE updated_at = 0;


ALTER TABLE meeting_cycles
    ADD COLUMN completion_order_json TEXT NOT NULL DEFAULT '[]';


CREATE TABLE fusion_runs (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    objective TEXT NOT NULL,
    baseline_oid TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN (
        'idle', 'primaryRunning', 'verifying', 'repairing', 'upgrading',
        'altRunning', 'adjudicating', 'decided', 'partial', 'interrupted',
        'cancelled'
    )),
    plan_json TEXT NOT NULL,
    plan_sufficiency TEXT NOT NULL CHECK (plan_sufficiency IN ('ok', 'insufficient')),
    decision_kind TEXT CHECK (decision_kind IS NULL OR decision_kind IN (
        'winner', 'partial', 'humanChoice'
    )),
    winner_candidate_id TEXT,
    reason_code TEXT,
    decision_json TEXT,
    verified_outcome TEXT CHECK (verified_outcome IS NULL OR verified_outcome IN (
        'verifiedSuccess', 'partial', 'failed'
    )),
    spent_wall_ms INTEGER NOT NULL DEFAULT 0 CHECK (spent_wall_ms >= 0),
    spent_cost_micros INTEGER,
    sequence_watermark INTEGER NOT NULL DEFAULT 0 CHECK (sequence_watermark >= 0),
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    completed_at INTEGER
);
CREATE INDEX fusion_runs_session_created
    ON fusion_runs(session_id, created_at DESC, id);
CREATE INDEX fusion_runs_state_updated
    ON fusion_runs(state, updated_at, id);
CREATE UNIQUE INDEX fusion_runs_one_active_per_session
    ON fusion_runs(session_id)
    WHERE state NOT IN ('decided', 'partial', 'interrupted', 'cancelled');

CREATE TABLE fusion_grants (
    run_id TEXT PRIMARY KEY REFERENCES fusion_runs(id) ON DELETE CASCADE,
    max_candidate_slots INTEGER NOT NULL CHECK (max_candidate_slots BETWEEN 1 AND 2),
    max_wall_ms INTEGER NOT NULL CHECK (max_wall_ms >= 0),
    verify_reserve_ms INTEGER NOT NULL CHECK (verify_reserve_ms >= 0),
    spent_wall_ms INTEGER NOT NULL DEFAULT 0 CHECK (spent_wall_ms >= 0),
    used_slots INTEGER NOT NULL DEFAULT 0 CHECK (used_slots >= 0),
    spend_quality TEXT NOT NULL CHECK (spend_quality IN (
        'exact', 'estimated', 'unavailable'
    )),
    tool_call_ceiling INTEGER CHECK (tool_call_ceiling IS NULL OR tool_call_ceiling >= 0),
    spent_tool_calls INTEGER CHECK (spent_tool_calls IS NULL OR spent_tool_calls >= 0),
    cost_ceiling_micros INTEGER,
    spent_cost_micros INTEGER,
    updated_at INTEGER NOT NULL
);

CREATE TABLE fusion_candidates (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES fusion_runs(id) ON DELETE CASCADE,
    slot INTEGER NOT NULL CHECK (slot BETWEEN 0 AND 1),
    kind TEXT NOT NULL CHECK (kind IN ('primary', 'alternative')),
    model_id TEXT NOT NULL,
    baseline_oid TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN (
        'pending', 'running', 'verifying', 'repairing', 'passed', 'failed',
        'interrupted', 'cancelled', 'cleanupFailed'
    )),
    worktree_path TEXT,
    head_oid TEXT,
    diff_line_count INTEGER CHECK (diff_line_count IS NULL OR diff_line_count >= 0),
    risk_labels_json TEXT NOT NULL DEFAULT '[]',
    task_pack_json TEXT,
    idempotency_key TEXT NOT NULL UNIQUE,
    send_state TEXT NOT NULL DEFAULT 'notSent' CHECK (send_state IN (
        'notSent', 'sent', 'terminal', 'interrupted'
    )),
    spent_wall_ms INTEGER NOT NULL DEFAULT 0 CHECK (spent_wall_ms >= 0),
    spent_cost_micros INTEGER,
    cleanup_failed INTEGER NOT NULL DEFAULT 0 CHECK (cleanup_failed IN (0, 1)),
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    completed_at INTEGER,
    UNIQUE(run_id, slot)
);
CREATE INDEX fusion_candidates_run_slot
    ON fusion_candidates(run_id, slot);
CREATE INDEX fusion_candidates_pending_sends
    ON fusion_candidates(run_id, send_state, created_at, id)
    WHERE send_state IN ('notSent', 'sent');

CREATE TABLE fusion_checks (
    candidate_id TEXT NOT NULL REFERENCES fusion_candidates(id) ON DELETE CASCADE,
    check_id TEXT NOT NULL,
    attempt INTEGER NOT NULL DEFAULT 1 CHECK (attempt >= 1),
    required INTEGER NOT NULL CHECK (required IN (0, 1)),
    result TEXT NOT NULL CHECK (result IN (
        'passed', 'failed', 'timedOut', 'cancelled', 'notRun', 'infraError'
    )),
    duration_ms INTEGER CHECK (duration_ms IS NULL OR duration_ms >= 0),
    exit_code INTEGER,
    output_digest TEXT,
    created_at INTEGER NOT NULL,
    PRIMARY KEY(candidate_id, check_id, attempt)
);
CREATE INDEX fusion_checks_candidate_required
    ON fusion_checks(candidate_id, required, result);


ALTER TABLE fusion_runs ADD COLUMN plan_digest TEXT;
ALTER TABLE fusion_runs ADD COLUMN preview_patch TEXT;


PRAGMA defer_foreign_keys = ON;

-- Fixed connection definitions: canonical wins. Rename the legacy row only when the
-- canonical row is absent; otherwise drop the legacy duplicate after references move.
UPDATE OR IGNORE connection_configs SET id = 'sencode-shared', kind = 'sencode' WHERE id = 'grok-shared';
UPDATE OR IGNORE connection_configs SET id = 'sencode-managed', kind = 'sencode' WHERE id = 'grok-managed';
DELETE FROM connection_configs WHERE id IN ('grok-shared', 'grok-managed');
UPDATE connection_configs SET kind = 'sencode' WHERE kind = 'grok';

-- Runtime bindings share a (session_id, connection_id) primary key. Keep the newest
-- complete binding per session (higher generation, then updated_at) before renaming so
-- a partially upgraded session does not lose or duplicate its accepted-turn capture.
DELETE FROM runtime_bindings
 WHERE connection_id = 'grok-shared'
   AND EXISTS (
     SELECT 1 FROM runtime_bindings canon
     WHERE canon.session_id = runtime_bindings.session_id
       AND canon.connection_id = 'sencode-shared'
       AND (canon.generation, canon.updated_at) >= (runtime_bindings.generation, runtime_bindings.updated_at)
   );
DELETE FROM runtime_bindings
 WHERE connection_id = 'sencode-shared'
   AND EXISTS (
     SELECT 1 FROM runtime_bindings legacy
     WHERE legacy.session_id = runtime_bindings.session_id
       AND legacy.connection_id = 'grok-shared'
       AND (legacy.generation, legacy.updated_at) > (runtime_bindings.generation, runtime_bindings.updated_at)
   );
UPDATE runtime_bindings SET connection_id = 'sencode-shared' WHERE connection_id = 'grok-shared';
DELETE FROM runtime_bindings
 WHERE connection_id = 'grok-managed'
   AND EXISTS (
     SELECT 1 FROM runtime_bindings canon
     WHERE canon.session_id = runtime_bindings.session_id
       AND canon.connection_id = 'sencode-managed'
       AND (canon.generation, canon.updated_at) >= (runtime_bindings.generation, runtime_bindings.updated_at)
   );
DELETE FROM runtime_bindings
 WHERE connection_id = 'sencode-managed'
   AND EXISTS (
     SELECT 1 FROM runtime_bindings legacy
     WHERE legacy.session_id = runtime_bindings.session_id
       AND legacy.connection_id = 'grok-managed'
       AND (legacy.generation, legacy.updated_at) > (runtime_bindings.generation, runtime_bindings.updated_at)
   );
UPDATE runtime_bindings SET connection_id = 'sencode-managed' WHERE connection_id = 'grok-managed';

-- Plain connection references (no identity is part of a primary key here): rewrite in place
-- so ordering, intervention state, and recovery semantics are untouched.
UPDATE messages SET connection_id = 'sencode-shared' WHERE connection_id = 'grok-shared';
UPDATE messages SET connection_id = 'sencode-managed' WHERE connection_id = 'grok-managed';
UPDATE queued_prompts SET connection_id = 'sencode-shared' WHERE connection_id = 'grok-shared';
UPDATE queued_prompts SET connection_id = 'sencode-managed' WHERE connection_id = 'grok-managed';
UPDATE app_preferences SET value = 'sencode-shared' WHERE key = 'preferred_connection_id' AND value = 'grok-shared';
UPDATE app_preferences SET value = 'sencode-managed' WHERE key = 'preferred_connection_id' AND value = 'grok-managed';
UPDATE meeting_runs SET moderator_connection_id = 'sencode-shared' WHERE moderator_connection_id = 'grok-shared';
UPDATE meeting_runs SET moderator_connection_id = 'sencode-managed' WHERE moderator_connection_id = 'grok-managed';
UPDATE meeting_seats SET connection_id = 'sencode-shared' WHERE connection_id = 'grok-shared';
UPDATE meeting_seats SET connection_id = 'sencode-managed' WHERE connection_id = 'grok-managed';
UPDATE meeting_runtime_bindings SET connection_id = 'sencode-shared' WHERE connection_id = 'grok-shared';
UPDATE meeting_runtime_bindings SET connection_id = 'sencode-managed' WHERE connection_id = 'grok-managed';

-- History graph: canonicalize the source kind and the deterministic project/message/tool
-- ID prefixes. Deterministic IDs keep the same content hash suffix, so a colliding
-- canonical row is provably the same upstream source and the legacy duplicate is dropped
-- after its children are re-pointed. Native session IDs are upstream identifiers and are
-- never rewritten, keeping the import marker bound to the same session.
UPDATE imports SET source_kind = 'sencode_cli' WHERE source_kind = 'grok_cli'
  AND source_id NOT IN (SELECT source_id FROM imports WHERE source_kind = 'sencode_cli');
DELETE FROM imports WHERE source_kind = 'grok_cli';

UPDATE sessions
  SET project_id = 'sencode-project' || substr(project_id, length('grok-project') + 1)
  WHERE project_id LIKE 'grok-project-%';
UPDATE OR IGNORE projects
  SET id = 'sencode-project' || substr(id, length('grok-project') + 1)
  WHERE id LIKE 'grok-project-%';
DELETE FROM projects WHERE id LIKE 'grok-project-%';

UPDATE tool_calls
  SET message_id = 'sencode-message' || substr(message_id, length('grok-message') + 1)
  WHERE message_id LIKE 'grok-message-%';
UPDATE OR IGNORE messages
  SET id = 'sencode-message' || substr(id, length('grok-message') + 1)
  WHERE id LIKE 'grok-message-%';
DELETE FROM messages WHERE id LIKE 'grok-message-%';

UPDATE OR IGNORE tool_calls
  SET id = 'sencode-tool' || substr(id, length('grok-tool') + 1)
  WHERE id LIKE 'grok-tool-%';
DELETE FROM tool_calls WHERE id LIKE 'grok-tool-%';


-- NULL identifies messages created before ordered content blocks existed.
-- New assistant turns store JSON here so restart preserves text/tool/reasoning
-- interleaving; legacy NULL rows intentionally keep the tools-first layout.
ALTER TABLE messages ADD COLUMN content_blocks_json TEXT;


ALTER TABLE sessions ADD COLUMN title_source TEXT NOT NULL DEFAULT 'placeholder'
    CHECK(title_source IN ('placeholder', 'first_message', 'user', 'existing'));

UPDATE sessions
SET title_source = CASE
    WHEN trim(title) = '' OR lower(replace(trim(title), ' ', '')) = 'newchat'
        THEN 'placeholder'
    ELSE 'existing'
END;


ALTER TABLE meeting_runs
ADD COLUMN participant_concurrency INTEGER NOT NULL DEFAULT 1
    CHECK (participant_concurrency BETWEEN 1 AND 4);


ALTER TABLE sessions ADD COLUMN selected_connection_id TEXT;
ALTER TABLE sessions ADD COLUMN selected_model_id TEXT;
ALTER TABLE sessions ADD COLUMN attention_kind TEXT NOT NULL DEFAULT 'none'
    CHECK(attention_kind IN ('none', 'success', 'error'));

ALTER TABLE messages ADD COLUMN accepted_at INTEGER;
ALTER TABLE messages ADD COLUMN runtime_generation INTEGER;
ALTER TABLE messages ADD COLUMN outcome TEXT
    CHECK(outcome IS NULL OR outcome IN ('success', 'error', 'cancelled', 'interrupted'));

UPDATE sessions
SET selected_connection_id = COALESCE(
        selected_connection_id,
        (
            SELECT message.connection_id
            FROM messages AS message
            WHERE message.session_id = sessions.id
              AND message.completed_at IS NOT NULL
              AND message.connection_id IS NOT NULL
              AND trim(message.connection_id) <> ''
              AND message.model_id IS NOT NULL
              AND trim(message.model_id) <> ''
            ORDER BY COALESCE(message.completed_at, message.created_at) DESC,
                     message.revision DESC,
                     message.id DESC
            LIMIT 1
        )
    ),
    selected_model_id = COALESCE(
        selected_model_id,
        (
            SELECT message.model_id
            FROM messages AS message
            WHERE message.session_id = sessions.id
              AND message.completed_at IS NOT NULL
              AND message.connection_id IS NOT NULL
              AND trim(message.connection_id) <> ''
              AND message.model_id IS NOT NULL
              AND trim(message.model_id) <> ''
            ORDER BY COALESCE(message.completed_at, message.created_at) DESC,
                     message.revision DESC,
                     message.id DESC
            LIMIT 1
        )
    );

UPDATE sessions
SET attention_kind = CASE
    WHEN unread = 0 THEN 'none'
    WHEN run_state IN ('error', 'interrupted') THEN 'error'
    ELSE COALESCE(
        (
            SELECT CASE
                WHEN message.cancelled = 1 THEN 'none'
                WHEN message.outcome IN ('error', 'interrupted') THEN 'error'
                ELSE 'success'
            END
            FROM messages AS message
            WHERE message.session_id = sessions.id
              AND message.role = 'assistant'
              AND message.completed_at IS NOT NULL
            ORDER BY COALESCE(message.completed_at, message.created_at) DESC,
                     message.revision DESC,
                     message.id DESC
            LIMIT 1
        ),
        'success'
    )
END;

UPDATE sessions
SET unread = CASE
    WHEN attention_kind = 'none' THEN 0
    ELSE 1
END;


-- Queued prompts capture the immutable task target at enqueue time so a later
-- target switch cannot redirect work the user already queued.
ALTER TABLE queued_prompts ADD COLUMN model_id TEXT;


CREATE TABLE usage_events (
    idempotency_key TEXT PRIMARY KEY,
    occurred_at INTEGER NOT NULL,
    source TEXT NOT NULL,
    project_id TEXT,
    project_label TEXT,
    session_id TEXT,
    session_label TEXT,
    connection_id TEXT,
    connection_label TEXT,
    model_id TEXT,
    model_label TEXT,
    input_tokens INTEGER,
    output_tokens INTEGER,
    cached_read_tokens INTEGER,
    reasoning_tokens INTEGER,
    reported_calls INTEGER NOT NULL DEFAULT 0,
    unreported_calls INTEGER NOT NULL DEFAULT 0,
    quality TEXT NOT NULL CHECK (quality IN ('exact', 'estimated', 'unreported')),
    terminal INTEGER NOT NULL DEFAULT 0 CHECK (terminal IN (0, 1))
);
CREATE INDEX usage_events_occurred ON usage_events(occurred_at);
CREATE INDEX usage_events_source_occurred ON usage_events(source, occurred_at);
CREATE INDEX usage_events_project_occurred ON usage_events(project_id, occurred_at);
CREATE INDEX usage_events_session_occurred ON usage_events(session_id, occurred_at);
CREATE INDEX usage_events_model_occurred ON usage_events(model_id, occurred_at);
CREATE INDEX usage_events_connection_occurred ON usage_events(connection_id, occurred_at);


CREATE TABLE subagent_runs (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    origin TEXT NOT NULL CHECK (origin IN ('native', 'managed')),
    parent_prompt_id TEXT,
    parent_message_id TEXT,
    child_session_id TEXT,
    hidden_session_id TEXT,
    connection_id TEXT,
    model_id TEXT,
    connection_label TEXT,
    model_label TEXT,
    status TEXT NOT NULL,
    activity TEXT,
    parent_revision INTEGER NOT NULL DEFAULT 0 CHECK (parent_revision >= 0),
    runtime_generation INTEGER,
    native_session_id TEXT,
    record_json TEXT NOT NULL,
    started_at INTEGER NOT NULL,
    finished_at INTEGER,
    updated_at INTEGER NOT NULL
);
CREATE INDEX subagent_runs_session_started
    ON subagent_runs(session_id, started_at, id);
CREATE INDEX subagent_runs_parent_message
    ON subagent_runs(session_id, parent_message_id, started_at);
CREATE INDEX subagent_runs_status
    ON subagent_runs(status, updated_at);
CREATE INDEX subagent_runs_target
    ON subagent_runs(connection_id, model_id, started_at);

CREATE TABLE subagent_stream_chunks (
    subagent_id TEXT NOT NULL REFERENCES subagent_runs(id) ON DELETE CASCADE,
    sequence INTEGER NOT NULL CHECK (sequence > 0),
    kind TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    PRIMARY KEY(subagent_id, sequence)
);
CREATE INDEX subagent_stream_created
    ON subagent_stream_chunks(subagent_id, created_at, sequence);


CREATE TABLE subagent_run_tombstones (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    pruned_at INTEGER NOT NULL
);
CREATE INDEX subagent_run_tombstones_session
    ON subagent_run_tombstones(session_id, pruned_at, id);


ALTER TABLE queued_prompts ADD COLUMN attachments_json TEXT NOT NULL DEFAULT '[]';


ALTER TABLE subagent_runs ADD COLUMN parent_tool_call_id TEXT;
CREATE INDEX subagent_runs_parent_tool
    ON subagent_runs(session_id, parent_message_id, parent_tool_call_id);


ALTER TABLE fusion_runs ADD COLUMN assessment_json TEXT;
ALTER TABLE fusion_runs ADD COLUMN routing_json TEXT;
ALTER TABLE fusion_runs ADD COLUMN failure_count INTEGER NOT NULL DEFAULT 0 CHECK (failure_count >= 0);
ALTER TABLE fusion_runs ADD COLUMN parent_revision INTEGER;
ALTER TABLE fusion_runs ADD COLUMN baseline_dirty_paths_json TEXT NOT NULL DEFAULT '[]';
ALTER TABLE fusion_runs ADD COLUMN delivery_status TEXT NOT NULL DEFAULT 'pending'
    CHECK (delivery_status IN ('pending', 'applied', 'conflict', 'failed'));
ALTER TABLE fusion_runs ADD COLUMN delivery_error TEXT;
ALTER TABLE fusion_runs ADD COLUMN delivery_idempotency_key TEXT;
CREATE UNIQUE INDEX fusion_runs_delivery_idempotency
    ON fusion_runs(delivery_idempotency_key)
    WHERE delivery_idempotency_key IS NOT NULL;

ALTER TABLE fusion_candidates ADD COLUMN connection_id TEXT;
ALTER TABLE fusion_candidates ADD COLUMN connection_label TEXT;
ALTER TABLE fusion_candidates ADD COLUMN model_label TEXT;
ALTER TABLE fusion_candidates ADD COLUMN phase TEXT
    CHECK (phase IS NULL OR phase IN ('economical', 'strongest'));
ALTER TABLE fusion_candidates ADD COLUMN attempt_count INTEGER NOT NULL DEFAULT 0
    CHECK (attempt_count >= 0);
ALTER TABLE fusion_candidates ADD COLUMN final_text TEXT;
ALTER TABLE fusion_candidates ADD COLUMN patch_ref TEXT;


CREATE TABLE IF NOT EXISTS task_workspaces (
    session_id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    repository_id TEXT NOT NULL,
    repository_root TEXT NOT NULL,
    checkout_path TEXT NOT NULL,
    branch TEXT,
    base_oid TEXT
);


ALTER TABLE messages ADD COLUMN acp_prompt_index INTEGER;


CREATE TABLE session_preferences (
    session_id TEXT PRIMARY KEY REFERENCES sessions(id) ON DELETE CASCADE,
    mode TEXT NOT NULL CHECK (mode IN ('ask', 'auto', 'plan', 'full-access')),
    effort TEXT NOT NULL CHECK (effort IN ('low', 'medium', 'high', 'xhigh', 'max')),
    plan_return_mode TEXT CHECK (plan_return_mode IN ('ask', 'auto', 'full-access'))
);


CREATE TABLE plan_canvas_plans (
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    tool_call_id TEXT NOT NULL,
    record_json TEXT NOT NULL,
    PRIMARY KEY(session_id, tool_call_id)
);
