# SlopeSniper + MoltBot Compatibility Assessment

*Created: 2026-01-28 | Updated: 2026-01-29 | Version: 0.3.1*

## Executive Summary

SlopeSniper is **fully compatible** with MoltBot workflows. After reviewing MoltBot's architecture and real-world usage patterns, the key insight is:

**MoltBot is the intelligent orchestrator.** It:
1. Receives user's natural language (Telegram, Discord, WhatsApp, etc.)
2. Reads our SKILL.md for guidance on what commands to use
3. Executes our CLI and receives JSON output
4. **Interprets the JSON and formats a human-friendly response**

This means we **don't need to worry about output formatting for different platforms** - MoltBot handles that. Our job is to return clean, structured JSON with meaningful field names.

| Category | Status | Notes |
|----------|--------|-------|
| CLI Output Format | PASS | JSON output, meaningful field names |
| SKILL.md Guidance | PASS | Comprehensive NLP examples, clear instructions |
| Error Handling | PASS | JSON errors with context |
| Script Interoperability | PASS | Clean JSON, exit codes |
| Background Tasks | INVESTIGATE | MoltBot has sessionId pattern - need to verify alignment |
| Real-time Data | PASS | SKILL.md instructs AI to always fetch fresh |

---

## 1. CLI Output Format Compatibility

### Current Implementation

SlopeSniper uses **JSON output to stdout** for all commands:

```python
def print_json(data: dict) -> None:
    print(json.dumps(data, indent=2, default=str))
```

**Exit Codes:**
- `0` = Success
- `1` = Error (with JSON error in stdout)

**Quiet Mode:**
```bash
slopesniper buy BONK 25 --quiet
```
- Suppresses all logging
- Returns only JSON result

### MoltBot Compatibility

| Pattern | SlopeSniper | MoltBot Expected | Status |
|---------|-------------|------------------|--------|
| JSON output | `{"success": true, ...}` | JSON or text | PASS |
| Error format | `{"error": "msg"}` | Any parseable | PASS |
| Exit codes | 0/1 | 0/non-zero | PASS |
| Quiet mode | `--quiet` flag | Suppressed noise | PASS |

**Verdict: FULLY COMPATIBLE**

---

## 2. Messaging Platform Considerations

### Why This Is NOT a Concern

MoltBot's AI interprets our JSON output and generates human-friendly responses. It doesn't send raw JSON to users.

**Example flow:**
```
User (Telegram): "What's in my wallet?"
     ↓
MoltBot executes: slopesniper wallet --quiet
     ↓
SlopeSniper returns: {"wallet": {"address": "7xK...", "tokens": [...]}}
     ↓
MoltBot AI formats: "You have 3 tokens worth $260:
• 1M BONK ($25.50)
• 500 WIF ($150.00)
• 100 JUP ($85.00)"
```

The AI naturally summarizes large outputs. MoltBot also has:
- Block streaming with configurable chunk sizes
- Platform-aware formatting
- Markdown support where available

### What We DO Need

1. **Meaningful JSON field names** - So MoltBot can describe them naturally
2. **Consistent structure** - So patterns are predictable
3. **Error context** - So MoltBot can explain what went wrong

**Our current output is already well-structured for this.**

---

## 3. Long-Running Task Patterns

### How MoltBot Handles Background Tasks

MoltBot has a built-in pattern for long-running commands using `exec` with `background:true`:

```bash
# MoltBot can run any command in background
bash background:true command:"slopesniper watch BONK --target-price 0.01"
# Returns: {"sessionId": "abc123"}

# MoltBot's process tool manages the session
process action:poll sessionId:abc123   # Get output
process action:log sessionId:abc123    # Get logs
process action:kill sessionId:abc123   # Terminate
```

### SlopeSniper Current Implementation

**Daemon Mode (for auto-sell targets):**
```bash
slopesniper daemon start           # Starts background monitoring
slopesniper daemon status          # Check status
slopesniper daemon logs --tail 20  # View logs
slopesniper daemon stop            # Stop
```

**Watch Mode (foreground, blocking):**
```bash
slopesniper watch BONK --target-price 0.01 --interval 5
# Prints progress to stdout every interval
# Blocks until target hit or Ctrl+C
```

### Analysis: Is This a Problem?

**Likely NO.** MoltBot's `bash background:true` can wrap ANY command:

```bash
# MoltBot would do:
bash background:true command:"slopesniper watch BONK --mcap 1000000000 --sell all"

# This creates a MoltBot-managed session that:
# - Captures stdout (our progress output)
# - Can be polled via process action:poll
# - Can be killed via process action:kill
```

Our `watch` command already outputs progress to stdout, which MoltBot captures.

### What About the Daemon?

The daemon is for **persistent background monitoring** that survives MoltBot restarts. It's complementary:

| Use Case | Solution |
|----------|----------|
| "Watch BONK until $1B mcap" | MoltBot runs `watch` in background |
| "Monitor all my targets 24/7" | User starts daemon with `daemon start` |

### Recommendation: Verify, Don't Over-Engineer

**Action:** Test actual MoltBot behavior before adding complexity.

1. Test `bash background:true command:"slopesniper watch ..."` in MoltBot
2. Verify `process action:poll` captures our stdout
3. If it works, document it in SKILL.md
4. Only add sessionId pattern if MoltBot's built-in backgrounding doesn't work

**Do NOT add a parallel `slopesniper process` interface unless proven necessary.**

---

## 4. Script Interoperability

