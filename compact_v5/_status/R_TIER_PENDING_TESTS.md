# R-tier Pending Test Matrix

Date: 2026-05-05

This table is maintained from the production-readiness contract in
`r_tier_test_matrix.json`. It is human-readable status only. Execution order is
controlled by `v5_completion_audit/OPTIMIZED_AWS_VALIDATION_PLAN.md`, not by
this file.

Production-ready means every row is `READY`, total local spend is at or below
`$14.25`, AWS Budget remains healthy, and final review + user F5 signoff pass.

| Test | Current status | Why pending | Benefit | Ready criterion |
|---|---|---|---|---|
| R1 | IN_PROGRESS | AWS call #1 found Unicode stdout crash; fix pushed, needs fixed-code review and rerun | Full composite tool/workflow proof | AWS pass + telemetry + quality + gate |
| R2 | PENDING_EXECUTABLE | Test code missing | Long-context compaction/cache proof | Executable + Phase A + AWS pass |
| R3 | READY | Existing AWS call2 evidence reused for Stage 6; not rerun per optimized plan and Claude Phase A/Phase C | Sub-agent orchestration proof | Subagent telemetry + parent synthesis |
| R4 | EXECUTABLE_PENDING_REVIEW | Test exists; needs Phase A review before real idle/AWS run | PS#3 cold-cache idle recovery | Idle/resume compact evidence |
| R5 | PENDING_EXECUTABLE | Test code missing | PS#7 exec-limit recovery | 201st exec blocked; other tools continue |
| R6 | EXECUTABLE_PENDING_REVIEW | Zero-cost spec exists; needs Phase A review/execution | `/dream` memory consolidation proof | Required facts preserved |
| R7 | EXECUTABLE_PENDING_REVIEW | Zero-cost spec exists; needs Phase A review/execution | Model-switch/cache invariant proof | Haiku->Sonnet behavior documented |
| R8 | EXECUTABLE_PENDING_REVIEW | Zero-cost mock spec exists; needs local mock implementation/review | Free malformed JSON repair proof | Mock repair ladder pass |
| R9 | EXECUTABLE_PENDING_REVIEW | Zero-cost spec exists; needs Phase A review/execution | Approval/diff/audit proof | Approve/deny/always asserted |
| R10 | EXECUTABLE_PENDING_REVIEW | Zero-cost spec exists; needs Phase A review/execution | Save/load cost persistence proof | Cost/history restored |
| R11 | EXECUTABLE_PENDING_REVIEW | Zero-cost spec exists; needs Phase A review/execution | Production Sonnet compatibility | Sonnet workflow pass under cap |
| R12 | EXECUTABLE_PENDING_REVIEW | Zero-cost spec exists; needs Phase A review/execution | Unicode/malformed args robustness | No crash, recovery visible |
| R13 | READY | AWS pass, Phase C GENUINE_PASS, gate pass, committed/pushed | Coding accuracy proof | 5/5 assertions pass or scored |
| R14 | READY_WITH_RECURRENCE_WATCH | AWS artifact pass, Phase C GENUINE_PASS, gate pass, committed/pushed; R14/R19-U3 process blocker fixed locally, Claude-approved, and Stage 5 call2 showed no recurrence | Multi-file refactor proof | Pytest green + grep clean |
| R15 | READY | AWS pass, Phase C GENUINE_PASS, gate pass, committed/pushed | Debugging proof | Both bugs fixed, no false positives |
| R16 | READY | Stage 7 call1 passed on Haiku with Phase C `GENUINE_PASS`, `software_builder_subchecks`, numeric cache evidence, forced/local compaction evidence, no R14/R19-U3 loop recurrence, and gate pass | Long-session app-build proof | App/tests pass, compaction reviewed |
| R17 | EXECUTABLE_PENDING_RUN | Test exists but no AWS evidence yet | PS#4 thinking visibility proof | Thinking blocks in history/telemetry |
| R18-E1 | EXECUTABLE_PENDING_REVIEW | Zero-cost edge spec exists; needs Phase A review/execution | Throttle/retry behavior | 429 handled or escalated as infra |
| R18-E2 | EXECUTABLE_PENDING_REVIEW | Zero-cost mock spec exists; needs local mock implementation/review | 5xx recovery without forced AWS fault | Mock 5xx ladder pass |
| R18-E3 | EXECUTABLE_PENDING_REVIEW | Zero-cost edge spec exists; needs Phase A review/execution | Cost-cap timing proof | Cap halt/warning evidence |
| R18-E4 | EXECUTABLE_PENDING_REVIEW | Zero-cost edge spec exists; needs Phase A review/execution | Skill alias activation proof | Alias activates expected skill |
| R18-E5 | EXECUTABLE_PENDING_REVIEW | Zero-cost mock spec exists; needs local mock implementation/review | Corrupt session recovery | Clean error/recovery |
| R18-E6 | EXECUTABLE_PENDING_REVIEW | Zero-cost edge spec exists; needs Phase A review/execution | Missing/empty file recovery | Agent recovers from tool error |
| R18-E7 | READY | Stage 5 call2 passed under $0.10 planned cap after deterministic replay redesign; call1 diagnostic cap exceed remains recorded | Long output truncation proof | Truncation visible, agent continues |
| R18-E8 | EXECUTABLE_PENDING_REVIEW | Zero-cost edge spec exists; needs Phase A review/execution | Concurrent sub-agent race proof | No shared-state corruption |
| R18-E9 | EXECUTABLE_PENDING_REVIEW | Zero-cost mock spec exists; needs local mock implementation/review | Disk-full snapshot safety | Mock write failure safe |
| R18-E10 | EXECUTABLE_PENDING_REVIEW | Zero-cost edge spec exists; needs Phase A review/execution | Plan-mode allowlist proof | Mutating tool blocked/audited |
| R18-E11 | EXECUTABLE_PENDING_REVIEW | Zero-cost edge spec exists; needs Phase A review/execution | Timeout/compaction coordination | Parent recovers |
| R18-E12 | EXECUTABLE_PENDING_REVIEW | Zero-cost mock spec exists; needs local mock implementation/review | Audit rotation proof | Rotation behavior tested |
| R18-E13 | EXECUTABLE_PENDING_REVIEW | Zero-cost edge spec exists; needs Phase A review/execution | Unicode/RTL memory proof | Unicode/RTL preserved |
| R18-E14 | EXECUTABLE_PENDING_REVIEW | Zero-cost edge spec exists; needs Phase A review/execution | `/dream` atomicity proof | No partial corrupt memory |
| R18-E15 | EXECUTABLE_PENDING_REVIEW | Zero-cost edge spec exists; needs Phase A review/execution | Cache TTL behavior proof | TTL handling documented |
| R19-U1 | READY_WITH_LOW_FOLLOWUP | Stage 4 bundle AWS pass, Phase C GENUINE_PASS, gate pass; low follow-up for direct chat clarification vs ask_user | Ambiguity handling | Clarifies instead of blind edit |
| R19-U2 | READY | Stage 4 bundle AWS pass, Phase C GENUINE_PASS, gate pass | Contradictory requirement handling | Conflict flagged |
| R19-U3 | READY | Stage 5 call2 passed on Haiku with search-before-edit, pytest pass, no repeated guard/exec loop, Phase C GENUINE_PASS, and gate pass | Hidden dependency refactor proof | Search before edit; tests pass |
| R19-U4 | READY | Stage 6 call2 passed on Haiku after Claude Phase B retry approval; Phase C `GENUINE_PASS`; gate pass; call1 diagnostic spend preserved | Conflicting sub-agent reconciliation | Evidence-based parent decision + Phase C + gate |
| R19-U5 | READY | Stage 6 call2 passed on Haiku after predicate fix and Claude Phase B retry approval; Phase C `GENUINE_PASS`; gate pass; call1 diagnostic spend preserved | Sub-agent failure recovery | Parent completes after child failure + Phase C + gate |
| R19-U6 | READY | Stage 5 call2 passed with malformed-output recovery, Phase C GENUINE_PASS, and gate pass | Garbage tool output recovery | Retry/alternative path succeeds |
| R19-U7 | READY | Stage 5 call2 passed with breaker_fired=true, exactly two actual bait calls, Phase C GENUINE_PASS, and gate pass | Repeated-call circuit breaker proof | Third repeat blocked, alternative used |
| R19-U8 | EXECUTABLE_PENDING_REVIEW | Zero-cost UX spec exists; needs Phase A review/execution | Memory conflict latest-wins proof | Uses latest preference |
| R19-U9 | EXECUTABLE_PENDING_REVIEW | Zero-cost UX spec exists; needs Phase A review/execution | `/dream` semantic preservation | All required facts preserved |
| R19-U10 | EXECUTABLE_PENDING_REVIEW | Zero-cost UX spec exists; needs Phase A review/execution | Long coherence with switches/compactions | Final task succeeds |

## Cost summary

The canonical matrix totals `$14.25` exactly:

- R1-R12: `$6.50`
- R13-R16: `$2.75`
- R17: `$0.30`
- R18-E1..E15: `$1.60`
- R19-U1..U10: `$3.10`

Use Haiku 4.5 AU for all tests except Sonnet-required cases. Sonnet cases are
R7 switch, R11, and R17. Mock cases are R8 and R18-E2/E5/E9/E12.
