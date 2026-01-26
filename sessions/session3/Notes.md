# Session 3 Notes: Git Collaboration & Version Control

## Primary Focus: Git Version Control

### Git Fundamentals

#### What is Git?
- **Distributed Version Control System (DVCS)**
- Tracks changes in source code during software development
- Enables collaboration among multiple developers
- Provides complete history of project changes

#### Core Git Concepts

**Repository (Repo)**
- Database containing project files and their complete history
- Every clone contains full repository history
- Can work offline and sync later

**Working Directory**
- Current state of files on your filesystem
- Where you make changes to files

**Staging Area (Index)**
- Preparation area for next commit
- Select what changes to include in commit
- Provides granular control over commits

**Commit**
- Snapshot of project at specific point in time
- Has unique SHA-1 hash identifier
- Contains author, timestamp, and message

**Branch**
- Pointer to specific commit
- Enables parallel development
- Default branch: `main` (historically `master`)

### Essential Git Commands

#### Repository Setup
```bash
# Initialize new repository
git init

# Clone existing repository
git clone <url>

# Configure user information
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

#### Basic Workflow
```bash
# Check status
git status

# Add files to staging area
git add filename.txt
git add .                    # Add all files
git add -A                   # Add all including deletions

# Commit changes
git commit -m "Descriptive message"

# Push to remote
git push origin main

# Pull changes from remote
git pull origin main
```

### Branching Strategies

#### Feature Branch Workflow
```bash
# Create new feature branch
git checkout -b feature/user-authentication

# Work on feature...
git add .
git commit -m "feat: add user authentication"

# Push feature branch
git push origin feature/user-authentication

# Merge into main (via pull request)
git checkout main
git merge feature/user-authentication
git branch -d feature/user-authentication
```

#### Git Flow Model
- **main**: Production-ready code
- **develop**: Integration branch for features
- **feature/***: New features development
- **release/***: Release preparation
- **hotfix/***: Critical production fixes

### Merge Techniques

#### Fast-Forward Merge
- Simple case: main has no new commits
- Branch pointer just moves forward
- Clean linear history

#### 3-Way Merge
- Both branches have new commits
- Creates merge commit
- Combines both histories

#### Merge Conflicts
**When conflicts occur:**
```bash
# Identify conflicted files
git status

# Resolve conflicts manually
# Edit files, remove conflict markers:
# <<<<<<< HEAD
# your changes
# =======
# their changes
# >>>>>>> branch-name

# Mark conflicts as resolved
git add .
git commit
```

### Advanced Git Features

#### Rebase
**Rewrite commit history for cleaner timeline:**
```bash
# Rebase feature onto main
git checkout feature-branch
git rebase main

# Interactive rebase (edit, squash, reorder commits)
git rebase -i HEAD~3
```

**Rebase vs Merge:**
- **Merge**: Preserves exact history, shows branch structure
- **Rebase**: Creates linear history, easier to read
- **Never rebase public/shared branches**

#### Stash
**Save work-in-progress temporarily:**
```bash
# Stash current changes
git stash
git stash save "Work on user authentication"

# List stashes
git stash list

# Apply most recent stash
git stash apply
git stash pop      # Apply and remove

# Apply specific stash
git stash apply stash@{1}

# Drop stash
git stash drop stash@{0}
git stash clear     # Remove all stashes
```

#### Cherry-pick
**Apply specific commits to current branch:**
```bash
# Apply commit from another branch
git cherry-pick <commit-hash>

# Apply without committing
git cherry-pick --no-commit <commit-hash>
```

### Remote Collaboration

#### Working with Remotes
```bash
# View remotes
git remote -v

# Add remote repository
git remote add origin https://github.com/user/repo.git

# Push to remote
git push -u origin main    # Set upstream

# Push all branches
git push --all origin

# Push tags
git push --tags
```

#### Pull Request Workflow
```bash
# 1. Fork repository (GitHub/GitLab web interface)
# 2. Clone your fork
git clone https://github.com/yourusername/repo.git

# 3. Create feature branch
git checkout -b feature/new-feature

