# # we re implement as a click command with 2 different commands
# # - generate metadata. we read in a meta data file and generate a json file that can be uploaded to ipfs.
# # - print metadata: we read in a meta data file and print it in a way that can be copy pasted into the frontend.
import json
from typing import List
import yaml
from aea_cli_ipfs.ipfs_utils import IPFSTool
from aea.helpers.cid import to_v1

from aea.configurations.base import AgentConfig, CRUDCollection, PublicId
from aea.configurations.constants import (
    AGENT,
    AGENTS,
    CONNECTIONS,
    CONTRACTS,
    DEFAULT_AEA_CONFIG_FILE,
    DEFAULT_README_FILE,
    ITEM_TYPE_PLURAL_TO_TYPE,
    PROTOCOLS,
    SKILLS,
    SERVICES,
    SERVICE
)


from rich import print_json
import rich_click as click

def read_yaml_file(file_path):
    with open(file_path, 'r') as file:
        data = list(yaml.safe_load_all(file))[0]
    return data

def read_json_file(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data


def write_json_file(file_path, data):
    with open(file_path, 'w') as file:
        json.dump(data, file, separators=(',', ':'))


def get_metadata(root, name, hash_, target_id):
    split_name = name.split('/')
    file_name = split_name[0] if split_name[0] != "agent" else "aea-config"
    data = read_yaml_file(root + "/packages/{author}/{package_type}s/{package_name}/{file_name}.yaml".format(author=split_name[1], package_type=split_name[0], package_name=split_name[2], file_name=file_name))
    name_ = "{package_type}/{author}/{package_name}:{version}".format(package_type=split_name[0], author=split_name[1], package_name=split_name[2], version=split_name[3])
    response = IPFSTool().client.add(root + f"/mints/{target_id}.png", pin=True, recursive=True, wrap_with_directory=False)
    image_hash = to_v1(response["Hash"])
    return {"name":name_,"description":data["description"],"code_uri":f"ipfs://{hash_}","image":f"ipfs://{image_hash}","attributes":[{"trait_type":"version","value":f"{split_name[3]}"}]}


def get_package_deps(root, name,):
    """
    Get package dependencies by reading in the package.yaml file and then getting the packages from the yaml keys in the orders of:
    - contracts
    - protocols
    - connections
    - skills
    - agents

    """

def render_metadata(metadata):
    """Render metadata for a package"""
    click.echo("Raw Data:")
    print_json(data=metadata)
    click.echo("\nName:", )
    click.echo(metadata["name"])
    click.echo("\nDescription:", )
    click.echo(f"`{metadata['description']}`")

    click.echo("\nVersion:", )
    click.echo(metadata["attributes"][0]["value"])

    click.echo("\nPackage Hash:", )
    click.echo(metadata["code_uri"][14:])
    click.echo("\nNFT Image URL:", )
    click.echo(metadata["image"])

    dependencies = build_dependency_tree_for_component(metadata["name"])
    click.echo("\nDependencies:", )
    mint_status = {}
    raise Exception("STOPPING HERE")
    for dependency, path in dependencies.items():
        component_status, component_id = check_component_status(dependency)
        mint_status[component_id] = component_status
        # we use a sexy emjoji to show the status of the minting.
        status_emjoji = "✅" if component_status == "MINTED" else "❌"
        click.echo(f"Status: {status_emjoji} {component_status} - {dependency} - {path}")




@click.group()
def cli():
    """Meta data generation tool for aea packages"""

@cli.command()
@click.argument("root", type=click.Path(exists=True),)
@click.argument("target_name", type=str,)
@click.argument("target_id", type=str, )
def generate(root, target_name, target_id):
    """Generate metadata for a package
    
    example usage:
         python ./metadata.py generate . contract/eightballer/cool_skill/0.1.0 01
    
    """
    data = read_json_file(root + "/packages/packages.json")
    for name, hash_ in data['dev'].items():
        if name != target_name:
            continue
        metadata = get_metadata(root, name, hash_, target_id)
        break
    write_json_file(root + f"/mints/{target_id}.json", metadata)
    click.echo("Metadata generated successfully! Saved to: {}".format(root + f"/mints/{target_id}.json"))
    render_metadata(metadata)


# we will be minting compoenents sequentially as some components depend on others.
# the order of the dependency is:
# -protocols
# -contracts
# -connections
# -skills
# -agents
# -services
# when we render the metadata we will need to get the dependencies and PRINT them to the user.
# we also need to 2 checks A) if the package is already minted, this will be confirmed by checking 
# in the mapping.txt file in the mints folder. 
# B) if the package is already minted, we need to check if the hash is the same as the one in the mapping.txt file. this will be done later.

dependency_order = [
    PROTOCOLS,
    CONTRACTS,
    CONNECTIONS,
    SKILLS,
    AGENTS,
    SERVICES,
]
class Dependency(PublicId):
    component_type: str

def build_dependency_tree_for_component(component) -> List[str]:
    """Build dependency tree for a component"""
    component_type = component.split("/")[0]
    component_author = component.split("/")[1]
    component_name = component.split("/")[2]
    public_id = PublicId(component_author, component_name.split(":")[0])
    if component_type == AGENT:
        file_name = DEFAULT_AEA_CONFIG_FILE
    elif component_type == SERVICE:
        file_name = "service.yaml"
    else:
        file_name = f"{component_type}.yaml"
    
    component_path = f"packages/{public_id.author}/{component_type}s/{public_id.name}/{file_name}"
    component_data = read_yaml_file(component_path)

    dependencies = {}


    for dependency_type in dependency_order:
        if dependency_type == AGENTS:
            if component_type != SERVICE:
                continue
        if component_type == SERVICE and dependency_type == SERVICES:
                dependency_id = Dependency.from_str(component_data[AGENT])
                dependency_id.component_type = AGENT
                path = f"{dependency_type}/{dependency_id.author}/{dependency_id.name}"
                dependencies[dependency_id] = path
        else:
            if dependency_type not in component_data:
                continue
            for dependency in component_data[dependency_type]:
                dependency_id = Dependency.from_str(dependency)
                dependency_id.component_type = dependency_type[:-1]
                path = (f"{dependency_type}/{dependency_id.author}/{dependency_id.name}")
                dependencies[dependency_id] = path
    return dependencies


@cli.command()
@click.argument("metadata_file", type=click.Path(exists=True),)
def print_metadata(metadata_file):
    """Print metadata for a package"""
    metadata = read_json_file(metadata_file)
    render_metadata(metadata)

def render_metadata(metadata):
    """Render metadata for a package"""
    click.echo("Raw Data:")
    print_json(data=metadata)
    click.echo("\nName:", )
    click.echo(metadata["name"])
    self_component = Dependency.from_str("/".join(metadata["name"].split("/")[1:]))
    self_component.component_type = metadata["name"].split("/")[0]
    click.echo(f"\nType: \n{self_component.component_type}")
    self_component_status, self_component_id = check_component_status(self_component)
    click.echo("\nDescription:", )
    click.echo(f"\"{metadata['description']}\"")

    click.echo("\nVersion:", )
    click.echo(metadata["attributes"][0]["value"])

    click.echo("\nPackage Hash:", )
    click.echo(metadata["code_uri"][14:])
    click.echo("\nNFT Image URL:", )
    click.echo(metadata["image"])

    dependencies = build_dependency_tree_for_component(metadata["name"])
    click.echo("\nDependencies:", )
    mint_status = {}
    for dependency, path in dependencies.items():
        component_status, component_id = check_component_status(dependency)
        mint_status[component_id] = component_status
        # we use a sexy emjoji to show the status of the minting.
        status_emjoji = "✅" if component_status == "MINTED" else "❌"
        click.echo(f"Status: {status_emjoji} {component_id if component_id else ''} {component_status} - {path}")

    # we print the self mint status
    # we first check that all the dependencies are minted.
    # if they are not minted, we print the dependencies that are not minted.
    # if they are minted, we print the dependecies list.
    # we also print the self mint status.

    for component_id, component_status in mint_status.items():
        if component_status == "NOT MINTED":
            click.echo(f"\n{component_id} is not minted. Please mint it first.")
            return
    click.echo("\nAll dependencies are minted. You can mint this component now.")

    deps_ids_numeric = sorted(map(int, mint_status.keys()))

    click.echo(f"\nDependencies: \n{list(deps_ids_numeric)}")

    click.echo("\nSelf Mint Status:", )
    status_emjoji = "✅" if self_component_status == "MINTED" else "❌"
    click.echo(f"{status_emjoji} {self_component_id if self_component_id else ''} {self_component_status} - {self_component} ")

def check_component_status(component_id):
    """
    We check the status of the component by reading the mapping.txt file in the mints folder.
    ➤ cat mints/mapping.txt 
    token_id-"component_id"
    # deps
    1-"protocol/valory/abci/0.1.0"
    2-"protocol/valory/acn/1.1.0"
    3-"protocol/valory/contract_api/1.0.0"
    4-"protocol/valory/http/1.0.0"
    5-"protocol/valory/ledger_api/1.0.0"
    6-"protocol/valory/tendermint/0.1.0"
    7-"protocol/open_aea/signing/1.0.0"
    8-"connection/valory/abci/0.1.0"
    9-"connection/valory/http_client/0.23.0"
    10-"connection/valory/ledger/0.19.0"
    11-"connection/valory/p2p_libp2p_client/0.1.0"
    12-"contract/valory/service_registry/0.1.0"
    13-"skill/valory/abstract_abci/0.1.0"
    14-"skill/valory/abstract_round_abci/0.1.0"
    16-"skill/valory/registration_abci/0.1.0"
    17-"skill/valory/reset_pause_abci/0.1.0"
    18-"contract/valory/gnosis_safe_proxy_factory/0.1.0"
    19-"contract/valory/gnosis_safe/0.1.0"
    20-"contract/valory/multisend/0.1.0"
    22-"skill/valory/transaction_settlement_abci/0.1.0"
    39-"protocol/valory/ipfs/0.1.0"
    50-"connection/valory/ipfs/0.1.0"
    51-"contract/valory/multicall2/0.1.0"
    # dev
    97-contract/zarathustra/grow_registry:0.1.0
    ?-skill/zarathustra/plantation_abci/0.1.0
    ?-skill/zarathustra/plantation_station_abci/0.1.0
    ?-agent/zarathustra/plantation/0.1.0
    ?-service/eightballer/plantation_station/0.1.0

    NOTES: if the component is NOT present in the mapping.txt file, then it is not minted.
    if the component is present in the mapping.txt file, and the token_id is a number, then it is minted.
    we always return the token_id, even if it is not minted.

    """
    with open("mints/mapping.txt", "r") as file:
        lines = file.readlines()
    status, token_id = "NOT MINTED", "?"
    path = f"{component_id.component_type}/{component_id.author}/{component_id.name}"
    for line in lines:
        if path in line:
            if line.split("-")[0].isnumeric():
                status = "MINTED"
                token_id = line.split("-")[0]
                break
    return status, token_id



if __name__ == '__main__':
    cli()

