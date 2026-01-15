---
name: codex-collab
description: Collaborative development using tmux with dual perspectives - implementation and review/guidance (Codex). Use when user requests collaboration, code review, or architectural guidance. Requires tmux. Creates two-pane session where left handles implementation and right (Codex) provides review/guidance. Both communicate via message files. If Codex doesn't respond within 60 seconds, automatically falls back to simple mode simulating both roles.
allowed-tools:
  - Read
  - Bash(python ~/.claude/skills/codex-collab/scripts/session_manager.py:*)
  - Bash(python3:*)
  - Bash(find:*)
  - Bash(which:*)
  - Bash(tmux:*)
---

# Codex Collaborative Development

Real parallel collaboration using tmux with automatic fallback.

## IMPORTANT: DO NOT USE MCP/Codex Plugin

**This skill uses tmux for collaboration. DO NOT call Codex via MCP or any plugin.**

- The right pane runs `codex` CLI separately in tmux
- Claude (left pane) communicates via `collab_communicate.py` scripts only
- NEVER use MCPSearch or any Codex MCP tool during this collaboration
- All communication happens through `/tmp/codex_collab/messages.json`

## Default: tmux Mode

When user requests collaboration, **always start with tmux mode** for true parallel development.

### Quick Start

User says:
```
"Codex collaboration, work together on user authentication"
```

Claude immediately:
1. Checks tmux installation
2. Initializes tmux session
3. Sets up communication infrastructure
4. Guides user through the workflow

### Prerequisites Check

Before starting, verify tmux is installed:

```bash
which tmux
```

If not installed, guide user to install:
- **macOS**: `brew install tmux`
- **Linux**: `sudo apt-get install tmux`

## Workflow

### Step 1: Auto-Initialize Session

When user requests collaboration, Claude runs:

```bash
python3 ~/.claude/skills/codex-collab/scripts/session_manager.py --init --session-name [project-name]
```

This creates:
- Two-pane tmux session
- Communication directory at `/tmp/codex_collab/`
- Message queue system

**IMPORTANT: After initialization, ALWAYS verify session was created correctly:**

```bash
tmux has-session -t [project-name] && echo "Session exists" || echo "Session NOT created"
tmux list-panes -t [project-name]
```

If session creation fails or panes are missing, inform user and troubleshoot.

**If session already exists:**
1. First verify it has 2 panes: `tmux list-panes -t [project-name]`
2. If valid, guide user to attach: `tmux switch-client -t [project-name]` (from within tmux) or `tmux attach-session -t [project-name]` (from outside tmux)
3. If user wants fresh session, end existing one first: `python3 ~/.claude/skills/codex-collab/scripts/session_manager.py --end --session-name [project-name]`

### Step 2: Guide User

Inform user:
```
✓ tmux session created: [project-name]

Left pane (Code): Implementation workspace
Right pane (Codex): Review & guidance workspace

Next steps:
1. Open left pane: This conversation continues as Code
2. Open right pane: Start new Claude conversation for Codex role
3. Both sides communicate via message scripts

To attach to session:
tmux attach-session -t [project-name]
```

### Step 3: Communication Protocol

**This conversation (Code)** sends messages:
```bash
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --agent claude --type IMPLEMENT \
  --message "Planning JWT auth. Architecture advice?"
```

**User opens Codex pane** and runs:
```bash
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --agent codex --action read
```

Codex responds:
```bash
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --agent codex --type SUGGEST \
  --message "Use PyJWT with RS256. Key points: ..."
```

**Code reads response**:
```bash
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --agent claude --action read
```

### Step 4: Timeout Handling

After sending a message, Code waits for Codex response.

**If no response within 60 seconds**, automatically switch to simple mode:

```
⚠️ Codex hasn't responded within 60 seconds.
Switching to simple mode - I'll simulate both roles.

[Codex Mode 🔍]
Architectural guidance: ...

[Code Mode 🔧]  
Implementing based on guidance...
```

This ensures development continues even if:
- User hasn't opened Codex pane yet
- Codex is busy with another task
- Communication issues occur

### Step 5: Returning to tmux Mode

If later Codex becomes available, inform user:
```
💡 Tip: Codex is now available in the tmux session.
   You can switch back to full tmux collaboration mode:
   
   tmux attach-session -t [project-name]
```

