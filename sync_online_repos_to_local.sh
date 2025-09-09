#!/bin/bash
# Sync Online to Local - Transcriber System
# =========================================
# 
# This script pulls the latest changes from GitHub to your local transcriber-system.
# Run this to ensure your local files match what's online.

echo "🔄 Syncing Transcriber System: Online to Local..."
echo "=================================================="

# Repository directory
REPO_DIR="/home/ben/SolWorkingFolder/CustomSoftware/transcriber"

# Function to sync the repo
sync_repo() {
    echo ""
    echo "📁 Syncing: Transcriber System"
    echo "----------------------------------------"
    
    if [ -d "$REPO_DIR" ]; then
        cd "$REPO_DIR" || return 1
        
        # Check if there are any local uncommitted changes
        if ! git diff-index --quiet HEAD --; then
            echo "⚠️  Warning: Transcriber System has uncommitted local changes!"
            echo "   Please commit or stash these changes:"
            git status --porcelain
            return 1
        fi
        
        # Fetch latest from GitHub
        echo "🔍 Fetching latest changes..."
        git fetch origin
        
        # Check if we're behind
        LOCAL=$(git rev-parse HEAD)
        REMOTE=$(git rev-parse origin/main)
        
        if [ "$LOCAL" != "$REMOTE" ]; then
            echo "⬇️  Pulling updates from GitHub..."
            git pull origin main
            
            if [ $? -eq 0 ]; then
                echo "✅ Transcriber System synced successfully!"
                return 0
            else
                echo "❌ Failed to sync Transcriber System"
                return 1
            fi
        else
            echo "✅ Transcriber System already up to date"
            return 0
        fi
        
    else
        echo "❌ Repository not found: $REPO_DIR"
        return 1
    fi
}

# Sync the repository
echo "🚀 Syncing Transcriber System..."
echo ""

if sync_repo; then
    echo ""
    echo "=================================================="
    echo "✅ Transcriber System synced successfully!"
    echo ""
    echo "🎉 Ready to work with latest transcriber code!"
    echo "   All local files are now up-to-date with GitHub"
    echo ""
    echo "💡 Remember: When you're done, run './sync_local_to_online_repos.sh' to save your changes"
else
    echo ""
    echo "=================================================="
    echo "❌ Failed to sync Transcriber System"
    echo "   Please resolve issues before starting work"
    exit 1
fi

echo ""
echo "🏁 Online to local sync complete!"
