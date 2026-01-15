# Communication Protocol

Detailed specification for inter-agent communication between Code and Codex.

## Message Types

### IMPLEMENT
Request implementation guidance before starting work.

**When to use:**
- Starting a new feature or module
- Need architectural advice before coding
- Clarifying approach before implementation

**Example:**
```bash
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py \
  --agent claude --type IMPLEMENT \
  --message "Planning to implement OAuth2 flow. Should I use authlib or create custom?" \
  --notify
```

### REVIEW
Request code review after implementation.

**When to use:**
- Completed a feature or module
- Made significant changes
- Ready for quality check

**Context should include:**
- File paths that were modified
- Summary of changes
- Any concerns or questions

**Example:**
```bash
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --agent claude --type REVIEW \
  --message "Completed OAuth2 implementation. Ready for security review." \
  --context '{"files": ["src/auth/oauth.py", "tests/test_oauth.py"], "status": "ready"}'
```

### SUGGEST
Provide suggestions, alternatives, or improvements.

**When to use:**
- Responding to IMPLEMENT requests
- Providing feedback on REVIEW requests
- Offering improvements or optimizations

**Example:**
```bash
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --agent codex --type SUGGEST \
  --message "For OAuth2, use authlib. It's battle-tested and handles edge cases. Consider: 1) PKCE for mobile clients, 2) Token refresh strategy, 3) State parameter validation"
```

### APPROVE
Approve implementation after review.

**When to use:**
- Code meets quality standards
- No blocking issues found
- Ready to proceed or merge

**Example:**
```bash
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --agent codex --type APPROVE \
  --message "OAuth implementation looks solid. Security patterns are correct, tests cover edge cases."
```

### QUESTION
Ask for clarification or additional information.

**When to use:**
- Requirements are unclear
- Need more context
- Ambiguous specifications

**Example:**
```bash
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --agent claude --type QUESTION \
  --message "Should the OAuth flow support both authorization code and implicit grant types, or just authorization code?"
```

### COMPLETE
Signal that a task is fully complete.

**When to use:**
- All review feedback incorporated
- Tests passing
- Documentation updated
- Ready for deployment or next task

**Example:**
```bash
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --agent claude --type COMPLETE \
  --message "OAuth2 implementation complete with all feedback incorporated. Tests passing, docs updated."
```

## Message Structure

### Required Fields
- `timestamp`: ISO 8601 datetime (auto-generated)
- `agent`: "claude" or "codex"
- `type`: One of the message types above
- `message`: Human-readable message content

### Optional Fields
- `context`: JSON object with additional information
  - `files`: Array of file paths
  - `status`: Current status indicator
  - `priority`: Message priority
  - `related_to`: Reference to previous message
  - Custom fields as needed

### Example Full Message
```json
{
  "timestamp": "2025-01-15T12:34:56.789Z",
  "agent": "claude",
  "type": "REVIEW",
  "message": "Completed user authentication system with JWT tokens",
  "context": {
    "files": [
      "src/auth/jwt_handler.py",
      "src/auth/middleware.py",
      "tests/test_auth.py"
    ],
    "status": "ready_for_review",
    "priority": "high",
    "test_coverage": "95%",
    "related_to": "IMPLEMENT request from 12:15:00"
  }
}
```

## Communication Patterns

### Pattern 1: Guided Implementation
```
1. Claude: IMPLEMENT - "Need to build X feature"
2. Codex: SUGGEST - "Use approach Y, consider Z"
3. Claude: [implements]
4. Claude: REVIEW - "Implementation complete"
5. Codex: APPROVE - "Looks good"
```

### Pattern 2: Iterative Refinement
```
1. Claude: REVIEW - "Initial implementation complete"
2. Codex: SUGGEST - "Add error handling for case X"
3. Claude: REVIEW - "Added error handling"
4. Codex: SUGGEST - "Also add logging"
5. Claude: REVIEW - "Added logging"
6. Codex: APPROVE - "All good now"
```

### Pattern 3: Clarification Flow
```
1. Claude: IMPLEMENT - "Building feature X"
2. Codex: QUESTION - "Should it handle Y scenario?"
3. Claude: QUESTION - "User, should we handle Y?"
4. User: "Yes, handle Y"
5. Claude: IMPLEMENT - "Will handle Y"
6. Codex: SUGGEST - "Use pattern Z for Y"
7. Claude: [implements with pattern Z]
```

### Pattern 4: Quick Approval
```
1. Claude: REVIEW - "Simple bug fix in module X"
2. Codex: APPROVE - "Fix is correct"
```

## Best Practices

### For Code

1. **Be Specific**: Include file paths and clear descriptions
2. **Small Batches**: Request review for logical chunks, not entire features
3. **Context Matters**: Provide relevant context in the context field
4. **Clear Status**: Indicate when work is truly ready for review
5. **Acknowledge Feedback**: Respond to suggestions before re-submitting

### For Codex

1. **Constructive**: Focus on improvements, not just problems
2. **Specific**: Point to exact issues with line numbers when possible
3. **Actionable**: Provide clear guidance on how to address issues
4. **Prioritized**: Distinguish between critical issues and nice-to-haves
5. **Timely**: Respond promptly to maintain development flow

## Reading Messages

### Basic Read
```bash
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --agent codex --action read
```

### Read All Messages (including own)
```bash
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --agent codex --action read --all
```

### Read Limited Messages
```bash
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --agent codex --action read --limit 5
```

### View History
```bash
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --action history --limit 20
```

### Clear Current Messages
```bash
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --action clear
```

## Error Handling

If communication fails:

1. **Check directory exists**: `/tmp/codex_collab/`
2. **Check file permissions**: Messages file should be readable/writable
3. **Reinitialize**: Run `python3 ~/.claude/skills/codex-collab/scripts/session_manager.py --init` to recreate structure
4. **View raw messages**: `cat /tmp/codex_collab/messages.json`

## New Options (v2)

### Auto-notification (--notify)

Automatically send a notification to the other agent's pane after sending a message:

```bash
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py \
  --agent claude --type REVIEW \
  --message "Ready for review" \
  --notify
```

### Response waiting (--wait)

Wait for response from the other agent after sending a message:

```bash
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py \
  --agent claude --type IMPLEMENT \
  --message "Need guidance" \
  --wait --timeout 90
```

### Combining options

Send message with notification and wait for response:

```bash
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py \
  --agent claude --type IMPLEMENT \
  --message "Need architectural guidance" \
  --notify --wait --timeout 60
```

## Tips

- Use `--all` flag sparingly; usually you only want to read others' messages
- Clear messages periodically to keep the active queue manageable
- Use history to review past decisions and patterns
- Include context liberally; it's better to over-communicate than under-communicate
- Establish message frequency expectations to maintain development rhythm
- Use `--notify` to reduce manual notification overhead
- Use `--wait` for synchronous workflows requiring immediate response
