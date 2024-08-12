# Scaffolding a new API Handler agent.

The tools within the `handler` subcommand are used to scaffold a new agent.

We start with a simple openapi;

```bash
cat auto_dev/data/openapi/openapi_specification.yaml
```

We now scaffold the agent and cd in.

```bash
aea create new_agent && cd new_agent
```

This creates a new agent without any real skills.

Once we have a new agent, we can now use the cli to scaffold the skill using the CORE autonomy libraries and the OpenAPI specification.

This reduces the amount of code we need to write to get a skill up and means that we have no need to write any code to re-implement the wheel.

## Scaffolding a new skill

Use the --new-skill flag to scaffold a new skill.

```bash
adev scaffold handler ../auto_dev/data/openapi/openapi_specification.yaml --output my_api_skill --new-skill
```

The skill will be created in the skills directory.  The user will be prompted whether to rename MyModel.py to strategy.py, and whether to remove the dialogues.py file. THe scaffolding step will also install the http protocol, and fingerprint the skill.  At the completion, the user can now run the agent.

```bash
aea run
```
