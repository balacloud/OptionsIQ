# OptionsIQ Session Close

Execute every step below IN ORDER. Claude does all file updates — no manual user action needed. Do not skip any step. Do not ask the user to run git commands.

## Step 1 — Confirm what happened this session

Before updating any doc, answer these internally (check against actual code changes):
- Which bugs were fixed? → drives KNOWN_ISSUES update
- Which bugs were found (new)? → drives KNOWN_ISSUES update
- Did any API endpoint change or get added? → drives API_CONTRACTS update
- Did we learn a new process rule or architectural lesson? → drives GOLDEN_RULES update
- What is the new version number? (patch bump for fixes, minor for features)

## Step 2 — Update all docs (in this order)

### 2a. Create `docs/versioned/KNOWN_ISSUES_DAY{N}.md` (new file each day)
- Mark resolved issues with ✅ RESOLVED Day {N} + root cause summary
- Add any new issues found this session with severity (HIGH/MEDIUM/LOW) and exact reproduction
- Carry forward all still-open issues verbatim

### 2b. Create `docs/status/PROJECT_STATUS_DAY{N}_SHORT.md` (new file each day)
- What shipped (each fix/feature with root cause + verification result)
- Current test count
- Open issues table (ID, severity, description)
- Next session priorities (P0 → P4, with effort estimate)

### 2c. Update `CLAUDE_CONTEXT.md`
- Header: Last Updated → Day {N}, Current Version → vX.Y.Z, Project Phase blurb
- Startup checklist filenames → DAY{N}
- Current State table → reflect today's changes
- Known Issues section → remove resolved, add new
- Session Log → add new row for today
- Next Session Priorities → replace with today's P0-P4

### 2d. Update `docs/stable/ROADMAP.md`
- Tick completed items with ✅ Day {N}
- Add new open items under the correct phase
- Add new row to Version Log table

### 2e. Update `README.md`
- Version badge line: `> **vX.Y.Z** — Day {N} (date)`

### 2f. Update `memory/MEMORY.md`
- Current Phase section → new version, what shipped, what's next
- Startup checklist filenames → DAY{N}
- Key Source Files → update any files that changed (line counts, status)
- Day {N+1} Priorities → match CLAUDE_CONTEXT next priorities

### 2g. Update `docs/stable/API_CONTRACTS.md` — ONLY if any endpoint was added or changed
### 2h. Update `docs/stable/GOLDEN_RULES.md` — ONLY if a new rule or process lesson was learned

## Step 3 — Git commit and push

Stage only relevant files (never `.pids`, `backend/data/`, `backend/backend.log.prev`):

```
git add CLAUDE_CONTEXT.md README.md memory/MEMORY.md \
  docs/versioned/KNOWN_ISSUES_DAY{N}.md \
  docs/status/PROJECT_STATUS_DAY{N}_SHORT.md \
  docs/stable/ROADMAP.md \
  [any changed source files]
git commit -m "Day {N}: <one line summary> (vX.Y.Z)

<2-3 bullet points of what changed>

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
git push origin main
```

## Step 4 — Confirm to user

Output exactly:
- Files updated: (list each doc touched)
- Commit: (short hash + message)
- Pushed: ✅
- Next session: start with `/session-start`, then focus on (P0 item)