# 4. Make changes and commit
git add .
git commit -m "feat: implement new feature"

# 5. Push to your fork
git push origin feature/new-feature

# 6. Create pull request (GitHub/GitLab web interface)
```

#### Collaboration Best Practices

**Commit Message Format:**
```
type(scope): description

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code formatting (no logic changes)
- `refactor`: Code restructuring
- `test`: Adding/modifying tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(auth): add OAuth2 integration
Fix login validation for special characters
docs(readme): update installation instructions
refactor(database): optimize query performance
```

### Git Configuration

#### User Configuration
```bash
# Global configuration (affects all repositories)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Repository-specific configuration
git config user.name "Work Name"
git config user.email "work.email@company.com"

# Set default branch name
git config --global init.defaultBranch main
```

#### Useful Aliases
```bash
# Common aliases
git config --global alias.st status
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.cm commit
git config --global alias.unstage 'reset HEAD --'
git config --global alias.last 'log -1 HEAD'
git config --global alias.visual '!gitk'

# Log formatting
git config --global alias.lg "log --color --graph --pretty=format:'%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset' --abbrev-commit"
```

### Troubleshooting Common Issues

#### Undo Changes
```bash
# Undo staged changes (keep file modifications)
git reset HEAD filename

# Undo working directory changes (discard modifications)
git checkout -- filename

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes)
git reset --hard HEAD~1

# Find lost commits
git reflog
git reset --hard <commit-hash>
```

#### Recover from Bad Merge
```bash
# Abort current merge
git merge --abort

# Reset to last known good state
git reset --hard HEAD
```

#### Handle Detached HEAD
```bash
# Check current status
git status

# Create branch from detached HEAD
git checkout -b new-branch-name

# Return to main branch
git checkout main
```

### Team Workflows

#### Feature Branch Workflow
1. **Setup**: Repository with main branch
2. **Development**: Create feature branches for new work
3. **Review**: Pull requests for code review
4. **Integration**: Merge reviewed features to main
5. **Deployment**: Deploy from main branch

#### Git Flow Workflow
1. **main**: Production-ready code
2. **develop**: Integration branch for features
3. **feature branches**: Develop new features
4. **release branches**: Prepare releases
5. **hotfix branches**: Fix production issues

#### Forking Workflow
1. **Fork**: Create personal copy of repository
2. **Clone**: Work on local copy
3. **Push**: Push changes to personal fork
4. **Pull Request**: Propose changes to upstream
5. **Merge**: Maintainer integrates changes

### Git Security

#### SSH vs HTTPS
```bash
# SSH (recommended)
git clone git@github.com:user/repo.git

# HTTPS (alternative)
git clone https://github.com/user/repo.git
```

#### Sensitive Data
- Never commit passwords, API keys, or secrets
- Use environment variables
- Use Git LFS for large binary files
- Use `.gitignore` to exclude sensitive files

#### Signing Commits
```bash
# Configure GPG signing
git config --global commit.gpgsign true
git config --global user.signingkey <key-id>

# Sign commits
git commit -S -m "Signed commit"

# Sign tags
git tag -s v1.0 -m "Release version 1.0"
```

---

## Advanced: Pipeline Reliability (Optional)

*The following sections cover advanced pipeline reliability topics available in the `advanced/` folder. These are recommended after mastering Git fundamentals.*

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
- **UPDATE with idempotent logic**: Same result regardless of executions

**Implementation Strategies**
```python
# Example: UPSERT with ON CONFLICT
def upsert_sales_data(conn, data):
    query = """
    INSERT INTO gold.fact_sales_monthly 
        (month_key, year, month, total_sales, total_quantity)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (month_key) 
    DO UPDATE SET 
        total_sales = EXCLUDED.total_sales,
        total_quantity = EXCLUDED.total_quantity,
        updated_at = CURRENT_TIMESTAMP
    """
    execute_batch(conn, query, data)
