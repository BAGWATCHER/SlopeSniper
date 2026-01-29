  Post-PR Merge Workflow

  After your PR is merged to BAGWATCHER/SlopeSniper:main:

  # 1. Switch to main and pull latest from production
  git checkout main
  git pull origin main

  # 2. Sync fork's main branch
  git push fork main

  # 3. Reset dev branch to new main (for next round of changes)
  git checkout bagwatcher-release
  git reset --hard origin/main
  git push fork bagwatcher-release --force

  ---
  Full Cycle Reference

  # === DEVELOP ===
  git checkout bagwatcher-release
  # make changes...
  git add -A && git commit -m "description"
  git push fork bagwatcher-release

  # === CREATE PR ===
  GH_TOKEN="your_pat" gh pr create \
    --repo BAGWATCHER/SlopeSniper \
    --base main \
    --head maddefientist:bagwatcher-release \
    --title "title" --body "description"

  # === AFTER MERGE ===
  git checkout main
  git pull origin main
  git push fork main
  git branch -D bagwatcher-release  # or reset it for reuse


