#!/bin/bash

# Git Basic Setup Tutorial
# This script demonstrates initial git configuration and setup

echo "=== Git Basic Setup ==="
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "Git is not installed. Please install git first."
    echo "Mac: brew install git"
    echo "Ubuntu: sudo apt-get install git"
    exit 1
fi

echo "1. Configure git user identity"
echo "   git config --global user.name \"Your Name\""
echo "   git config --global user.email \"your.email@example.com\""
echo ""

echo "2. View current git configuration"
echo "   git config --list"
echo ""

echo "3. Check git version"
echo "   git --version"
echo ""

echo "4. Configure default branch name"
echo "   git config --global init.defaultBranch main"
echo ""

echo "5. Configure line endings (Mac/Linux)"
echo "   git config --global core.autocrlf input"
echo ""

echo "6. Configure line endings (Windows)"
echo "   git config --global core.autocrlf true"
echo ""

echo "7. Set useful aliases"
echo "   git config --global alias.st status"
echo "   git config --global alias.co checkout"
echo "   git config --global alias.br branch"
echo "   git config --global alias.ci commit"
echo "   git config --global alias.unstage 'reset HEAD --'"
echo "   git config --global alias.last 'log -1 HEAD'"
echo "   git config --global alias.visual '!gitk'"
echo ""

echo "8. Enable colored output"
echo "   git config --global color.ui auto"
echo ""

echo "9. Check if configuration is saved"
echo "   cat ~/.gitconfig"
echo ""

echo "=== End of Git Basic Setup ==="
