WITH origin_objects AS (
    SELECT session_id,
           CASE WHEN json_type(mode_json,'$.session_origin')='object'
                THEN json_extract(mode_json,'$.session_origin') ELSE '{}' END AS origin
    FROM shared_modes
    WHERE (SELECT count(*) FROM json_each(mode_json) WHERE key='session_origin')=1
), declared_children AS (
    SELECT session_id FROM origin_objects
    WHERE json_type(origin,'$.version')='integer' AND json_extract(origin,'$.version')=1
      AND json_extract(origin,'$.kind')='child'
      AND json_type(origin,'$.parent_session_id')='text'
      AND length(json_extract(origin,'$.parent_session_id')) BETWEEN 1 AND 256
      AND json_extract(origin,'$.parent_session_id')<>session_id
      AND (SELECT count(*) FROM json_each(origin) WHERE key='version')=1
      AND (SELECT count(*) FROM json_each(origin) WHERE key='kind')=1
      AND (SELECT count(*) FROM json_each(origin) WHERE key='parent_session_id')=1
), ledger_payloads AS (
    SELECT session_id AS parent_id,name,
           CASE WHEN length(CAST(result AS BLOB))<=262144 AND json_valid(result)
                THEN result ELSE '{}' END AS payload
    FROM shared_tool_ledger
    WHERE state='complete' AND name IN('spawn_agent','list_agents','wait_agents')
), ledger_objects AS (
    SELECT parent_id,payload AS child FROM ledger_payloads WHERE name='spawn_agent'
    UNION ALL
    SELECT l.parent_id,CASE WHEN j.type='object' THEN j.value ELSE '{}' END
    FROM ledger_payloads l,json_each(l.payload,'$.children') j
    WHERE l.name IN('list_agents','wait_agents')
), ledger_children AS (
    SELECT parent_id,json_extract(child,'$.session_id') AS child_id
    FROM ledger_objects
    WHERE json_type(child,'$.session_id')='text'
      AND json_extract(child,'$.role') IN('explore','plan','general')
      AND (SELECT count(*) FROM json_each(child) WHERE key='session_id')=1
      AND (SELECT count(*) FROM json_each(child) WHERE key='role')=1
), child_sessions AS (
    SELECT session_id AS id FROM declared_children
    UNION
    SELECT c.id FROM ledger_children l
    JOIN sessions p ON p.id=l.parent_id
    JOIN sessions c ON c.id=l.child_id AND c.project_id=p.project_id AND c.id<>p.id
    UNION
    SELECT c.id FROM subagent_runs r
    JOIN sessions p ON p.id=r.session_id
    JOIN sessions c ON (c.id=r.child_session_id OR c.id=r.hidden_session_id)
                      AND c.project_id=p.project_id AND c.id<>p.id
)
