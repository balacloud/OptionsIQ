# Log a Known Issue (KI)

You are logging a new known issue to the OptionsIQ issue tracker. The issue description is:

> $ARGUMENTS

## Steps

### Step 1 — Find the current day and KI file

Read `CLAUDE_CONTEXT.md` and extract:
- The current day number N (from the `> **Last Updated:** Day N` header line)

The active known issues file is: `docs/versioned/KNOWN_ISSUES_DAY{N}.md`

### Step 2 — Find the next KI number

Read the active KNOWN_ISSUES file. Scan ALL lines for patterns matching `KI-###` (e.g. KI-096, KI-101). Find the highest number present anywhere in the file (resolved or open). The new KI number = highest + 1.

If no KI numbers exist in the file, start at KI-101.

### Step 3 — Determine severity

Classify the issue from the description:

- **HIGH**: Gate logic wrong, data silently corrupted, wrong verdict shown to user, test suite broken
- **MEDIUM**: Design gap, edge case not handled, incorrect display, missing warning
- **LOW**: Polish, cosmetic, deferred feature, minor UX gap

When in doubt, use MEDIUM.

### Step 4 — Append the new KI entry

Find the `## Still Open (Carried Forward)` section in the KNOWN_ISSUES file. Insert the new entry at the TOP of that section (before any existing open issues), in this exact format:

```
### KI-{N}: {one-line title derived from the description} (SEVERITY — OPEN)
**Symptom:** {what the user sees or what goes wrong — from the description}
**Root cause:** TBD
**Fix:** Pending
```

Leave a blank line before and after the entry.

### Step 5 — Confirm

Output exactly:

```
KI-{N} logged ({SEVERITY}) — "{one-line title}" → docs/versioned/KNOWN_ISSUES_DAY{day}.md
```

Nothing else. Do not summarize the full file. Do not suggest next steps unless the user asks.