## Example: Full tmux Workflow

```
User: "Build JWT authentication with Codex collaboration"

Code (this conversation):
✓ Initializing tmux session...
✓ Session created: jwt-auth-dev

Please open two terminal windows:

Window 1 (Code - this conversation continues here):
$ tmux attach-session -t jwt-auth-dev
$ # Select left pane (Ctrl+b, then arrow left)

Window 2 (Codex - start new Claude conversation):
$ tmux attach-session -t jwt-auth-dev  
$ # Select right pane (Ctrl+b, then arrow right)
$ python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --agent codex --action read

---

[Code sends first message]
$ python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --agent claude --type IMPLEMENT \
  --message "Planning JWT auth implementation. Architecture advice?"

Waiting for Codex response... (timeout: 60s)

[If Codex responds within 60s]
✓ Codex responded!

$ python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --agent claude --action read

Response from Codex:
"Use PyJWT with RS256 signing. Key recommendations:
1. Access token: 15min expiry
2. Refresh token: 7 day expiry with rotation
3. Store refresh tokens with user association
4. Add rate limiting to token endpoints"

Implementing based on Codex's guidance...
[Creates files: src/auth/jwt_handler.py, ...]

---

[If Codex doesn't respond within 60s]
⚠️ No response from Codex within 60 seconds.
Switching to simple mode - I'll simulate both roles.

[Codex Mode 🔍]
For JWT authentication, I recommend:
- Use PyJWT with RS256 signing
- Access token: 15min expiry
- Refresh token rotation pattern

[Code Mode 🔧]
Implementing based on architectural guidance...
[Creates files...]

💡 Tip: Codex can join anytime. When ready:
   tmux attach-session -t jwt-auth-dev
```

## Simple Mode (Fallback Only)

Simple mode activates **only when**:
- Codex doesn't respond within 60 seconds
- User explicitly requests "use simple mode"
- tmux is not installed and user cannot install it

In simple mode, Claude simulates both roles:

**🔧 Code Mode** (Implementation)
- Writes code and implements features
- Asks for architectural guidance
- Responds to code review feedback

**🔍 Codex Mode** (Review & Guidance)  
- Provides architectural recommendations
- Reviews code for quality, security, best practices
- Suggests improvements and alternatives

### Simple Mode Example

```
⚠️ Codex hasn't responded. Using simple mode.

[Codex Mode 🔍]
For user registration API, consider:
- Email validation and uniqueness
- Password strength (8+ chars, mixed case)
- Rate limiting (prevent spam)
- Status codes (201, 400, 409)

[Code Mode 🔧]
[Implements endpoint with validations]

[Codex Mode 🔍]
Implementation looks good. Add email verification workflow.

[Code Mode 🔧]
[Adds email verification]
✓ Complete
```

## When Simple Mode is Appropriate

Use simple mode only when:
- **Quick prototyping**: Need fast iteration, tmux overhead not worth it
- **Teaching/Demo**: Showing collaboration concept
- **No tmux access**: Cloud environment without tmux
- **Emergency fallback**: Codex unavailable

For production development, **always prefer tmux mode** for true parallel collaboration.

---

# tmux Mode Details

The default operational mode for professional collaboration.

## Architecture

```
┌─────────────────────────┬─────────────────────────┐
│ Code (Left)      │ Codex (Right)           │
│ ─────────────────────── │ ─────────────────────── │
│ Role: Implementation    │ Role: Review & Guidance │
│ Agent ID: claude        │ Agent ID: codex         │
│                         │                         │
│ Writes code             │ Reviews code            │
│ Requests guidance       │ Provides guidance       │
│ Implements feedback     │ Suggests improvements   │
└─────────────────────────┴─────────────────────────┘
                    ▼
        /tmp/codex_collab/
        ├── messages.json (active queue)
        ├── history.json (full log)
        └── sessions.json (metadata)
```

## Installation & Setup

### Prerequisites

```bash
# macOS
brew install tmux

# Linux
sudo apt-get install tmux
```

## Setup

### Step 1: Initialize Session

```bash
python3 ~/.claude/skills/codex-collab/scripts/session_manager.py --init --session-name my-project
```

This creates:
- tmux session with 2 panes (Code | Codex)
- Communication infrastructure at `/tmp/codex_collab/`
- Message queue system

