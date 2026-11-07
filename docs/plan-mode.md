# Plan applies to one turn

Use `/plan TASK` to plan a task, or `/plan` to make the next submitted turn
read-only. `--plan` has the same one-turn scope.

Plan exits automatically when the reply finishes, you cancel it, or execution
fails or disconnects. The following message uses your selected manual, auto or
full permission mode. Plan tools and subagents remain read-only until that turn
has stopped and cleaned up. An automatically queued follow-up is a new turn.

Resuming or switching sessions does not restore Plan, including older sessions.
Saved plan files remain available. Exiting Plan does not execute them or approve
tools; manual approval continues to apply when selected. `/plan approve` remains
available to clear an armed Plan selection before sending a task.
