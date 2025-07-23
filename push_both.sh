#!/bin/bash
# push_both.sh - Push to both CodeCrafters and GitHub

echo "🚀 Pushing to CodeCrafters..."
git push origin master

if git remote | grep -q github; then
    echo "📊 Pushing to GitHub for contributions..."
    git push github master
    echo "✅ Successfully pushed to both repositories!"
else
    echo "⚠️  GitHub remote not configured. Add it with:"
    echo "git remote add github https://github.com/YOUR_USERNAME/codecrafters-redis-python.git"
fi
