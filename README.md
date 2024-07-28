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

[![Build Status](https://img.shields.io/github/actions/workflow/status/8ball030/auto_dev/build.yaml?branch=main)](https://github.com/8ball030/auto_dev/actions/workflows/build.yaml)
[![Coverage Status](https://img.shields.io/codecov/c/github/8ball030/auto_dev)](https://codecov.io/gh/8ball030/auto_dev)
[![Code Quality](https://img.shields.io/scrutinizer/quality/g/8ball030/auto_dev)](https://scrutinizer-ci.com/g/8ball030/auto_dev/)
[![Dependencies](https://img.shields.io/librariesio/release/npm/auto_dev)](https://libraries.io/npm/auto_dev)
[![Version](https://img.shields.io/github/v/release/8ball030/auto_dev)](https://github.com/8ball030/auto_dev/releases)
[![License](https://img.shields.io/github/license/8ball030/auto_dev)](https://github.com/8ball030/auto_dev/blob/main/LICENSE)
[![Contributors](https://img.shields.io/github/contributors/8ball030/auto_dev)](https://github.com/8ball030/auto_dev/graphs/contributors)
[![Open Issues](https://img.shields.io/github/issues/8ball030/auto_dev)](https://github.com/8ball030/auto_dev/issues)
[![Pull Requests](https://img.shields.io/github/issues-pr/8ball030/auto_dev)](https://github.com/8ball030/auto_dev/pulls)
[![Downloads](https://img.shields.io/github/downloads/8ball030/auto_dev/total)](https://github.com/8ball030/auto_dev/releases)