```

### Checkpointing

**First Principles**
- Track progress to enable resumption from last successful point
- Prevent re-processing of already completed work
- Essential for long-running batch processes

**Checkpoint Types**
- **File-based**: Store checkpoint in file system
- **Database-based**: Store in operational database
- **Object storage**: Store in S3, GCS, etc.
- **Distributed**: Store in Redis, ZooKeeper, etc.

**Implementation Patterns**
```python
# Database checkpoint table
class CheckpointManager:
    def __init__(self, conn):
        self.conn = conn
    
    def set_month_processed(self, year, month, status='completed'):
        query = """
        INSERT INTO ops.processed_months 
            (month_key, year, month, status)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (month_key) 
        DO UPDATE SET 
            status = EXCLUDED.status,
            updated_at = CURRENT_TIMESTAMP
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (f"{year}-{month:02d}", year, month, status))
        self.conn.commit()
    
    def get_processed_months(self):
        query = "SELECT year, month FROM ops.processed_months WHERE status = 'completed'"
        with self.conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()
```

### Retry Logic

**First Principles**
- Transient failures are common in distributed systems
- Automatic retry improves system reliability
- Exponential backoff prevents system overload

**Retry Strategies**
- **Fixed delay**: Wait same time between retries
- **Linear backoff**: Increase delay linearly
- **Exponential backoff**: Double delay each retry
- **Exponential with jitter**: Add randomness to avoid thundering herd

**Implementation with Exponential Backoff**
```python
import time
import random
import functools

def retry_with_backoff(max_attempts=3, base_delay=1.0, max_delay=60.0):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    
                    # Exponential backoff with jitter
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    jitter = random.uniform(0, delay * 0.1)
                    time.sleep(delay + jitter)
                    
            return None
        return wrapper
    return decorator

# Usage
@retry_with_backoff(max_attempts=3, base_delay=1.0)
def process_month(conn, year, month):
    # Process month data
    pass
```

### Structured Logging

**First Principles**
- Logs should be machine-readable for analysis
- Consistent format enables automated monitoring
- Include context for troubleshooting

**Structured vs Unstructured**
- **Unstructured**: Text-based, human-readable
- **Structured**: JSON/logfmt, machine-readable
- **Best choice**: Structured for production systems

**JSON Logging Implementation**
```python
import json
import logging
from datetime import datetime

class JSONLogger:
    def __init__(self, name, pipeline_name):
        self.logger = logging.getLogger(name)
        self.pipeline_name = pipeline_name
        self.run_id = str(uuid.uuid4())
    
    def log(self, level, message, **metadata):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "message": message,
            "pipeline_name": self.pipeline_name,
            "run_id": self.run_id,
            "metadata": metadata
        }
        
        # Store in database
        self._store_log(log_entry)
        
        # Also log to console/stdout
        getattr(self.logger, level.lower())(message)
    
    def info(self, message, **metadata):
        self.log("INFO", message, **metadata)
    
    def error(self, message, **metadata):
        self.log("ERROR", message, **metadata)
    
    def _store_log(self, log_entry):
        # Store in ops.pipeline_logs table
        pass
```

**Log Levels**
- **DEBUG**: Detailed information for debugging
- **INFO**: General information about program execution
- **WARNING**: Something unexpected happened, but system continues
- **ERROR**: Serious error occurred, system can continue
- **CRITICAL**: Very serious error, system might not continue

**Best Practices**
- Log all errors with full context
- Include correlation IDs for distributed tracing
- Use structured JSON format
- Set appropriate log levels for different environments
- Implement log rotation and retention policies

---

## Summary

Session 3 provides a comprehensive Git curriculum designed to make you proficient in version control and team collaboration. The primary focus on Git prepares you for real-world software development workflows, while the optional advanced section offers pipeline reliability concepts for production-grade data engineering.

**Key Takeaways:**
- Git is essential for collaborative development
- Proper branching and merging strategies prevent chaos
- Structured commits and pull requests enable effective code review
- Advanced features like rebase and stash create professional workflows
- Pipeline reliability concepts prepare you for production systems

**Next Steps:**
- Practice Git workflows on personal projects
- Explore advanced pipeline reliability in `advanced/` folder
- Apply Git best practices in team environments
- Move to Session 4: Orchestration & Operations