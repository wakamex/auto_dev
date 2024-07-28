# Autonomy Dev

Tooling to speed up autonomy development.

## Usage

### Contracts

We can scaffold a new contract using the `adev scaffold contract` command. This will create a new directory with;
- open-aea contract component
    - open-aea contract component class 🎉
    - open-aea contract component function generation 🚧
    - open-aea contract component test generation 🚧


```bash
adev scaffold contract 0xc939df369C0Fc240C975A6dEEEE77d87bCFaC259 beyond_pricer \
      --block-explorer-api-key $BLOCK_EXPLORER_API_KEY \
      --block-explorer-url "https://api-goerli.arbiscan.io"
```


## Installation

```bash
pip install autonomy-dev[all]
```
## Release

```bash
checkout main
git pull
adev release
```


# Project Status Badges
[![Code Quality](https://github.com/8ball030/auto_dev/actions/workflows/common_check.yaml/badge.svg)](https://github.com/8ball030/auto_dev/actions/workflows/common_check.yaml)

[![Last Commit](https://img.shields.io/github/last-commit/8ball030/auto_dev)](https://github.com/8ball030/auto_dev/commits/main)

[![Activity](https://img.shields.io/github/commit-activity/m/8ball030/auto_dev)](https://github.com/8ball030/auto_dev/commits/main)

[![Closed Issues](https://img.shields.io/github/issues-closed/8ball030/auto_dev)](https://github.com/8ball030/auto_dev/issues?q=is%3Aissue+is%3Aclosed)

[![Commit Activity](https://gh-card.dev/repos/8ball030/auto_dev.svg)](https://github.com/8ball030/auto_dev)
