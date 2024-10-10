# Autonomy Dev

Tooling to speed up autonomy development.

## Usage

There are a number of useful command tools available.

- Dev Tooling: linting, formatting and dependency management.

- Scaffolding: Tooling to auto generate repositories and components.

### Create

- Templated agents for speedy proof of concept and getting started fast.


### Scaffolding of Components

#### Protocols

We provide tools to generate protocols components from specs.

```bash
adev create tmp_agent_name -t eightballer/base --force
cd tmp_agent_name
adev scaffold protocol ../specs/protocols/balances.yaml 
aea -s publish --push-missing
...
Starting Auto Dev v0.2.75 ...
Using 32 processes for processing
Setting log level to INFO
Creating agent tmp_agent_name from template eightballer/base
Executing command: ['poetry', 'run', 'autonomy', 'fetch', 'bafybeidohldv57m3jkc33zpgbxukaushmcibmt4ncnsnomd3pvpocxs3ui', '--alias', 'tmp_agent_name']
Command executed successfully.
Agent tmp_agent_name created successfully.
Starting Auto Dev v0.2.75 ...
Using 32 processes for processing
Setting log level to INFO
Read protocol specification: ../specs/protocols/balances.yaml
protolint version 0.50.0(d6a3250)
protolint version 0.50.0(d6a3250)
Updated: /home/eight/Projects/StationsStation/repos/capitalisation_station/tmp_agent_name/protocols/balances/custom_types.py
New protocol scaffolded at /home/eight/Projects/StationsStation/repos/capitalisation_station/tmp_agent_name/protocols/balances

...
# Tests can be run as well;
adev test -p packages/eightballer/protocols/balances
Testing path: `packages/eightballer/protocols/balances/` ⌛
Testing... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   0% -:--:--👌 - packages/eightballer/protocols/balances/
Testing... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:02
Testing completed successfully! ✅
```

#### Contracts

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
