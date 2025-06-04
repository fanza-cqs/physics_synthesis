# Git Feature Branch Workflow

This guide covers the complete process of creating a feature branch, developing on it, and merging it back to the main branch.

## Step 1: Create and Set Up Feature Branch

Before starting work on a new feature, create a dedicated branch from the latest main branch:

```bash
# Switch to the main branch
git checkout main

# Or check status
git status

# Pull the latest changes from remote main to ensure you're up-to-date
git pull origin main

# Create a new feature branch and switch to it in one command
git checkout -b feature/new-branch-name

# Push the new branch to remote and set up tracking for future pushes/pulls
git push -u origin feature/new-branch-name
```

## Step 2: Develop Your Feature

Now you can work on your feature. Make commits as needed:

```bash
# Stage all your changes
git add .

# Or, add documents
git add new_document.py

# Commit your changes with a descriptive message
git commit -m "FA: Describe the changes"

# Push your commits to the remote feature branch
git push
```

Repeat the add/commit/push cycle as you develop your feature.

## Step 3: Merge Back to Main Branch

Once your feature is complete and tested, merge it back to main:

```bash
# Switch back to the main branch
git checkout main

# Pull any new changes that might have been added to main while you were working
git pull origin main

# Merge your feature branch into main
git merge feature/new-branch-name

# Push the updated main branch to remote
git push origin main

# Clean up: delete the local feature branch (no longer needed)
git branch -d feature/new-branch-name

# Clean up: delete the remote feature branch
git push origin --delete feature/new-branch-name
```

## Summary

This workflow ensures:
- You always start from the latest main branch
- Your feature development is isolated in its own branch
- The main branch stays clean and stable
- Branches are properly cleaned up after merging

**Note:** If there are merge conflicts during step 3, Git will pause the merge process and ask you to resolve them manually before continuing.