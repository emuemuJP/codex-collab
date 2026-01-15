# Collaboration Best Practices

Patterns and tips for effective Code and Codex collaboration.

## General Principles

### Clear Handoffs
Always explicitly signal when transitioning control:
- State what you've completed
- Indicate what needs attention
- Provide context for next steps

❌ Bad: "Done"
✅ Good: "REVIEW: Implemented user auth in src/auth/. Tests passing. Ready for security review."

### Incremental Progress
Break work into reviewable chunks:
- Feature slices, not full features
- Logical commits
- Independent modules

❌ Bad: Implement entire e-commerce system, then request review
✅ Good: Review product catalog → Review cart → Review checkout

### Context Preservation
Include relevant information:
- File paths
- Related issues/tickets
- Assumptions made
- Alternative approaches considered

### Mutual Respect
- Codex: Provide constructive feedback, not criticism
- Claude: Be receptive to suggestions, ask for clarification
- Both: Assume good intentions

## Role-Specific Guidelines

### Code (Implementation)

#### Before Starting
1. **Understand Requirements**: Ask questions if unclear
2. **Request Guidance**: Use IMPLEMENT messages for architectural decisions
3. **Plan Approach**: Outline your implementation strategy
4. **Check Dependencies**: Ensure you have what you need

#### During Implementation
1. **Incremental Commits**: Save progress frequently
2. **Write Tests**: Test as you go, not after
3. **Document**: Add comments for complex logic
4. **Stay Focused**: Complete one thing before starting another

#### Before Review
1. **Self-Review**: Check your own code first
2. **Run Tests**: Ensure everything passes
3. **Clean Up**: Remove debug code, fix formatting
4. **Prepare Context**: Gather relevant information for reviewer

#### Example Workflow
```bash
# Start with guidance
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --agent claude --type IMPLEMENT \
  --message "Building rate limiter. Planning sliding window with Redis. Thoughts?"

# Wait for response...

# After implementation
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --agent claude --type REVIEW \
  --message "Rate limiter complete. Used sliding window with Redis. Tests at 98% coverage." \
  --context '{"files": ["src/middleware/rate_limiter.py", "tests/test_rate_limiter.py"]}'
```

### Codex (Review & Guidance)

#### Providing Guidance
1. **Be Specific**: Reference exact patterns, not vague concepts
2. **Explain Why**: Don't just say what, explain reasoning
3. **Offer Alternatives**: Present options when applicable
4. **Prioritize**: Distinguish must-fix from nice-to-have

#### Code Review
1. **Security First**: Check for vulnerabilities
2. **Readability**: Code should be clear and maintainable
3. **Performance**: Identify potential bottlenecks
4. **Testing**: Verify test coverage and quality
5. **Documentation**: Ensure adequate comments and docs

#### Review Checklist
- [ ] Security vulnerabilities?
- [ ] Error handling adequate?
- [ ] Edge cases covered?
- [ ] Tests comprehensive?
- [ ] Performance acceptable?
- [ ] Code readable and maintainable?
- [ ] Documentation sufficient?
- [ ] Follows project conventions?

#### Example Review Response
```bash
# Good review with specific feedback
python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --agent codex --type SUGGEST \
  --message "Rate limiter looks solid. Three suggestions:
1. Add exponential backoff for temporary bans (prevents rapid retries)
2. Consider distributed rate limiting if you plan to scale horizontally
3. Add Prometheus metrics for monitoring rate limit hits

The Redis sliding window implementation is correct. Line 45 could use a comment explaining the window boundary calculation."
```

## Communication Patterns

### Pattern: Pre-Implementation Planning

**Goal**: Align on approach before coding

```
Claude: IMPLEMENT - "Need to add caching layer. Considering Redis vs Memcached"
Codex: SUGGEST - "Use Redis. Reasons: 1) Persistence, 2) Data structures, 3) Pub/sub if needed later"
Claude: IMPLEMENT - "Going with Redis. Will implement LRU with TTL"
Codex: APPROVE - "Good plan. Remember to handle connection failures"
Claude: [implements with error handling]
```

### Pattern: Iterative Review

**Goal**: Refine implementation through cycles

```
Claude: REVIEW - "API endpoints implemented"
Codex: SUGGEST - "Add input validation and rate limiting"
Claude: REVIEW - "Added validation and rate limiting"
Codex: SUGGEST - "Validation looks good. Rate limiting needs per-user tracking"
Claude: REVIEW - "Added per-user rate limiting with Redis"
Codex: APPROVE - "All good. Comprehensive implementation"
```

### Pattern: Problem Solving

**Goal**: Collaborate on difficult issues

```
Claude: QUESTION - "Memory leak in worker pool. Can't identify source"
Codex: SUGGEST - "Check: 1) Event listener cleanup, 2) Circular refs, 3) Cache growth. Add memory profiling first"
Claude: IMPLEMENT - "Added memory profiler. Found cache growing unbounded"
Codex: SUGGEST - "Implement LRU with max size. Use functools.lru_cache or cachetools"
Claude: REVIEW - "Implemented LRU with cachetools. Memory stable now"
Codex: APPROVE - "Good fix. Consider adding metrics for cache hit rate"
```

