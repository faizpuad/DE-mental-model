# Session 3 Notes: Reliability & Business Logic

## Theoretical Concepts

### Business Requirement → Technical Design

**First Principles**
- Business needs drive technical decisions
- Translate vague requirements to concrete technical specifications
- Document decisions for future reference

**Example from PRD**
- Business: "Daily dashboard updated by T+1 day"
- Technical: Pipeline completes within 6-hour window, scheduled at 2 AM
- Business: "Metrics accuracy ≥ 99.9%"
- Technical: Add data quality checks, validation rules

### Access Patterns → Indexing Decisions

**First Principles**
- Understand how data is accessed to optimize storage
- Trade-off: Write performance vs. Read performance
- Indexes speed up reads but slow down writes

**Common Query Patterns**
From PRD:
- Filter by date range (daily, weekly, monthly)
- Group by product, category, country
- Aggregate metrics over time

**Indexing Strategy**
- Date columns: B-tree index (range queries)
- Foreign keys: B-tree index (joins)
- Aggregation columns: Consider materialized views
- Composite indexes: (date_id, product_id) for common queries

**Example:**
```sql
-- Optimize for date range queries
CREATE INDEX idx_fact_date ON fact_sales_daily(date_id);

-- Optimize for date + product queries
CREATE INDEX idx_fact_date_product ON fact_sales_daily(date_id, product_id);
```

### Functional Programming vs OOP

**First Principles**
- Stateless batch operations favor functional programming
- Immutability reduces bugs
- Pure functions are easier to test

**When to Use Each**

**Functional Programming (Use For This Pipeline)**
- Stateless transformations
- Data pipelines (extract, transform, load)
- Retry logic
- Data validation
- Benefits: Predictable, testable, immutable

**Object-Oriented Programming**
- Stateful operations
- Complex state machines
- GUI applications
- Frameworks requiring classes
- Benefits: Encapsulation, inheritance

**Example Functional ETL:**
```python
# Functional approach (preferred for batch)
def extract(path):
    return pd.read_csv(path)

def transform(rows):
    return [clean_row(r) for r in rows]

def load(rows, conn):
    return [upsert(r, conn) for r in rows]

# Pipeline
data = extract('data.csv')
cleaned = transform(data)
load(cleaned, conn)
```

### Idempotency

**First Principles**
- Idempotency means an operation can be applied multiple times without changing the result beyond the initial application
- Critical for data pipelines to handle retries and failures safely

**Definition**
- An operation f is idempotent if: f(f(x)) = f(x)
- In data pipelines: Re-running the pipeline produces the same result

**Examples in Data Engineering**
- **INSERT with ON CONFLICT**: Prevent duplicate inserts
- **UPSERT**: Update existing records or insert new ones
- **DELETE with WHERE**: Safe to re-run
- **TRUNCATE + INSERT**: Atomic replacement of data

**Implementation Strategies**
1. **Check-then-Act**: Query if record exists before insert
2. **Upsert**: Use INSERT ... ON CONFLICT UPDATE
3. **Merge**: Use MERGE statement (where available)
4. **Deduplication**: Remove duplicates after load
5. **Versioning**: Track source system version to identify changes

**Benefits**
- Safe to retry failed operations
- Enables exactly-once processing semantics
- Simplifies error handling
- Reduces manual intervention

### Checkpointing

**First Principles**
- Track progress of long-running operations
- Enable resuming from last successful point
- Avoid re-processing entire dataset

**What is a Checkpoint?**
- Marker indicating the last successfully processed record
- Typically stored in a database table
- Contains metadata like timestamp, record count, status

**Checkpoint Strategies**
1. **Record-Level**: Track individual records processed
   - Pros: Granular recovery
   - Cons: High storage overhead

2. **Batch-Level**: Track groups of records
   - Pros: Good balance
   - Cons: Must re-process failed batch

3. **File-Level**: Track entire files processed
   - Pros: Simple
   - Cons: Must re-process entire file on failure

4. **Time-Based**: Track last processed timestamp
   - Pros: Natural for streaming
   - Cons: Timezone issues, duplicates

**Implementation Considerations**
- **Atomic Updates**: Checkpoint update must be atomic with data update
- **Transaction Boundaries**: Checkpoint and data updates in same transaction
- **Recovery Logic**: Identify unprocessed records on restart
- **Checkpoint Cleanup**: Remove old checkpoints

