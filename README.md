# Autonomy Dev

Tooling to speed up autonomy development.

# Installation

```bash
pip install autonomy-dev[all]
```
# Release
bump the version in pyoproject and create a new branch and tag

```bash
export new_version=v0.1.5
git checkout -b $new_version
git add .
git tag $new_version
git push --set-upstream origin (git rev-parse --abbrev-ref HEAD)
git push --tag
```