### Current Strengths

SlopeSniper is **well-suited** for script interoperability:

```bash
# Parse JSON output
RESULT=$(slopesniper buy BONK 25 --quiet)
SUCCESS=$(echo "$RESULT" | jq -r '.success')

# Check exit code
if slopesniper check SCAM_TOKEN --quiet; then
  echo "Token is safe"
else
  echo "Token failed safety check"
fi

# Chain commands
slopesniper price BONK --quiet | jq -r '.price_usd'
```

### Interop with Other MoltBot Skills

SlopeSniper can be called from other skills:

```bash
# From another skill's context
bash command:"slopesniper buy BONK 25 --quiet"

# With environment variables
SOLANA_PRIVATE_KEY=xxx bash command:"slopesniper buy BONK 25"
```

### Recommendations

**Priority: LOW** (already good)

1. **Document JSON schemas** for each command output
2. **Add `--format` flag** for future flexibility
   ```bash
   slopesniper wallet --format json  # Default
   slopesniper wallet --format csv   # For spreadsheets
   ```

---

## 5. Cross-Provider Messaging

### MoltBot Cross-Provider Config

```json
{
  "agents": {
    "defaults": {
      "tools": {
        "message": {
          "crossContext": {
            "allowAcrossProviders": true,
            "marker": { "enabled": true, "prefix": "[from {channel}] " }
          }
        }
      }
    }
  }
}
```

### SlopeSniper Considerations

- Users may start a trade on Telegram, check status on Discord
- Wallet state is **local to the machine**, not session-specific
- Trade history is persisted in `~/.slopesniper/trades.db`

**No changes needed** - SlopeSniper's stateless CLI model works well with cross-provider messaging.

---

## 6. Block Streaming for Long Responses

### MoltBot Streaming Config

```json
{
  "agents": {
    "defaults": {
      "blockStreamingChunk": {
        "minChars": 800,
        "maxChars": 1200
      }
    }
  }
}
```

### SlopeSniper Implications

Long outputs (wallet, status, scan) will be chunked by MoltBot. This works but can feel disjointed.

### Recommendations

**Priority: MEDIUM**

1. **Structure output with clear sections**
   ```json
   {
     "summary": "3 tokens, $125.50 total",
     "tokens": [...],
     "details": {...}
   }
   ```

2. **Add summary-first pattern**
   - First line: actionable summary
   - Following: details (can be truncated)

---

## 7. Recommended Actions

### Immediate: Verify Before Building

**DO NOT add features until testing actual MoltBot behavior:**

1. **Test background tasks**
   ```bash
   # In MoltBot/Telegram:
   "Watch BONK until it hits $500M mcap, then sell all"
   # Does MoltBot use background:true? Does polling work?
   ```

2. **Test large outputs**
   ```bash
   # With 20+ tokens in wallet:
   "Show my wallet"
   # Does MoltBot summarize appropriately?
   ```

3. **Test daemon interaction**
   ```bash
   "Start monitoring my targets in background"
   "What's the daemon status?"
   # Does the conversation flow work?
   ```

### If Issues Found: Targeted Fixes

| Problem | Solution |
|---------|----------|
| Background watch doesn't work | Add SKILL.md guidance for daemon instead |
| Large output confuses AI | Add summary fields to JSON |
| Daemon status unclear | Improve daemon status output |

### What NOT To Do

- **Don't add `--compact` flags** - MoltBot handles formatting
- **Don't add `--limit` defaults** - User can ask for "top 3" naturally
- **Don't add `slopesniper process`** - MoltBot has this built-in
- **Don't over-engineer** - Trust MoltBot's intelligence

---

## 8. Testing Checklist

### Telegram Integration

- [ ] Buy command returns within 4096 chars
- [ ] Wallet with 10+ tokens fits in message
- [ ] Scan trending with `--limit 5` fits
- [ ] Error messages are clear and actionable

### Discord Integration

- [ ] All outputs under 2000 chars with `--compact`
- [ ] Embeds render correctly (if MoltBot uses them)
- [ ] Long operations show progress

### Background Tasks

- [ ] `daemon start` returns sessionId
- [ ] `process poll` returns current output
- [ ] `process log` returns historical output
- [ ] `process kill` terminates cleanly
- [ ] Watch mode works in background

### Script Interoperability

- [ ] JSON output is valid and parseable
- [ ] Exit codes are correct (0=success, 1=error)
- [ ] `--quiet` suppresses all non-JSON output
- [ ] Can chain commands with pipes

---

## 9. SKILL.md Verification

Current SKILL.md should document:

1. **All CLI commands** with examples
2. **Output format** (JSON)
3. **Long-running task patterns** (daemon, watch)
4. **Error handling** (JSON errors, exit codes)

**Current Status:** SKILL.md is comprehensive (355 lines) with NLP examples and CLI reference.

---

## Appendix: MoltBot Tool Patterns Reference

### exec (Background Execution)
```json
{"tool": "exec", "command": "slopesniper daemon start", "background": true}
// Returns: {"sessionId": "..."}
```

### process (Session Management)
```json
{"tool": "process", "action": "poll", "sessionId": "..."}
{"tool": "process", "action": "log", "sessionId": "...", "offset": 0, "limit": 100}
{"tool": "process", "action": "kill", "sessionId": "..."}
```

### bash (Direct Execution)
```bash
bash command:"slopesniper buy BONK 25 --quiet"
bash pty:true background:true command:"slopesniper watch BONK --target-price 0.01"
```