### Retry Logic

**First Principles**
- Network and database operations can fail transiently
- Automatic retry handles temporary failures
- Prevents pipeline failures from transient issues

**Types of Failures**
1. **Transient**: Temporary issues (network blips, temporary locks)
   - Solution: Retry with backoff

2. **Permanent**: Persistent issues (invalid data, schema mismatch)
   - Solution: Fail fast, alert, manual intervention

3. **Rate Limit**: Too many requests
   - Solution: Exponential backoff

**Retry Strategies**
1. **Fixed Delay**: Wait same amount between retries
   - Simple but can overwhelm system

2. **Linear Backoff**: Increase delay linearly
   - Better for some scenarios

3. **Exponential Backoff**: Double delay each retry (recommended)
   - Best practice: 1s, 2s, 4s, 8s, 16s, 32s
   - Jitter: Add randomness to avoid thundering herd

4. **Circuit Breaker**: Stop retrying after threshold
   - Prevents cascading failures
   - Requires monitoring to reset

**Retry Implementation**
```python
# Exponential backoff with jitter
import time
import random

def retry_with_backoff(func, max_retries=5):
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait_time = (2 ** attempt) + random.random()
            time.sleep(wait_time)
```

### Structured Logging

**First Principles**
- Logs should be machine-readable for analysis and alerting
- Consistent format enables parsing and querying
- Rich context aids debugging and monitoring

**Structured vs Unstructured Logs**

**Unstructured (Traditional)**
```
INFO: Data loaded successfully
ERROR: Failed to connect to database
```
- Hard to parse
- Inconsistent format
- Limited context

**Structured (JSON)**
```json
{
  "timestamp": "2024-01-15T10:30:45Z",
  "level": "INFO",
  "message": "Data loaded successfully",
  "service": "ingestion-pipeline",
  "metadata": {
    "records_processed": 12345,
    "duration_ms": 2456,
    "source_file": "data.xlsx"
  }
}
```
- Easy to parse
- Consistent schema
- Rich context
- Queryable

**Log Levels**
- **DEBUG**: Detailed information for diagnostics
- **INFO**: General informational messages
- **WARNING**: Something unexpected but not an error
- **ERROR**: Error occurred but process continued
- **CRITICAL**: Serious error requiring immediate attention

**Best Practices**
1. **Correlation ID**: Unique ID to trace requests across services
2. **User ID**: Identify which user action caused log
3. **Duration**: Time taken for operation
4. **Status**: Success/failure status
5. **Error Details**: Stack traces, error codes
6. **Business Context**: Records affected, business metrics

**Structured Logging in Python**
```python
import logging
import json
from datetime import datetime

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        return json.dumps(log_obj)

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logger.addHandler(handler)
```

## Implementation Considerations

### Transaction Management
- Use database transactions for atomic operations
- Commit only after all operations succeed
- Rollback on failure
- Set appropriate isolation levels

### Error Handling
- Catch specific exceptions, not generic Exception
- Log full error context
- Alert on critical failures
- Preserve error details for debugging

### Monitoring
- Track success/failure rates
- Monitor processing time
- Alert on anomalies
- Track retry counts

### Testing Reliability
- Simulate failures in tests
- Test retry logic
- Verify idempotency
- Test checkpoint recovery
- Validate error logging

### Production Considerations
- Graceful shutdown: Handle SIGTERM/SIGINT
- Resource limits: Set timeouts, memory limits
- Connection pooling: Reuse database connections
- Dead letter queue: Handle unprocessable records
- Data validation: Verify data quality before commit

---

## Git Collaboration Theory

### Version Control Fundamentals

**First Principles**
- Track changes to code over time
- Enable collaboration without overwriting each other's work
- Provide history and ability to revert changes
- Support parallel development through branching

**Git's Three States**
1. **Working Directory**: Files you see and edit
2. **Staging Area (Index)**: Files prepared to commit
3. **Repository (HEAD)**: Committed snapshots

**Git Commands by State**
```
Working Directory → Staging: git add
Staging → Repository: git commit
Repository → Working Directory: git checkout/reset
```

