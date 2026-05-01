# OptionsIQ Session Start

Read ALL 6 files below IN ORDER before writing a single line of code or making any claim about system state. Do not skip or reorder. Do not ask the user to re-explain anything.

## Step 1 — Read all startup files (parallel where possible)

1. Read `CLAUDE_CONTEXT.md` — current state, known issues, next priorities
2. Read `docs/stable/GOLDEN_RULES.md` — constraints, personas, process rules
3. Read `docs/stable/ROADMAP.md` — phase status, done vs pending
4. Read the latest `docs/status/PROJECT_STATUS_DAY{N}_SHORT.md` — find N from CLAUDE_CONTEXT.md header
5. Read the latest `docs/versioned/KNOWN_ISSUES_DAY{N}.md` — find N from CLAUDE_CONTEXT.md header
6. Read `memory/MEMORY.md` — persistent memory: user preferences, feedback, project state

Read `docs/stable/API_CONTRACTS.md` ONLY if this session will touch API endpoints.

## Step 2 — State session status

After reading all files, output exactly this summary:

- **Version:** (from CLAUDE_CONTEXT.md header)
- **Day:** (current day number)
- **Tests:** (current test count)
- **Top priority:** (P0 from Next Session Priorities)
- **Open blockers:** (any HIGH severity issues)
- **What shipped last session:** (one line from PROJECT_STATUS)

## Step 3 — Ask

End with: "What would you like to focus on today?"

## Behavioral rules (non-negotiable)

- Do NOT ask the user to re-explain the project
- Do NOT jump to fixing anything before understanding current state
- Do NOT assume file structure — verify from actual files
- Do NOT skip files because "context was loaded earlier" — always re-read at session start
- Apply both personas from Golden Rule 22 to every decision: Architect (Rule 3/4/11) + Quant Trader (Rule 21)
