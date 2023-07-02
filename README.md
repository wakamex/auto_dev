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
bump the version in pyoproject and create a new branch and tag

```bash
export new_version=v0.1.5
git checkout -b $new_version
git add .
git tag $new_version
git push --set-upstream origin (git rev-parse --abbrev-ref HEAD)
git push --tag
```