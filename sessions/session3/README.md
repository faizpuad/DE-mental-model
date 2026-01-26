# Session 3: Git Collaboration & Version Control

## Overview

Session 3 focuses on Git collaboration, version control workflows, and team development practices. You'll learn essential Git commands, branching strategies, merge techniques, and how to work effectively in a collaborative development environment.

**Note**: An advanced section on pipeline reliability is available in the `advanced/` folder for learners who want to explore production-grade data pipeline concepts after completing the Git curriculum.

## Prerequisites

- Completed Session 1 (Data ingestion pipeline - bronze.raw_transactions)
- Completed Session 2 (Data modeling - silver and gold schemas populated)
- Basic understanding of command line interfaces
- Git installed on your system

## Learning Objectives

### Primary Focus: Git Collaboration
- Set up Git repository and basic configuration
- Master essential Git commands (add, commit, push, pull)
- Understand branching strategies and workflows
- Learn merge techniques and conflict resolution
- Practice remote collaboration with GitHub/GitLab
- Implement stash for work-in-progress management
- Use rebase for clean commit history

### Advanced (Optional): Pipeline Reliability
- Implement idempotent month-based processing for gold layer
- Build checkpoint mechanism using ops.processed_months table
- Add retry logic with exponential backoff
- Implement structured JSON logging (info/warning/error)
- Make pipeline safe to re-run without double-counting

## Git Curriculum Structure

### Module 1: Git Basic Setup
- Repository initialization and configuration
- Basic Git commands and concepts
- First commit and push operations

### Module 2: Branching Strategy
- Creating and managing branches
- Branch naming conventions
- Feature branch workflow

### Module 3: Merge Techniques
- Merge types (fast-forward, 3-way merge)
- Conflict resolution strategies
- Pull request processes

### Module 4: Remote Collaboration
- Working with remote repositories
- GitHub/GitLab workflows
- Team collaboration best practices

### Module 5: Advanced Git Features
- Stash management for WIP
- Rebase for clean history
- Cherry-pick and selective commits

## File Structure

```
sessions/session3/
├── git/                          # Main Git curriculum
│   └── git-lesson/              # Git lesson scripts and tutorials
│       ├── git_basic_setup.sh     # Repository setup and basic commands
│       ├── git_branching_strategy.sh  # Branch management workflows
│       ├── git_merge.sh           # Merge techniques and conflicts
│       ├── git_collaboration.sh   # Team collaboration exercises
│       ├── git_remote_online.sh   # Remote repository operations
│       ├── git_rebase.sh          # Rebase and history management
│       └── git_stash.sh           # Work-in-progress management
├── advanced/                     # Optional advanced topics
│   ├── code/                      # Pipeline reliability code
│   │   ├── init_schemas.py        # Initialize database schemas
│   │   ├── idempotent_pipeline.py # Idempotent gold layer pipeline
│   │   └── reliable_pipeline.py   # Reliable pipeline with logging
│   ├── tests/                     # Test cases
│   ├── docker/                    # Docker configurations
│   └── requirement.txt            # Python dependencies
├── Notes.md                       # Updated theory notes (Git focus + advanced)
├── README.md                      # This file
└── docker-compose.yml             # Moved to advanced/ as optional
```

## Git Learning Path

### Step 1: Basic Git Setup

Run the Git basics tutorial:

```bash
cd sessions/session3
bash git/git-lesson/git_basic_setup.sh
```

**What you'll learn:**
- Git configuration (user.name, user.email)
- Repository initialization (`git init`)
- Basic workflow: add → commit → push
- Understanding `.gitignore` and staging area

### Step 2: Branching Strategy

Practice branch management:

```bash
bash git/git-lesson/git_branching_strategy.sh
```

**What you'll learn:**
- Creating feature branches
- Switching between branches
- Branch naming conventions
- Merge workflows

### Step 3: Merge Techniques

Master merging and conflict resolution:

```bash
bash git/git-lesson/git_merge.sh
```

**What you'll learn:**
- Different merge types
- Handling merge conflicts
- Conflict resolution strategies
- Merge vs rebase decisions

### Step 4: Remote Collaboration

Work with remote repositories:

```bash
bash git/git-lesson/git_remote_online.sh
```

**What you'll learn:**
- GitHub/GitLab integration
- Pull request workflows
- Team collaboration best practices
- Remote branch management

### Step 5: Advanced Git Features

Master professional Git workflows:

```bash
bash git/git-lesson/git_rebase.sh
bash git/git-lesson/git_stash.sh
bash git/git-lesson/git_collaboration.sh
```

**What you'll learn:**
- Clean commit history with rebase
- Stashing work-in-progress
- Advanced collaboration scenarios
- Professional Git workflows

## Advanced Pipeline Reliability (Optional)

After mastering Git, explore advanced pipeline reliability concepts in the `advanced/` folder:

### Setup for Advanced Section

```bash
cd sessions/session3/advanced
# Install dependencies
pip install -r requirement.txt

# Initialize database schemas (optional for Git learning)
python code/init_schemas.py
```

### Advanced Features Available
- **Idempotent Processing**: Safe re-run capabilities
- **Checkpointing**: Progress tracking and recovery
- **Retry Logic**: Exponential backoff mechanisms
- **Structured Logging**: JSON-based pipeline monitoring

*Note: The advanced section requires completion of Sessions 1 & 2 and is optional for Git-focused learners.*

## Git Best Practices

### Daily Workflow
1. Pull latest changes before starting work
2. Create feature branch for new work
3. Commit frequently with meaningful messages
4. Push regularly to backup work
5. Use pull requests for code review

### Branch Naming Conventions
- `feature/user-authentication`
- `bugfix/login-validation`
- `hotfix/critical-security-fix`
- `refactor/database-optimization`

### Commit Message Format
```
type(scope): description

[optional body]

[optional footer]
```

Examples:
- `feat(auth): add OAuth2 integration`
- `fix(api): resolve null pointer exception`
- `docs(readme): update setup instructions`

## Troubleshooting Git Issues

### Common Problems & Solutions

**Merge Conflicts**
```bash
# View conflicts
git status
git diff

# Resolve manually, then:
git add .
git commit
```

**Lost Commits**
```bash
# Find lost commits
git reflog
git reset --hard <commit-hash>
```

**Undo Last Commit**
```bash
# Keep changes
git reset --soft HEAD~1

# Discard changes
git reset --hard HEAD~1
```

**Recover from Bad Merge**
```bash
git merge --abort
git reset --hard HEAD
```

## Team Collaboration Guidelines

### Pull Request Process
1. Create feature branch from main
2. Make changes with atomic commits
3. Push branch to remote
4. Create pull request with description
5. Address code review feedback
6. Merge after approval

### Code Review Checklist
- [ ] Code follows style guidelines
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] No hardcoded credentials
- [ ] Error handling is appropriate

## Next Steps

After completing Session 3 Git curriculum:
- Practice Git workflows on personal projects
- Explore advanced features in the `advanced/` folder
- Move to Session 4: Orchestration & Operations
- Review the `Notes.md` for theoretical concepts

## References

- [Pro Git Book](https://git-scm.com/book)
- [GitHub Git Cheat Sheet](https://education.github.com/git-cheat-sheet-education.pdf)
- [Git Branching Strategies](https://www.atlassian.com/git/tutorials/comparing-workflows)
- [Advanced Git Rebase](https://git-scm.com/book/en/v2/Git-Branching-Rebasing)

For advanced pipeline reliability topics, see references in `advanced/Notes.md`.