### Pattern: Urgent Bug Fix

**Goal**: Quick fix with verification

```
Claude: REVIEW - "Critical bug fix: SQL injection in search endpoint. Added parameterization"
Codex: [immediate review] APPROVE - "Fix is correct. Also verify no other endpoints have this issue"
Claude: IMPLEMENT - "Audited all endpoints. Found 2 more. Fixing now"
Claude: REVIEW - "All SQL injection vulnerabilities fixed. Audit complete"
Codex: APPROVE - "Good catch. Consider adding SQL query linting to CI"
```

## tmux Tips

### Window Management
```bash
# Split panes
Ctrl+b → %   # Split vertically
Ctrl+b → "   # Split horizontally

# Navigate panes
Ctrl+b → o   # Switch to next pane
Ctrl+b → ;   # Toggle last active pane
Ctrl+b → ←↑→↓  # Navigate with arrow keys

# Resize panes
Ctrl+b → Ctrl+←→↑↓  # Resize with arrow keys
```

### Copy-Paste
```bash
# Enter copy mode
Ctrl+b → [

# Navigate and select
Space        # Start selection
Enter        # Copy selection

# Paste
Ctrl+b → ]
```

### Session Management
```bash
# Detach
Ctrl+b → d

# List sessions
tmux ls

# Attach
tmux attach-session -t session-name

# Rename session
Ctrl+b → $
```

### Useful Commands
```bash
# Synchronize panes (send command to all panes)
Ctrl+b → :set synchronize-panes on

# Show pane numbers
Ctrl+b → q

# Zoom pane (temporary full screen)
Ctrl+b → z
```

## Workflow Examples

### Example 1: New Feature Development

```
[User requests feature]

Claude: IMPLEMENT - "Building user profile page. Planning: React component + REST API + PostgreSQL"
Codex: SUGGEST - "Good. Add: 1) Avatar upload with S3, 2) Privacy settings, 3) Activity feed"

[Claude implements backend]
Claude: REVIEW - "Backend API complete: GET/PUT /api/profile"
Codex: SUGGEST - "Add PATCH for partial updates, validate image uploads server-side"

[Claude adds PATCH and validation]
Claude: REVIEW - "Added PATCH endpoint and server-side validation"
Codex: APPROVE - "Backend looks good"

[Claude implements frontend]
Claude: REVIEW - "Frontend complete: ProfilePage component with form"
Codex: SUGGEST - "Add loading states, error boundaries, and optimistic updates"

[Claude adds suggested improvements]
Claude: REVIEW - "Added loading states, error handling, optimistic updates"
Codex: APPROVE - "Complete. Consider adding e2e tests"

Claude: COMPLETE - "Feature complete with e2e tests. Ready for deployment"
```

### Example 2: Bug Investigation

```
[User reports bug: "Users getting logged out randomly"]

Claude: QUESTION - "Need to investigate auth timeout. Where should I start?"
Codex: SUGGEST - "Check: 1) Session expiry settings, 2) Token refresh logic, 3) Server logs for auth failures"

Claude: IMPLEMENT - "Checking session config and logs"
Claude: REVIEW - "Found issue: Token refresh fails when original token expires. Race condition"
Codex: SUGGEST - "Implement refresh token rotation. Refresh before expiry, not after"

Claude: REVIEW - "Implemented proactive refresh at 80% token lifetime"
Codex: APPROVE - "Good fix. Add tests for edge cases (clock skew, network delay)"

Claude: REVIEW - "Added tests for edge cases. All passing"
Codex: APPROVE - "Complete. Consider adding monitoring for auth failures"

Claude: COMPLETE - "Bug fixed with monitoring. Deployed to staging"
```

## Anti-Patterns (Avoid These)

### ❌ Vague Messages
```
Bad:  "Done. Check it."
Good: "REVIEW: OAuth2 flow implemented in src/auth/oauth.py. Tests in tests/test_oauth.py"
```

### ❌ Incomplete Reviews
```
Bad:  "Looks fine"
Good: "APPROVE: Code follows security best practices. Tests cover edge cases. Performance is acceptable."
```

### ❌ No Context
```
Bad:  "Fixed the bug"
Good: "REVIEW: Fixed SQL injection in search endpoint by using parameterized queries. Audited other endpoints."
```

### ❌ Overly Large Changes
```
Bad:  "REVIEW: Entire application rewrite"
Good: "REVIEW: Refactored authentication module. Next: authorization, then sessions"
```

### ❌ Ignoring Feedback
```
Bad:  [No response to suggestions]
Good: "REVIEW: Incorporated all feedback. Added rate limiting and improved error handling"
```

## Measuring Success

Good collaboration shows:
- **Fast feedback loops**: Quick review cycles
- **High quality**: Fewer bugs, better design
- **Clear communication**: No confusion or repeated questions
- **Continuous improvement**: Learning from each cycle
- **Mutual trust**: Confidence in each other's judgment

Track these metrics:
- Time from REVIEW to APPROVE
- Number of review cycles per feature
- Bug density before/after reviews
- Test coverage trends
- Developer satisfaction
