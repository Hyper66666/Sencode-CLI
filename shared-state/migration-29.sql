-- Shared store v1. Both engines supply per-connection sengoo_context(key).
CREATE TABLE shared_contract (
    id INTEGER PRIMARY KEY CHECK(id=1), version INTEGER NOT NULL,
    minimum_writer INTEGER NOT NULL
);
INSERT INTO shared_contract VALUES(1,1,1);
CREATE TABLE shared_executions (
    session_id TEXT PRIMARY KEY REFERENCES sessions(id) ON DELETE CASCADE,
    owner_instance_id TEXT NOT NULL, execution_id TEXT NOT NULL,
    engine TEXT NOT NULL, fence INTEGER NOT NULL CHECK(fence>0),
    active INTEGER NOT NULL CHECK(active IN(0,1)),
    cleanup_required INTEGER NOT NULL DEFAULT 0 CHECK(cleanup_required IN(0,1)),
    started_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);
CREATE TABLE shared_history (
    message_id TEXT PRIMARY KEY REFERENCES messages(id) ON DELETE CASCADE,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    message_json TEXT NOT NULL CHECK(json_valid(message_json)),
    execution_id TEXT NOT NULL, fence INTEGER NOT NULL
);
CREATE TABLE shared_tool_ledger (
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    call_id TEXT NOT NULL, execution_id TEXT NOT NULL, fence INTEGER NOT NULL,
    name TEXT NOT NULL, arguments TEXT NOT NULL,
    state TEXT NOT NULL CHECK(state IN('running','complete','interrupted')),
    result TEXT, updated_at INTEGER NOT NULL, PRIMARY KEY(session_id,call_id)
);
CREATE TABLE shared_modes (
    session_id TEXT PRIMARY KEY REFERENCES sessions(id) ON DELETE CASCADE,
    mode_json TEXT NOT NULL CHECK(json_valid(mode_json)), updated_at INTEGER NOT NULL
);
CREATE TABLE shared_engine_bindings (
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    connection_id TEXT NOT NULL, engine TEXT NOT NULL,
    native_session_id TEXT NOT NULL, synced_revision INTEGER NOT NULL,
    generation INTEGER NOT NULL, PRIMARY KEY(session_id,connection_id,engine)
);
INSERT INTO shared_engine_bindings
SELECT session_id,connection_id,'desktop',native_session_id,synced_revision,generation
FROM runtime_bindings;
CREATE TABLE shared_changes (
    seq INTEGER PRIMARY KEY AUTOINCREMENT, entity TEXT NOT NULL,
    entity_id TEXT NOT NULL, operation TEXT NOT NULL, instance_id TEXT,
    changed_at INTEGER NOT NULL
);
CREATE TABLE shared_usage (
    request_id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    connection_id TEXT NOT NULL, model_id TEXT NOT NULL,
    input_tokens INTEGER NOT NULL CHECK(input_tokens>=0),
    output_tokens INTEGER NOT NULL CHECK(output_tokens>=0), created_at INTEGER NOT NULL
);
ALTER TABLE messages ADD COLUMN shared_fence INTEGER;
CREATE INDEX shared_history_session ON shared_history(session_id,message_id);
CREATE INDEX shared_changes_entity ON shared_changes(entity,seq);
