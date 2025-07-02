#!/usr/bin/env python3
"""
Bitbucket Environment Variable Manager.

This module provides functionality to export and import environment variables
for Bitbucket deployment environments. It supports both secured and non-secured
variables and can handle bulk operations through JSON files.
"""

import argparse
import json
import os
import sys
from typing import cast, Union, Any
from dataclasses import dataclass

import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

# -- local ./helpers
from helpers.logging import BitbucketLogger

# pylint: disable=import-error

# pylint: disable=too-many-arguments, too-many-positional-arguments
@dataclass
class BitbucketConfig:
    """Configuration class for Bitbucket API operations."""
    workspace: str
    repo_slug: str
    deployment_name: str
    auth: HTTPBasicAuth
    logger: Any

def arg_parser() -> argparse.Namespace:
    """Parse arguments and execute export or import functionality."""
    parser = argparse.ArgumentParser(
        description='''
        Manage Bitbucket deployment environment variables.
        Requires BITBUCKET_USERNAME and BITBUCKET_APP_PASSWORD in bitbucket.env.
        '''
    )
    _ = parser.add_argument(
        "-w",
        "--workspace",
        required=True,
        help="Bitbucket workspace"
    )
    _ = parser.add_argument(
        "-r",
        "--repo-slug",
        required=True,
        help="Repository slug"
    )
    _ = parser.add_argument(
        "-d",
        "--deployment-name",
        required=True,
        help="Deployment environment name"
    )
    _ = parser.add_argument(
        '-l',
        '--logfile',
        help='Output a log file',
        action='store_true'
    )
    _ = parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging"
    )

    group = parser.add_mutually_exclusive_group(required=True)
    _ = group.add_argument(
        "-o",
        "--output",
        help="Output JSON file for exporting non-secured variables"
    )
    _ = group.add_argument(
        "-a",
        "--all-vars-output",
        help="Output JSON file for exporting all variables"
    )
    _ = group.add_argument(
        "-e",
        "--export-secret-keys",
        help="Output JSON file for exporting secured variable keys"
    )
    _ = group.add_argument(
        "-i",
        "--import",
        dest="import_file",
        help="Input JSON file for importing variables"
    )
    _ = group.add_argument(
        "--import-all",
        dest="import_all",
        help="Input JSON file for importing all variables, including secret keys"
    )

    return parser.parse_args()


def get_environment_uuid(
    workspace: str,
    repo_slug: str,
    deployment_name: str,
    auth: HTTPBasicAuth,
    logger: Any
) -> str:
    """Retrieve the UUID of the specified deployment environment."""
    logger.debug("Fetching environments for workspace %s, repo %s", workspace, repo_slug)
    url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}/environments"
    response = requests.get(url, auth=auth, timeout=30)
    response.raise_for_status()
    environments = cast(list[dict[str, object]], response.json()["values"])
    logger.debug("Received %s environments", len(environments))
    for env in environments:
        logger.debug("Checking environment: %s", env['name'])
        if env["name"] == deployment_name:
            logger.info("Found environment '%s' with UUID %s", deployment_name, env['uuid'])
            return str(env["uuid"])
    logger.error("Deployment environment '%s' not found", deployment_name)
    raise ValueError(f"Deployment environment '{deployment_name}' not found")


def get_variables(
    workspace: str,
    repo_slug: str,
    environment_uuid: str,
    auth: HTTPBasicAuth,
    logger: Any
) -> list[dict[str, object]]:
    """Fetch all environment variables for the given environment UUID."""
    logger.debug(
        "Fetching variables for repository %s/%s, environment %s",
        workspace, repo_slug, environment_uuid
    )
    url = (f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}/"
           f"deployments_config/environments/{environment_uuid}/variables?pagelen=1")
    all_variables: list[dict[str, object]] = []
    while url:
        logger.debug("Requesting %s", url)
        response = requests.get(url, auth=auth, timeout=30)
        response.raise_for_status()
        data = cast(dict[str, object], response.json())
        variables = cast(list[dict[str, object]], data.get("values", []))
        if not variables:
            logger.info("No variables configured for %s", environment_uuid)
            return all_variables
        key = variables[0]["key"]
        logger.info("Fetched variable: %s", key)
        all_variables.extend(variables)
        url = cast(Union[str, None], data.get("next"))
        if url:
            logger.debug("Next page: %s", url)
        else:
            logger.debug("No more pages")
    logger.info("Total variables fetched: %s", len(all_variables))
    return all_variables


