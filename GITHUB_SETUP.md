# GitHub Setup Guide - Yahboom Dashboard

Complete step-by-step guide to connect your project to GitHub and push your code.

## 📋 Prerequisites

- Git installed (✓ You have it: `git version 2.34.1`)
- GitHub account (create one at https://github.com if you don't have one)
- Terminal access

---

## Step 1: Configure Git (First Time Only)

If this is your first time using git on this computer, set up your identity:

```bash
# Set your name (use your GitHub username or real name)
git config --global user.name "Your Name"

# Set your email (use the email associated with your GitHub account)
git config --global user.email "your.email@example.com"

# Verify the configuration
git config --global --list
```

**Example:**
```bash
git config --global user.name "John Doe"
git config --global user.email "john.doe@example.com"
```

---

## Step 2: Initialize Git Repository

Navigate to your project directory and initialize git:

```bash
cd /home/john/yahboom_dashboard

# Initialize git repository
git init

# Check status
git status
```

---

## Step 3: Add Files to Git

Add all project files (the `.gitignore` will automatically exclude venv, recordings, etc.):

```bash
# Add all files
git add .

# Check what will be committed
git status
```

You should see files like:
- `backend/`
- `frontend/`
- `config/`
- `README.md`
- `HOWTO.md`
- `requirements.txt`
- `.gitignore`

**Note:** `streamlit-venv/` and `recordings/` should NOT appear (they're in `.gitignore`).

---

## Step 4: Create Initial Commit

```bash
# Create your first commit
git commit -m "Initial commit: Yahboom Dashboard - Real-time robotic control & replay system"
```

---

## Step 5: Create GitHub Repository

### Option A: Using GitHub Website (Recommended for Beginners)

1. **Go to GitHub**: https://github.com
2. **Sign in** to your account
3. **Click the "+" icon** in the top right corner
4. **Select "New repository"**
5. **Fill in the details:**
   - **Repository name**: `yahboom_dashboard` (or any name you prefer)
   - **Description**: "Real-Time Robotic Control & Replay System for ROS2"
   - **Visibility**: Choose Public or Private
   - **DO NOT** check "Initialize with README" (we already have one)
   - **DO NOT** add .gitignore or license (we already have them)
6. **Click "Create repository"**

### Option B: Using GitHub CLI (if you have `gh` installed)

```bash
# Install GitHub CLI if needed (Ubuntu/Debian)
# sudo apt install gh

# Authenticate (first time only)
gh auth login

# Create repository
gh repo create yahboom_dashboard --public --description "Real-Time Robotic Control & Replay System for ROS2"
```

---

## Step 6: Connect Local Repository to GitHub

After creating the repository on GitHub, you'll see a page with setup instructions. Use the "push an existing repository" option:

```bash
# Add GitHub as remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/yahboom_dashboard.git

# Verify remote was added
git remote -v
```

**Example:**
```bash
git remote add origin https://github.com/johndoe/yahboom_dashboard.git
```

---

## Step 7: Authenticate with GitHub

### Option A: Personal Access Token (Recommended)

GitHub no longer accepts passwords. You need a Personal Access Token:

1. **Go to GitHub**: https://github.com/settings/tokens
2. **Click "Generate new token"** → **"Generate new token (classic)"**
3. **Name it**: "Yahboom Dashboard"
4. **Select scopes**: Check `repo` (full control of private repositories)
5. **Click "Generate token"**
6. **Copy the token** (you won't see it again!)

When you push, use your token as the password:
- **Username**: Your GitHub username
- **Password**: The token you just created

### Option B: SSH Keys (More Secure, One-Time Setup)

```bash
# Generate SSH key (if you don't have one)
ssh-keygen -t ed25519 -C "your.email@example.com"

# Start SSH agent
eval "$(ssh-agent -s)"

# Add key to agent
ssh-add ~/.ssh/id_ed25519

# Copy public key to clipboard
cat ~/.ssh/id_ed25519.pub

# Add to GitHub:
# 1. Go to https://github.com/settings/keys
# 2. Click "New SSH key"
# 3. Paste the key
# 4. Save

# Then use SSH URL instead:
git remote set-url origin git@github.com:YOUR_USERNAME/yahboom_dashboard.git
```

---

## Step 8: Push to GitHub

```bash
# Push to GitHub (main branch)
git branch -M main
git push -u origin main
```

**First time:** You'll be prompted for username and password (use your token as password).

**Success message:**
```
Enumerating objects: X, done.
Counting objects: 100% (X/X), done.
Writing objects: 100% (X/X), done.
To https://github.com/YOUR_USERNAME/yahboom_dashboard.git
 * [new branch]      main -> main
Branch 'main' set up to track remote branch 'main' from 'origin'.
```

---

## Step 9: Verify on GitHub

1. Go to your repository: `https://github.com/YOUR_USERNAME/yahboom_dashboard`
2. You should see all your files!
3. Check that `streamlit-venv/` and `recordings/` are NOT there (they're ignored)

---

## 🎉 You're Done!

Your code is now on GitHub! 

---

## Future Updates

When you make changes, push them like this:

```bash
# Check what changed
git status

# Add changed files
git add .

# Commit with a message
git commit -m "Description of your changes"

# Push to GitHub
git push
```

---

## Quick Reference Commands

```bash
# Check status
git status

# See what files changed
git diff

# Add all changes
git add .

# Commit changes
git commit -m "Your commit message"

# Push to GitHub
git push

# Pull latest changes (if working from multiple computers)
git pull

# View commit history
git log --oneline

# See remote repository
git remote -v
```

---

## Troubleshooting

### "Repository not found" error

- Check your repository name matches exactly
- Verify you have access to the repository
- Make sure you're using the correct username

### "Authentication failed"

- If using HTTPS: Make sure you're using a Personal Access Token, not your password
- If using SSH: Make sure your SSH key is added to GitHub

### "Permission denied"

- Check your GitHub username is correct
- Verify your Personal Access Token has `repo` scope
- Try regenerating your token

### "Updates were rejected"

Someone else pushed changes. Pull first:
```bash
git pull origin main
# Resolve any conflicts, then:
git push
```

### Want to change remote URL?

```bash
# View current remote
git remote -v

# Change to new URL
git remote set-url origin https://github.com/NEW_USERNAME/NEW_REPO.git
```

---

## Security Best Practices

1. **Never commit sensitive data:**
   - API keys
   - Passwords
   - Personal tokens
   - Use `.env` file and add to `.gitignore`

2. **Use `.gitignore`:**
   - Already set up for this project
   - Excludes venv, recordings, logs, etc.

3. **Use Personal Access Tokens:**
   - More secure than passwords
   - Can be revoked if compromised
   - Scoped to specific permissions

---

## Next Steps

- Add a license file (MIT, Apache, etc.)
- Set up GitHub Actions for CI/CD
- Add branch protection rules
- Create releases/tags for versions
- Add collaborators if working in a team

---

**Need Help?** Check GitHub's official docs: https://docs.github.com/en/get-started