### Distributed Version Control (DVC)

**Centralized vs Distributed**

**Centralized (SVN, CVS)**
- Single central server stores all history
- Check out working copy, commit back to server
- Server is single point of failure
- Network required for most operations

**Distributed (Git, Mercurial)**
- Every developer has full repository copy
- Clone includes entire history
- Work offline, synchronize later
- No single point of failure
- Faster operations (local)

**Git Workflow Diagram**
```
Working Dir    Staging    Local Repo     Remote Repo
    |              |            |               |
    | git add      |            |               |
    +------------->|            |               |
    |              | git commit |               |
    |              +----------->|               |
    |              |            | git push      |
    |              |            +-------------->|
    |              |            | git pull      |
    |              |            |<--------------+
    |              |            | git checkout  |
    |<-------------|------------+               |
```

### Branching Theory

**Git Branching Model**

Git branches are lightweight pointers to commits. Creating a branch creates a new pointer - no copying of files.

```
Commit Graph:
            A---B---C  (main)
                 \
                  D---E  (feature)
```

**HEAD Pointer**
- HEAD points to current branch
- HEAD ~ moves back in history
- HEAD ^ moves to parent commit

**Branch Types**

1. **Persistent Branches**: main, master, develop
   - Long-lived, rarely deleted
   - Main integration points

2. **Feature Branches**: feature/feature-name
   - Short-lived (1-3 days)
   - Isolated development
   - Merged via Pull Request

3. **Release Branches**: release/v1.0.0
   - Prepare for production release
   - Bug fixes only
   - Merged to main and develop

4. **Hotfix Branches**: hotfix/v1.0.1
   - Emergency production fixes
   - Created from main
   - Merged to main and develop

### Branching Strategies

**GitHub Flow (Simple)**

```
main (production-ready)
  |
  +--- feature/auth (work in progress)
  |
  +--- feature/payments (work in progress)
```

**Process:**
1. Create branch from main
2. Commit changes
3. Open Pull Request
4. Review and discuss
5. Merge to main
6. Deploy to production

**Pros:**
- Simple, easy to understand
- Continuous deployment
- Single main branch

**Cons:**
- Requires good automated testing
- Requires feature flags for incomplete features
- Not ideal for complex release cycles

**Use for:**
- Small to medium teams (1-20 developers)
- SaaS/web applications
- Continuous deployment environments

**Git Flow (Complex)**

```
main (production)
  |
develop (integration)
  |
  +--- feature/auth
  |
  +--- feature/payments
```

**Process:**
1. `main`: Production releases only
2. `develop`: Integration of all features
3. `feature/*`: Develop features from develop
4. `release/*`: Stabilize for release from develop
5. `hotfix/*`: Emergency fixes from main

**Release Process:**
1. `develop` → `release/v1.0.0`: Freeze features, test
2. `release/v1.0.0` → `main`: Tag release, deploy
3. `release/v1.0.0` → `develop`: Merge back bugfixes
4. Delete release branch

**Pros:**
- Structured release process
- Separate production and development
- Clear workflow for releases

**Cons:**
- Complex for small teams
- Multiple long-lived branches
- More merge operations
- Slower feedback cycle

**Use for:**
- Enterprise teams
- Scheduled releases (monthly/quarterly)
- Projects requiring version control of releases

**Trunk-Based Development (Extreme)**

```
main (all work)
  |
  +- commits from all developers
```

**Process:**
1. All development happens on main
2. Very small commits (minutes apart)
3. Continuous integration/continuous deployment
4. Feature flags for incomplete features
5. Rollback by disabling feature flags

**Pros:**
- No merge conflicts
- Fastest feedback
- Simplest model
- Always releasable

**Cons:**
- Requires mature infrastructure
- Extensive automation mandatory
- Strong engineering culture
- Complex feature management

**Use for:**
- Very large teams (20+ developers)
- Daily or hourly releases
- Companies with strong DevOps practices

### Merge vs Rebase

**Merge**

```
Main:   A---B---C---D---G (merge commit)
Feature:       \---E---F/
```

**Definition:**
- Creates new merge commit with two parents
- Preserves true history of development
- Shows branching and merging points

**When to Use:**
- Merging feature branches into main
- Public/shared branches
- Want to preserve branch history
- Team prefers merge commits