def export_variables(
    workspace: str,
    repo_slug: str,
    deployment_name: str,
    output_file: str,
    auth: HTTPBasicAuth,
    logger: Any
):
    """Export non-secured environment variables to a JSON file."""
    logger.info("Exporting non-secured variables numbering to %s", output_file)
    environment_uuid = get_environment_uuid(workspace, repo_slug, deployment_name, auth, logger)
    variables = get_variables(workspace, repo_slug, environment_uuid, auth, logger)
    if not variables:
        return
    export_vars: list[dict[str, object]] = []
    for var in variables:
        if not var["secured"]:
            export_vars.append({
                "key": var["key"],
                "value": var["value"],
                "secured": var["secured"]
            })
        else:
            logger.info(
                "Secured variable '%s' will not be exported. "
                "Use --export-secret-keys for a list of secure keys.",
                var['key']
            )
    logger.debug(
        "Preparing to export %s variables",
        len(export_vars)
    )
    count = len(export_vars)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(export_vars, f, indent=4)
    logger.info(
        "Non-secured variables(%s) exported to %s",
        count,
        output_file
    )


def export_all_variables(
    workspace: str,
    repo_slug: str,
    deployment_name: str,
    output_file: str,
    auth: HTTPBasicAuth,
    logger: Any
):
    """Export all environment variables to a JSON file."""
    logger.info("Exporting all variables to %s", output_file)
    environment_uuid = get_environment_uuid(workspace, repo_slug, deployment_name, auth, logger)
    variables = get_variables(workspace, repo_slug, environment_uuid, auth, logger)
    if not variables:
        return
    export_vars: list[dict[str, object]] = []
    for var in variables:
        if var["secured"]:
            export_vars.append({
                "key": var["key"],
                "value": "",
                "secured": var["secured"]
            })
        else:
            export_vars.append({
                "key": var["key"],
                "value": var["value"],
                "secured": var["secured"]
            })
    logger.debug("Preparing to export %s variables", len(export_vars))
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(export_vars, f, indent=4)
    logger.info(
        "All variables for %s exported to %s",
        deployment_name,
        output_file
    )


def export_secret_keys(
    workspace: str,
    repo_slug: str,
    deployment_name: str,
    output_file: str,
    auth: HTTPBasicAuth,
    logger: Any
):
    """Export keys of secured environment variables to a JSON file."""
    logger.info(
        "Exporting secured variable keys to %s",
        output_file
    )
    environment_uuid = get_environment_uuid(
        workspace,
        repo_slug,
        deployment_name,
        auth,
        logger
    )
    variables = get_variables(
        workspace,
        repo_slug,
        environment_uuid,
        auth,
        logger
    )
    if not variables:
        return
    secret_keys = [var["key"] for var in variables if var["secured"]]
    logger.debug(
        "Preparing to export %s secured variable keys",
        len(secret_keys)
    )
    count = len(secret_keys)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(secret_keys, f, indent=4)
    logger.info(
        "Secured variable keys(%s) exported to %s",
        count,
        output_file
    )


def update_vars(
    workspace: str,
    repo_slug: str,
    environment_uuid: str,
    existing_vars: list[dict[str, object]],
    var: dict[str, object],
    auth: HTTPBasicAuth,
    logger: Any
):
    """Function that actually calls the api to update args"""
    existing_var = next((v for v in existing_vars if v["key"] == var["key"]), None)
    if existing_var:
        logger.debug("Variable '%s' exists, updating", var['key'])
        url = (f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}/"
            f"deployments_config/environments/{environment_uuid}/variables/{existing_var['uuid']}")
        payload = {
            "key": var["key"],
            "value": var["value"],
            "secured": var["secured"],
            "environment": {
                "type": "deployment_environment",
                "uuid": environment_uuid
            }
        }
        response = requests.put(url, json=payload, auth=auth, timeout=30)
        response.raise_for_status()
        logger.info("Updated variable '%s'", var['key'])
    else:
        logger.debug("Variable '%s' does not exist, creating", var['key'])
        url = (f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}/"
               f"deployments_config/environments/{environment_uuid}/variables")
        payload = {
            "key": var["key"],
            "value": var["value"],
            "secured": var["secured"],
            "environment": {
                "type": "deployment_environment",
                "uuid": environment_uuid
            }
        }
        response = requests.post(url, json=payload, auth=auth, timeout=30)
        response.raise_for_status()
        logger.info("Created variable '%s'", var['key'])


