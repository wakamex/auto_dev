# Autonomy Dev

Tooling to speed up autonomy development.

# Installation

```bash
pip install autonomy-dev[all]
```
# Release
bump the version in pyoproject and create a new branch and tag

```bash
git checkout -b v0.1.5
git tag v0.1.5
git push --tag
git push --set-upstream origin (git rev-parse --abbrev-ref HEAD)
```