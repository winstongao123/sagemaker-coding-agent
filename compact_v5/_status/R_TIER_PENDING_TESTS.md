# R-tier Pending Test Matrix

Date: 2026-05-03

This table is generated from the production-readiness contract in
`r_tier_test_matrix.json`. It is the human-readable queue for AFK execution.

Production-ready means every row is `READY`, total local spend is at or below
`$14.25`, AWS Budget remains healthy, and final review + user F5 signoff pass.

| Test | Current status | Why pending | Benefit | Ready criterion |
|---|---|---|---|---|
| R1 | IN_PROGRESS | AWS call #1 found Unicode stdout crash; fix pushed, needs fixed-code review and rerun | Full composite tool/workflow proof | AWS pass + telemetry + quality + gate |
| R2 | PENDING_EXECUTABLE | Test code missing | Long-context compaction/cache proof | Executable + Phase A + AWS pass |
| R3 | PENDING_EXECUTABLE | Test code missing | Sub-agent orchestration proof | Subagent telemetry + parent synthesis |
| R4 | PENDING_EXECUTABLE | Test code missing | PS#3 cold-cache idle recovery | Idle/resume compact evidence |
| R5 | PENDING_EXECUTABLE | Test code missing | PS#7 exec-limit recovery | 201st exec blocked; other tools continue |
| R6 | PENDING_EXECUTABLE | Test code missing | `/dream` memory consolidation proof | Required facts preserved |
| R7 | PENDING_EXECUTABLE | Test code missing | Model-switch/cache invariant proof | Haiku->Sonnet behavior documented |
| R8 | PENDING_EXECUTABLE | Mock R-tier test missing | Free malformed JSON repair proof | Mock repair ladder pass |
| R9 | PENDING_EXECUTABLE | Test code missing | Approval/diff/audit proof | Approve/deny/always asserted |
| R10 | PENDING_EXECUTABLE | Test code missing | Save/load cost persistence proof | Cost/history restored |
| R11 | PENDING_EXECUTABLE | Test code missing | Production Sonnet compatibility | Sonnet workflow pass under cap |
| R12 | PENDING_EXECUTABLE | Test code missing | Unicode/malformed args robustness | No crash, recovery visible |
| R13 | PENDING_EXECUTABLE | Test code missing | Coding accuracy proof | 5/5 assertions pass or scored |
| R14 | PENDING_EXECUTABLE | Test code missing | Multi-file refactor proof | Pytest green + grep clean |
| R15 | PENDING_EXECUTABLE | Test code missing | Debugging proof | Both bugs fixed, no false positives |
| R16 | PENDING_EXECUTABLE | Test code missing | Long-session app-build proof | App/tests pass, compaction reviewed |
| R17 | EXECUTABLE_PENDING_RUN | Test exists but no AWS evidence yet | PS#4 thinking visibility proof | Thinking blocks in history/telemetry |
| R18-E1 | PENDING_EXECUTABLE | Edge test missing | Throttle/retry behavior | 429 handled or escalated as infra |
| R18-E2 | PENDING_EXECUTABLE | Mock edge test missing | 5xx recovery without forced AWS fault | Mock 5xx ladder pass |
| R18-E3 | PENDING_EXECUTABLE | Edge test missing | Cost-cap timing proof | Cap halt/warning evidence |
| R18-E4 | PENDING_EXECUTABLE | Edge test missing | Skill alias activation proof | Alias activates expected skill |
| R18-E5 | PENDING_EXECUTABLE | Mock edge test missing | Corrupt session recovery | Clean error/recovery |
| R18-E6 | PENDING_EXECUTABLE | Edge test missing | Missing/empty file recovery | Agent recovers from tool error |
| R18-E7 | PENDING_EXECUTABLE | Edge test missing | Long output truncation proof | Truncation visible, agent continues |
| R18-E8 | PENDING_EXECUTABLE | Edge test missing | Concurrent sub-agent race proof | No shared-state corruption |
| R18-E9 | PENDING_EXECUTABLE | Mock edge test missing | Disk-full snapshot safety | Mock write failure safe |
| R18-E10 | PENDING_EXECUTABLE | Edge test missing | Plan-mode allowlist proof | Mutating tool blocked/audited |
| R18-E11 | PENDING_EXECUTABLE | Edge test missing | Timeout/compaction coordination | Parent recovers |
| R18-E12 | PENDING_EXECUTABLE | Mock edge test missing | Audit rotation proof | Rotation behavior tested |
| R18-E13 | PENDING_EXECUTABLE | Edge test missing | Unicode/RTL memory proof | Unicode/RTL preserved |
| R18-E14 | PENDING_EXECUTABLE | Edge test missing | `/dream` atomicity proof | No partial corrupt memory |
| R18-E15 | PENDING_EXECUTABLE | Edge test missing | Cache TTL behavior proof | TTL handling documented |
| R19-U1 | PENDING_EXECUTABLE | UX test missing | Ambiguity handling | Clarifies instead of blind edit |
| R19-U2 | PENDING_EXECUTABLE | UX test missing | Contradictory requirement handling | Conflict flagged |
| R19-U3 | PENDING_EXECUTABLE | UX test missing | Hidden dependency refactor proof | Search before edit; tests pass |
| R19-U4 | PENDING_EXECUTABLE | UX test missing | Conflicting sub-agent reconciliation | Evidence-based parent decision |
| R19-U5 | PENDING_EXECUTABLE | UX test missing | Sub-agent failure recovery | Parent completes after child failure |
| R19-U6 | PENDING_EXECUTABLE | UX test missing | Garbage tool output recovery | Retry/alternative path succeeds |
| R19-U7 | PENDING_EXECUTABLE | UX test missing | Repeated-call circuit breaker proof | Third repeat blocked, alternative used |
| R19-U8 | PENDING_EXECUTABLE | UX test missing | Memory conflict latest-wins proof | Uses latest preference |
| R19-U9 | PENDING_EXECUTABLE | UX test missing | `/dream` semantic preservation | All required facts preserved |
| R19-U10 | PENDING_EXECUTABLE | UX test missing | Long coherence with switches/compactions | Final task succeeds |

## Cost summary

The canonical matrix totals `$14.25` exactly:

- R1-R12: `$6.50`
- R13-R16: `$2.75`
- R17: `$0.30`
- R18-E1..E15: `$1.60`
- R19-U1..U10: `$3.10`

Use Haiku 4.5 AU for all tests except Sonnet-required cases. Sonnet cases are
R7 switch, R11, and R17. Mock cases are R8 and R18-E2/E5/E9/E12.