### Step 2: Attach to Session

```bash
tmux attach-session -t my-project
```

You'll see:
```
┌─────────────────────┬─────────────────────┐
│ Code         │ Codex               │
│ (Implementation)    │ (Review & Guidance) │
│                     │                     │
└─────────────────────┴─────────────────────┘
```

### Step 3: Communication

**Left pane (Code)** sends implementation requests:
```bash
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --agent claude --type IMPLEMENT \
  --message "Planning JWT auth with RS256. Should I use PyJWT or authlib?"
```

**Right pane (Codex)** reads and responds:
```bash
# Read messages
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --agent codex --action read

# Respond
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --agent codex --type SUGGEST \
  --message "Use PyJWT. Key points: 1) RS256 signing, 2) Short token expiry, 3) Refresh rotation"
```

**Code** reads response:
```bash
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --agent claude --action read
```

## Message Types

- **IMPLEMENT**: Request guidance before starting
- **REVIEW**: Request code review  
- **SUGGEST**: Provide feedback/alternatives
- **APPROVE**: Approve implementation
- **QUESTION**: Ask for clarification
- **COMPLETE**: Signal task completion

## Development Workflow

### Full Collaboration Cycle

```bash
# 1. Code: Request guidance
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --agent claude --type IMPLEMENT \
  --message "Building user profile API. Architecture advice?" \
  --context '{"files": ["src/api/"], "priority": "high"}'

# 2. Codex: Provide guidance
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --agent codex --type SUGGEST \
  --message "Use: 1) REST endpoints, 2) JWT auth, 3) Input validation, 4) Rate limiting"

# 3. Code: Implement
[Write code in src/api/profile.py]

# 4. Code: Request review
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --agent claude --type REVIEW \
  --message "Profile API complete: GET/POST/PATCH /api/profile" \
  --context '{"files": ["src/api/profile.py", "tests/test_profile.py"]}'

# 5. Codex: Review and suggest
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --agent codex --type SUGGEST \
  --message "Add: 1) Avatar upload, 2) Privacy settings, 3) CORS headers"

# 6. Code: Incorporate feedback
[Update code]

# 7. Code: Request re-review
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --agent claude --type REVIEW \
  --message "Added all suggestions. Ready for approval."

# 8. Codex: Approve
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --agent codex --type APPROVE \
  --message "Looks good. All best practices followed."

# 9. Code: Complete
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --agent claude --type COMPLETE \
  --message "Feature complete and deployed."
```

## Session Management

### View Message History
```bash
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --action history --limit 10
```

### Clear Active Messages
```bash
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --action clear
```

### Save Session State
```bash
python3 ~/.claude/skills/codex-collab/scripts/session_manager.py --save --session-name my-project
```

### List All Sessions
```bash
python3 ~/.claude/skills/codex-collab/scripts/session_manager.py --list
```

### End Session
```bash
python3 ~/.claude/skills/codex-collab/scripts/session_manager.py --end --session-name my-project
```

## tmux Navigation

### Switching Panes
- `Ctrl+b` then `o` - Switch to other pane
- `Ctrl+b` then `←` or `→` - Navigate with arrows

### Detach/Attach
- `Ctrl+b` then `d` - Detach (session keeps running)
- `tmux attach-session -t my-project` - Reattach

### Copy/Paste
- `Ctrl+b` then `[` - Enter copy mode
- `Space` - Start selection
- `Enter` - Copy selection
- `Ctrl+b` then `]` - Paste

### Split Management
- `Ctrl+b` then `%` - Split vertically
- `Ctrl+b` then `"` - Split horizontally
- `Ctrl+b` then `x` - Close pane

## Advanced: Custom Workflow Script

Create a helper script for common operations:

```bash
#!/bin/bash
# collab.sh - Quick collaboration commands

case "$1" in
  start)
    python3 ~/.claude/skills/codex-collab/scripts/session_manager.py --init --session-name ${2:-dev}
    tmux attach-session -t ${2:-dev}
    ;;
  
  impl)
    python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --agent claude --type IMPLEMENT --message "$2"
    ;;
  
  review)
    python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --agent claude --type REVIEW --message "$2"
    ;;
  
  suggest)
    python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --agent codex --type SUGGEST --message "$2"
    ;;
  
  approve)
    python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --agent codex --type APPROVE --message "$2"
    ;;
  
  read)
    python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --agent ${2:-claude} --action read
    ;;
  
  history)
    python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --action history --limit ${2:-20}
    ;;
  
  *)
    echo "Usage: collab.sh {start|impl|review|suggest|approve|read|history} [args]"
    ;;
esac
```

