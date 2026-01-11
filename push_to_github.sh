#!/bin/bash
# Push to GitHub Script
# Run this locally after downloading the project

# Configuration - Update these!
GITHUB_USERNAME="YOUR_GITHUB_USERNAME"
REPO_NAME="prompt-to-video-app"

echo "🚀 Pushing to GitHub..."

# Initialize git if not already done
if [ ! -d ".git" ]; then
    git init
    git branch -m main
fi

# Configure git
git config user.email "${GITHUB_USERNAME}@users.noreply.github.com"
git config user.name "${GITHUB_USERNAME}"

# Add all files
git add -A

# Commit
git commit -m "Initial commit: Prompt-to-Video App with Enhancement Pipeline

Features:
- Full-stack video generation from text prompts
- Prompt Enhancement Pipeline:
  - Concept Extractor (subjects, actions, settings, emotions)
  - Style Extractor (cinematic, cultural, mood, lighting)
  - Aesthetic Scorer (quality prediction 0-100)
  - Dynamic Context Builder
  - Feedback Loop (iterative refinement)
  - Frame Smoother (temporal consistency)
- Provider Registry with quality-first selection
- Smart Orchestrator with automatic fallbacks
- Support for Veo 3.1, Sora, Runway, Kling
- Voice synthesis with Fish Audio, ElevenLabs
- React frontend with glass-morphism UI
- Docker deployment ready"

# Create repo on GitHub (requires gh CLI)
echo "Creating repository on GitHub..."
gh repo create ${REPO_NAME} --public --description "AI-powered prompt-to-video generator with advanced prompt enhancement pipeline" --source=. --remote=origin --push

echo "✅ Done! Repository pushed to: https://github.com/${GITHUB_USERNAME}/${REPO_NAME}"
