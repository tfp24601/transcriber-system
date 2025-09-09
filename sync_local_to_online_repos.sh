#!/bin/bash
# Sync Local to Online - Transcriber System
# =========================================
# 
# This script commits and pushes all local changes to the transcriber-system GitHub repository.
# Run this to save your local work to the online repository.

echo "🚀 Syncing Transcriber System: Local to Online..."
echo "=================================================="

# Repository directory
REPO_DIR="/home/ben/SolWorkingFolder/CustomSoftware/transcriber"

# Function to commit and push the repo
push_repo() {
    echo ""
    echo "📁 Processing: Transcriber System"
    echo "----------------------------------------"
    
    if [ -d "$REPO_DIR" ]; then
        cd "$REPO_DIR" || return 1
        
        # Check if there are any changes to commit
        if git diff-index --quiet HEAD --; then
            echo "ℹ️  No changes to commit in Transcriber System"
            return 0
        fi
        
        echo "📝 Changes detected in Transcriber System:"
        git status --porcelain
        
        # Add all changes (excluding data/ directory for privacy)
        echo "➕ Adding changes (excluding data/ directory)..."
        git add --all
        git reset data/ 2>/dev/null || true  # Don't add audio/transcript data
        
        if [ $? -ne 0 ]; then
            echo "❌ Failed to add changes in Transcriber System"
            return 1
        fi
        
        # Prompt for commit message if not provided
        if [ -z "$COMMIT_MESSAGE" ]; then
            echo ""
            echo "📝 Enter commit message for Transcriber System (or press Enter for default):"
            read -r user_message
            
            if [ -z "$user_message" ]; then
                commit_msg="Update transcriber system - $(date '+%Y-%m-%d %H:%M')"
            else
                commit_msg="$user_message"
            fi
        else
            commit_msg="$COMMIT_MESSAGE"
        fi
        
        # Commit changes
        echo "💾 Committing changes..."
        git commit -m "$commit_msg"
        
        if [ $? -ne 0 ]; then
            echo "❌ Failed to commit changes in Transcriber System"
            return 1
        fi
        
        # Push to GitHub
        echo "⬆️  Pushing to GitHub..."
        git push origin main
        
        if [ $? -eq 0 ]; then
            echo "✅ Transcriber System pushed successfully!"
            return 0
        else
            echo "❌ Failed to push Transcriber System to GitHub"
            return 1
        fi
        
    else
        echo "❌ Repository not found: $REPO_DIR"
        return 1
    fi
}

# Check for command line commit message
if [ "$1" = "-m" ] && [ -n "$2" ]; then
    COMMIT_MESSAGE="$2"
    echo "📝 Using commit message: '$COMMIT_MESSAGE'"
fi

# Process the repository
echo "🔄 Processing Transcriber System..."
echo ""

if push_repo; then
    echo ""
    echo "=================================================="
    echo "✅ Transcriber System sync completed successfully!"
    echo ""
    echo "🎉 Your transcriber development has been saved to GitHub!"
    echo "   Changes are now available for AI agents and collaboration"
    echo ""
    echo "💡 Next time: Run './sync_online_repos_to_local.sh' to get latest changes from online"
else
    echo ""
    echo "=================================================="
    echo "❌ Failed to sync Transcriber System"
    echo "   Please check the errors above and try again"
    exit 1
fi

echo ""
echo "🏁 Local to online sync complete!"
