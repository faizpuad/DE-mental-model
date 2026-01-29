# Session 3: Git Fundamentals & Collaboration

## Overview

Session 3 focuses on essential Git skills for collaborative development. You'll master the core Git workflow, from initializing a repository to collaborating with team members through pull requests and rebase.

**Note**: Advanced pipeline reliability topics are available in the `advanced-pipeline-reliability/` folder for learners who want to explore production-grade data engineering concepts after mastering Git fundamentals.

## Prerequisites

- Completed Session 1 (Data ingestion pipeline - bronze.raw_transactions)
- Completed Session 2 (Data modeling - silver and gold schemas populated)
- Basic understanding of command line interfaces
- Git installed on your system

## Learning Objectives

### Core Git Fundamentals
- Repository initialization and configuration (`git init`, `git config`)
- Essential Git workflow commands (`git status`, `git add`, `git commit`)
- Remote repository operations (`git clone`, `git push`, `git pull`)
- GitHub collaboration workflows (fork, pull request, merge)

### Advanced Git Features
- Branch creation and management
- Merge techniques and conflict resolution
- Clean commit history with `git rebase`
- Work-in-progress management with `git stash`

## Git Curriculum Structure

### Module 1: Repository Setup & Basic Workflow
- Repository initialization (`git init`)
- Basic configuration (`git config`)
- Essential workflow: `git status`, `git add`, `git commit`

### Module 2: Remote Collaboration
- GitHub repository operations (fork, clone)
- Working with remotes (`git push`, `git pull`)
- Pull request workflow through GitHub interface

### Module 3: Branching & Merging
- Branch creation and management
- Merge techniques and conflict resolution
- Team collaboration through pull requests

### Module 4: Advanced Git Features
- Clean commit history with `git rebase`
- Work-in-progress management with `git stash`
- Professional Git workflow best practices

## File Structure

```
sessions/session3/
├── git/                          # Main Git curriculum
│   └── git-lesson/              # Git lesson scripts and tutorials
│       ├── git_basic_setup.sh     # Repository setup and basic commands
│       ├── git_remote_online.sh   # GitHub collaboration and remotes
│       ├── git_branching_strategy.sh  # Branch management workflows
│       ├── git_merge.sh           # Merge techniques and conflicts
│       ├── git_rebase.sh          # Clean commit history management
│       ├── git_stash.sh           # Work-in-progress management
│       └── git_collaboration.sh   # Team collaboration exercises
├── advanced-pipeline-reliability/  # Optional advanced topics
│   ├── code/                      # Pipeline reliability code
│   │   ├── init_schemas.py        # Initialize database schemas
│   │   ├── idempotent_pipeline.py # Idempotent gold layer pipeline
│   │   └── reliable_pipeline.py   # Reliable pipeline with logging
│   ├── tests/                     # Test cases
│   ├── docker/                    # Docker configurations
│   └── requirement.txt            # Python dependencies
├── Notes.md                       # Git theory notes
├── README.md                      # This file
└── .env.example                   # Environment variables template
```

## Git Learning Path

### Step 1: Repository Setup & Basic Workflow

Learn Git fundamentals:

```bash
cd sessions/session3
bash git/git-lesson/git_basic_setup.sh
```

**What you'll learn:**
- Git configuration (user.name, user.email)
- Repository initialization (`git init`)
- Essential workflow: `git status`, `git add`, `git commit`
- Understanding `.gitignore` and staging area

### Step 2: Remote Collaboration with GitHub

Master GitHub workflows:

```bash
bash git/git-lesson/git_remote_online.sh
```

**What you'll learn:**
- Repository forking and cloning
- Working with remotes (`git push`, `git pull`)
- GitHub pull request process
- Team collaboration through GitHub interface

### Step 3: Branching & Merging

Practice branch management:

```bash
bash git/git-lesson/git_branching_strategy.sh
bash git/git-lesson/git_merge.sh
```

**What you'll learn:**
- Creating and switching branches
- Merge techniques and conflict resolution
- Pull request best practices
- Team collaboration workflows

### Step 4: Advanced Git Features

Master professional Git workflows:

```bash
bash git/git-lesson/git_rebase.sh
bash git/git-lesson/git_stash.sh
bash git/git-lesson/git_collaboration.sh
```

**What you'll learn:**
- Clean commit history with `git rebase`
- Work-in-progress management with `git stash`
- Advanced collaboration scenarios
- Professional Git best practices

## Advanced Pipeline Reliability (Optional)

After mastering Git fundamentals, explore production-grade data engineering concepts in the `advanced-pipeline-reliability/` folder:

### Setup for Advanced Section

```bash
cd sessions/session3/advanced-pipeline-reliability
# Install dependencies
pip install -r requirement.txt

# Initialize database schemas
python code/init_schemas.py
```

### Advanced Features Available
- **Idempotent Processing**: Safe re-run capabilities
- **Checkpointing**: Progress tracking and recovery
- **Retry Logic**: Exponential backoff mechanisms
- **Structured Logging**: JSON-based pipeline monitoring

*Note: This advanced section requires completion of Sessions 1 & 2 and is optional for Git-focused learners.*

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
- Explore advanced pipeline reliability in the `advanced-pipeline-reliability/` folder
- Move to Session 4: AWS Data Engineering Fundamentals
- Review the `Notes.md` for theoretical Git concepts

## References

- [Pro Git Book](https://git-scm.com/book)
- [GitHub Git Cheat Sheet](https://education.github.com/git-cheat-sheet-education.pdf)
- [Git Branching Strategies](https://www.atlassian.com/git/tutorials/comparing-workflows)
- [Advanced Git Rebase](https://git-scm.com/book/en/v2/Git-Branching-Rebasing)

For advanced pipeline reliability topics, see references in `advanced/Notes.md`.