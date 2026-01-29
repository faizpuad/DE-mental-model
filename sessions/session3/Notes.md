# Session 3 Notes: Git Fundamentals & Collaboration

## Primary Focus: Core Git Skills

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

## Summary

Session 3 provides essential Git skills for collaborative development. You'll master the core Git workflow from repository initialization to team collaboration through pull requests and rebase.

**Key Takeaways:**
- Git fundamentals are essential for team development
- Proper workflow with add, commit, push, pull forms the foundation
- GitHub collaboration through forks and pull requests enables teamwork
- Branching and merging strategies prevent code conflicts
- Rebase creates clean, linear commit history
- Professional Git workflows prepare you for real-world development

**Next Steps:**
- Practice Git workflows on personal projects
- Apply Git best practices in team environments
- Explore advanced pipeline reliability in `advanced-pipeline-reliability/` folder (optional)
- Move to Session 4: AWS Data Engineering Fundamentals