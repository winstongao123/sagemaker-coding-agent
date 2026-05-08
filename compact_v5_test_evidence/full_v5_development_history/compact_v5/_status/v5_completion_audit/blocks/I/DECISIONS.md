# Block I Decisions

Date: 2026-05-05

## I-D001: Close I-12 with a small deterministic parser

Decision: Implement the named I-12 parser drift cases locally instead of keeping the historical deferral.

Reason:

- `SYNTHESIS_MASTER.md` is canonical and lists I-12 as HIGH/CLEAN.
- The redo protocol does not permit silent deferrals.
- A small deterministic parser covers the real skill metadata failures without pulling in a new YAML dependency or adding shell execution.

## I-D002: Keep skill markdown text-only

Decision: Continue not porting Runnable inline shell-command execution in skill prompts.

Reason:

- v5 is Bedrock/SageMaker-oriented and keeps skills as prompt context.
- Executing commands from skill markdown would add a new unsafe runtime path.
- I-6 only substitutes safe variables; it does not execute them.

## I-D003: Keep command consolidation

Decision: Do not add any `/project-*` commands in Block I.

Reason:

- Software-project workflow behavior belongs in existing commands and skills.
- Block I improves the skill surface used by existing `/skill`, `/verify`, debug, remember, init, verifier, and skillify workflows.