def import_variables(
    workspace: str,
    repo_slug: str,
    deployment_name: str,
    input_file: str,
    update_all: bool,
    auth: HTTPBasicAuth,
    logger: Any
):
    """Import variables from a JSON file into Bitbucket."""
    logger.info("Importing variables from %s", input_file)
    environment_uuid = get_environment_uuid(workspace, repo_slug, deployment_name, auth, logger)
    existing_vars = get_variables(workspace, repo_slug, environment_uuid, auth, logger)
    with open(input_file, "r", encoding="utf-8") as f:
        import_vars = cast(list[dict[str, object]], json.load(f))
    logger.debug("Loaded %s variables from %s", len(import_vars), input_file)
    if update_all:
        for var in import_vars:
            update_vars(
                workspace=workspace,
                repo_slug=repo_slug,
                environment_uuid=environment_uuid,
                existing_vars=existing_vars,
                var=var,
                auth=auth,
                logger=logger
            )
    else:
        for var in import_vars:
            if var.get("secured", False):
                logger.info("Skipping secured variable '%s'", var['key'])
                continue
            update_vars(
                workspace=workspace,
                repo_slug=repo_slug,
                environment_uuid=environment_uuid,
                existing_vars=existing_vars,
                var=var,
                auth=auth,
                logger=logger
            )
    logger.info("Variable import completed")


def main(logger: Any):
    """Main function to handle the application logic."""
    main_args: argparse.Namespace = arg_parser()
    logger.info("Starting Bitbucket environment variable manager")
    logger.debug("Command-line arguments: %s", vars(main_args))

    # Load credentials
    logger.debug("Loading credentials from bitbucket.env")
    _ = load_dotenv('bitbucket.env')
    username = os.environ.get("BITBUCKET_USERNAME")
    app_password = os.environ.get("BITBUCKET_APP_PASSWORD")
    if not username or not app_password:
        logger.error("BITBUCKET_USERNAME and BITBUCKET_APP_PASSWORD must be set in bitbucket.env")
        sys.exit(1)
    auth = HTTPBasicAuth(username, app_password)
    logger.debug("Authentication credentials loaded successfully")

    try:
        if main_args.output:
            export_variables(
                workspace=main_args.workspace,
                repo_slug=main_args.repo_slug,
                deployment_name=main_args.deployment_name,
                output_file=main_args.output,
                auth=auth,
                logger=logger
            )
        elif main_args.all_vars_output:
            export_all_variables(
                workspace=main_args.workspace,
                repo_slug=main_args.repo_slug,
                deployment_name=main_args.deployment_name,
                output_file=main_args.all_vars_output,
                auth=auth,
                logger=logger
            )
        elif main_args.export_secret_keys:
            export_secret_keys(
                workspace=main_args.workspace,
                repo_slug=main_args.repo_slug,
                deployment_name=main_args.deployment_name,
                output_file=main_args.export_secret_keys,
                auth=auth,
                logger=logger
            )
        elif main_args.import_file:
            import_variables(
                workspace=main_args.workspace,
                repo_slug=main_args.repo_slug,
                deployment_name=main_args.deployment_name,
                input_file=main_args.import_file,
                auth=auth,
                update_all=False,
                logger=logger
            )
        elif main_args.import_all:
            import_variables(
                workspace=main_args.workspace,
                repo_slug=main_args.repo_slug,
                deployment_name=main_args.deployment_name,
                input_file=main_args.import_all,
                auth=auth,
                update_all=True,
                logger=logger
            )
        logger.info("Operation completed successfully")
    except requests.RequestException as e:
        logger.error("API error: %s", e)
        sys.exit(1)
    except ValueError as e:
        logger.error("Error: %s", e)
        sys.exit(1)
    except FileNotFoundError as e:
        logger.error("File error: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    parsed_args: argparse.Namespace = arg_parser()
    # Configure logging
    LEVEL = 'DEBUG' if parsed_args.verbose else 'INFO'
    WRITE_LOG = parsed_args.logfile
    log = BitbucketLogger(enable_log_file=WRITE_LOG, log_level=LEVEL).create_logger()
    # Main
    main(log)