**Command:**
```bash
git checkout main
git merge feature-branch
git merge --no-ff feature-branch  # Always create merge commit
```

**Rebase**

```
Original:
Main:   A---B---C
Feature:       \---D---E

After Rebase:
Main:   A---B---C---D'---E'
```

**Definition:**
- Moves branch to new base
- Creates new commits (replays work)
- Rewrites commit history
- Produces linear history

**When to Use:**
- Updating feature branch with latest main
- Local/feature branches (not pushed yet)
- Want linear, cleaner history
- Before opening Pull Request

**Command:**
```bash
git checkout feature-branch
git rebase main
```

**Rebase Dangers:**
- Rewrites history (commits get new hashes)
- Breaks other developers' work if branch is shared
- Can lose commits if not careful
- **Never rebase public/shared branches**

**Interactive Rebase**
```bash
git rebase -i HEAD~5
# Commands: pick, reword, edit, squash, fixup, drop, exec
```

**Best Practice:**
- Rebase local feature branches frequently
- Merge feature branches to main (don't rebase main)
- Never rebase commits that others have based work on
- Use `--force-with-lease` instead of `--force`

### Conflict Resolution

**Types of Conflicts**

1. **Content Conflicts**: Both branches modify same lines
   - Git shows `<<<<<<< HEAD`, `=======`, `>>>>>>> branch-name` markers
   - Manual resolution required

2. **Rename Conflicts**: File renamed in both branches
   - Git can detect and handle sometimes
   - Manual intervention may be needed

3. **Structural Conflicts**: File added in one, deleted in other
   - Git can't automatically resolve
   - Decision: keep, delete, or manually merge

**Conflict Resolution Process**

```bash
# 1. Detect conflicts
git merge feature-branch
# CONFLICT: README.md

# 2. Identify conflicts
git status

# 3. Open and resolve
# Edit files, remove conflict markers

# 4. Mark as resolved
git add resolved-file.txt

# 5. Complete merge
git commit
# Git auto-generates commit message
```

**Strategies for Avoiding Conflicts**

1. **Small, frequent commits**: Reduce overlap
2. **Update frequently**: Rebase often
3. **Coordinate with team**: Know what others are working on
4. **Separate concerns**: Different features in different files
5. **Clear code ownership**: Know who owns which modules

### Git Stash Theory

**Purpose: Temporary Save**

Stash provides a mechanism to save work-in-progress without committing:
- Switch context (emergency bug fix)
- Experiment with different approaches
- Clean working directory before pull/rebase
- Draft work not ready for commit

**Stash Implementation**

Stash uses two commits:
1. Staged files (tracked)
2. Untracked files (with `-u` flag)

Stored in `.git/refs/stash` reflog.

**Stash vs Commit**

| Aspect | Stash | Commit |
|--------|-------|--------|
| Purpose | Temporary work | Completed work |
| History | Not part of history | Part of git log |
| Sharing | Local only | Pushable to remote |
| Lifespan | Hours/days | Permanent |
| Message | Optional | Required |

**Stash Stack**

Stash is a LIFO (Last In First Out) stack:
```
stash@{0}: Newest
stash@{1}: Previous
stash@{2}: Older
```

**Stash Operations**
- `git stash`: Push to stack
- `git stash pop`: Remove from stack and apply
- `git stash apply`: Apply without removing
- `git stash drop`: Remove from stack

**Best Practices**
- Use descriptive messages
- Don't keep stashes for weeks (commit instead)
- Clean up old stashes regularly
- Remember stash is local-only

### Remote Operations

**Remote Tracking Branches**

```
Local Branch    Remote Tracking Branch    Remote Branch
feature/user    origin/feature/user      feature/user
     |                    |                     |
     | push/pull          |                     |
     +--------------------+---------------------+
```

**Remote Branch Relationships**

- **Tracking**: Local branch follows remote branch
- **Upstream**: Remote branch that local branch follows
- **Origin**: Default name for primary remote

**Push Operations**

```bash
# Simple push
git push origin main

# Set upstream (tracking)
git push -u origin feature-branch

# Force push (dangerous)
git push --force origin feature-branch

# Safe force push
git push --force-with-lease origin feature-branch
```

**Fetch vs Pull**

```bash
# Fetch: Update remote tracking branches only
git fetch origin

# Pull: Fetch + merge/rebase
git pull origin main

# Pull with rebase (recommended)
git pull --rebase origin main
```

**Remote Best Practices**

1. **Always fetch before pulling**: Know what you're getting
2. **Use pull --rebase**: Keep history linear
3. **Protect main branch**: No direct pushes
4. **Use force-with-lease**: Safer than force
5. **Pull frequently**: Minimize merge conflicts

### Collaborative Workflows

**Pull Request (PR) Workflow**

1. **Developer A** creates feature branch
2. **Developer A** commits and pushes branch
3. **Developer A** opens PR on GitHub/GitLab
4. **Team reviews PR**: Comments, suggestions, requests changes
5. **Developer A** updates PR with new commits
6. **Maintainer approves and merges PR**
7. **Branch deleted** after merge

**Code Review Benefits**
- Knowledge sharing
- Catch bugs early
- Enforce coding standards
- Documentation
- Team cohesion

**Fork Workflow**

Used when contributing to open-source projects:

1. Fork repository to your account
2. Clone your fork
3. Create feature branch
4. Commit and push to your fork
5. Open PR from your fork to original repo
6. Respond to feedback
7. PR merged by maintainer

**Upstream Remote**

```bash
# Add original repository as upstream
git remote add upstream https://github.com/original/repo.git

# Fetch from upstream
git fetch upstream

# Merge upstream changes to your fork
git checkout main
git merge upstream/main
git push origin main
```

### Git Configuration

**User Identity**
```bash
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

**Default Branch**
```bash
git config --global init.defaultBranch main
```

**Line Endings**
```bash
# Mac/Linux
git config --global core.autocrlf input

# Windows
git config --global core.autocrlf true
```

**Aliases**
```bash
git config --global alias.st status
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
```

**SSH vs HTTPS**

**SSH Keys:**
- No password required
- More secure
- Setup required once
- Recommended for frequent use

**HTTPS:**
- Password/token every push
- Easy setup
- Good for occasional use

### Branch Protection

**GitHub Branch Protection**

Protect main/master branch:
- Require pull request reviews
- Require status checks (CI/CD)
- Require branches up to date before merging
- Restrict who can push
- Block force pushes
- Require linear history

**Benefits:**
- Prevents accidental commits
- Ensures code review
- Requires passing tests
- Maintains history integrity

### Git Anti-Patterns

**Don't Do This:**

1. **Commit directly to main**: Always use feature branches
2. **Large, monolithic commits**: One logical change per commit
3. **Commit secrets**: Use environment variables
4. **Amend pushed commits**: Rewrites public history
5. **Rebase shared branches**: Breaks other developers' work
6. **Ignore merge conflicts**: Resolve properly
7. **Keep stale branches**: Delete after merge
8. **Poor commit messages**: Describe what and why
9. **Commit untested code**: Test before pushing
10. **Push broken builds**: Ensure CI/CD passes

### Git Best Practices

**Commit Message Format**

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:** feat, fix, docs, style, refactor, test, chore

**Example:**
```
feat(auth): add JWT token authentication

Implement JWT-based authentication with:
- Login endpoint
- Token validation middleware
- Refresh token support

Closes #123
```

**Atomic Commits**
- One logical change per commit
- Don't mix unrelated changes
- Keep commits focused
- Easier to review and revert

**Frequent Integration**
- Pull/rebase frequently (at least daily)
- Minimize conflicts
- Get fast feedback
- Stay up to date

**Clear History**
- Use meaningful commit messages
- Keep history linear when possible
- Squash fix-up commits
- Document important decisions

### Summary

Git collaboration requires understanding:
- **Fundamentals**: Working directory, staging, repository
- **Branching**: Feature branches, integration strategies
- **Merge vs Rebase**: When to use each approach
- **Conflict Resolution**: Handle merge conflicts gracefully
- **Remote Operations**: Work with GitHub/GitLab effectively
- **Best Practices**: Commit often, review thoroughly, communicate

Key principles:
- Use feature branches
- Review all code
- Commit frequently with clear messages
- Keep branches short-lived
- Resolve conflicts quickly
- Protect main branch
- Pull frequently