Usage:
```bash
chmod +x collab.sh
./collab.sh start my-project
./collab.sh impl "Building auth system"
./collab.sh read codex
./collab.sh suggest "Use bcrypt for passwords"
```

## Example: Real tmux Session

**Terminal Setup:**
```bash
# Initialize and attach
python3 ~/.claude/skills/codex-collab/scripts/session_manager.py --init --session-name auth-feature
tmux attach-session -t auth-feature
```

**Left Pane (Code):**
```bash
# Request architectural guidance
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --agent claude --type IMPLEMENT \
  --message "Need to build OAuth2 authorization server. Architecture recommendations?"

# Wait for Codex response...

# Read Codex's guidance
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --agent claude --action read

# Implement based on guidance
vim src/auth/oauth_server.py
# ... write code ...

# Request review
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --agent claude --type REVIEW \
  --message "OAuth2 server implemented: authorization endpoint, token endpoint, PKCE support" \
  --context '{"files": ["src/auth/oauth_server.py", "tests/test_oauth.py"]}'
```

**Right Pane (Codex):**
```bash
# Read Code's request
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --agent codex --action read

# Provide architectural guidance
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --agent codex --type SUGGEST \
  --message "OAuth2 server architecture:
1. Use authlib library (battle-tested)
2. Implement PKCE for all clients
3. Store tokens with user association
4. Add rate limiting (10 req/min per IP)
5. Validate redirect URIs strictly"

# Wait for implementation...

# Read review request
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --agent codex --action read

# Review the implementation
cat src/auth/oauth_server.py
cat tests/test_oauth.py

# Provide review feedback
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --agent codex --type SUGGEST \
  --message "Implementation looks solid. Two additions:
1. Add token revocation endpoint (RFC 7009)
2. Implement refresh token rotation
Also: Line 87 needs better error message for invalid_grant"

# After Code updates...
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --agent codex --action read

# Final approval
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --agent codex --type APPROVE \
  --message "All issues addressed. OAuth2 implementation is production-ready."
```

## Benefits of tmux Mode

1. **True Parallelism**: Independent processes, real async work
2. **Context Separation**: Each pane maintains its own focus
3. **Persistent Sessions**: Detach/reattach without losing state
4. **Visual Clarity**: See both perspectives simultaneously
5. **Message History**: Full audit trail of decisions
6. **Scalable**: Can add more panes for different roles

## When to Use tmux Mode

Use tmux mode for:
- **Long-running projects**: Sessions persist across days
- **Complex features**: Need sustained back-and-forth
- **Team collaboration**: Multiple developers can attach
- **Detailed review**: Codex needs time for thorough analysis
- **Learning**: See full communication protocol in action

Use simple mode for:
- **Quick tasks**: One-off features or fixes
- **Prototyping**: Fast iteration
- **No tmux access**: Cloud environments, restrictions
- **Solo work**: Single developer, simpler setup

## Troubleshooting

**Issue**: `command not found: tmux`
```bash
# macOS
brew install tmux

# Ubuntu/Debian
sudo apt-get install tmux

# Check installation
tmux -V
```

**Issue**: Messages not appearing
```bash
# Check communication directory
ls -la /tmp/codex_collab/

# View raw messages
cat /tmp/codex_collab/messages.json

# Reinitialize
python3 ~/.claude/skills/codex-collab/scripts/session_manager.py --init --session-name test
```

**Issue**: Session not found
```bash
# List all sessions
tmux ls

# Create new session
python3 ~/.claude/skills/codex-collab/scripts/session_manager.py --init --session-name new-session
```

**Issue**: Can't switch panes
- Make sure you press `Ctrl+b` first, then release, then press `o`
- Not `Ctrl+b+o` simultaneously

## References

For detailed protocol and patterns, see:
- `references/communication_protocol.md` - Complete message specification
- `references/best_practices.md` - Collaboration patterns and tips
