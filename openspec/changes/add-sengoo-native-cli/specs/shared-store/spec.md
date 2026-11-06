## ADDED Requirements

### Requirement: Independent clients share sessions without duplicate execution
Desktop and CLI SHALL share configuration and public conversation records while
exclusive execution is protected by OS ownership and transaction fencing.

#### Scenario: Both clients accept a turn
- **WHEN** desktop and CLI concurrently start work in one session
- **THEN** exactly one obtains execution authority and the other observes busy.

#### Scenario: A second client opens the database
- **WHEN** another client is executing a session
- **THEN** opening/reading does not recover or interrupt that live session.

#### Scenario: An old owner sends a delayed event
- **WHEN** an event has an obsolete execution fence
- **THEN** it cannot modify public messages or the new owner's terminal state.

#### Scenario: A delayed turn has not created its assistant placeholder
- **WHEN** an accepted turn ends and another turn starts in the same desktop
  instance before the first dispatch or error callback returns
- **THEN** dispatch, new assistant insertion, fallback errors and terminal state
  changes validate the original accepted user message's execution fence
- **AND** the obsolete callback cannot acquire the later turn's fence or lease.

#### Scenario: A desktop uses edit and resend or an ACP fallback route
- **WHEN** the desktop accepts an edited prompt or sends through its shared or
  managed ACP fallback
- **THEN** it claims the same cross-process session lease before provider work
- **AND** competing clients observe busy until fenced completion or rollback.

#### Scenario: A user hands off an idle session
- **WHEN** the old owner has stopped and released its processes and lock
- **THEN** the other engine continues using public history and its own binding.

#### Scenario: A crashed executor has unverified tool cleanup
- **WHEN** its OS lock is released but a tool may still be running
- **THEN** the session remains interrupted and takeover is refused until cleanup
  is proven; the client does not infer completion from a heartbeat or dead PID.
