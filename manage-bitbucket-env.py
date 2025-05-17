#!/usr/bin/env python3

import argparse
import json
import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

#import local modules
# -- local ./helpers
from helpers.logging import Logger

def arg_parser(version="1.0"):
    """Parse arguments and execute export or import functionality."""
    parser = argparse.ArgumentParser(
        description="Manage Bitbucket deployment environment variables. Requires BITBUCKET_USERNAME and BITBUCKET_APP_PASSWORD in bitbucket.env."
    )
    parser.add_argument("-w", "--workspace", required=True, help="Bitbucket workspace")
    parser.add_argument("-r", "--repo-slug", required=True, help="Repository slug")
    parser.add_argument("-d", "--deployment-name", required=True, help="Deployment environment name")
    parser.add_argument('-l', '--logfile', help='Output a log file', action='store_true')
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-o", "--output", help="Output JSON file for exporting non-secured variables")
    group.add_argument("-a", "--all-vars-output", help="Output JSON file for exporting all variables")
    group.add_argument("-e", "--export-secret-keys", help="Output JSON file for exporting secured variable keys")
    group.add_argument("-i", "--import", dest="import_file", help="Input JSON file for importing variables")
    group.add_argument(f"--import-all", dest="import_all", help="Input JSON file for importing all variables, including secret keys")

    return parser.parse_args()

def get_environment_uuid(workspace, repo_slug, deployment_name, auth):
    """Retrieve the UUID of the specified deployment environment."""
    log.debug(f"Fetching environments for workspace {workspace}, repo {repo_slug}")
    url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}/environments"
    response = requests.get(url, auth=auth)
    response.raise_for_status()
    environments = response.json()["values"]
    log.debug(f"Received {len(environments)} environments")
    for env in environments:
        log.debug(f"Checking environment: {env['name']}")
        if env["name"] == deployment_name:
            log.info(f"Found environment '{deployment_name}' with UUID {env['uuid']}")
            return env["uuid"]
    log.error(f"Deployment environment '{deployment_name}' not found")
    raise ValueError(f"Deployment environment '{deployment_name}' not found")

def get_variables(workspace, repo_slug, environment_uuid, auth):
    """Fetch all environment variables for the given environment UUID."""
    log.debug(f"Fetching variables for repository {workspace}/{repo_slug}, environment {environment_uuid}")
    url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}/deployments_config/environments/{environment_uuid}/variables?pagelen=1"
    all_variables = []
    while url:
        log.debug(f"Requesting {url}")
        response = requests.get(url, auth=auth)
        response.raise_for_status()
        data = response.json()
        page = data.get("page", 1)
        variables = data.get("values", [])
        if not variables:
            log.info(f"No variables configured for {environment_uuid}")
            return all_variables
        size = data.get("size")
        next = data.get("next")
        pagelen = data.get("pagelen")
        key = variables[0]["key"]
        log.info(f"Fetched variable: {key}")
        all_variables.extend(variables)
        url = data.get("next")
        if url:
            log.debug(f"Next page: {url}")
        else:
            log.debug("No more pages")
    log.info(f"Total variables fetched: {len(all_variables)}")
    return all_variables

def export_variables(workspace, repo_slug, deployment_name, output_file, auth):
    """Export non-secured environment variables to a JSON file."""
    log.info(f"Exporting non-secured variables numbering to {output_file}")
    environment_uuid = get_environment_uuid(workspace, repo_slug, deployment_name, auth)
    variables = get_variables(workspace, repo_slug, environment_uuid, auth)
    if not variables:
        return
    export_vars = []
    for var in variables:
        if not var["secured"]:
            export_vars.append({"key": var["key"], "value": var["value"], "secured": False})
        else:
            log.info(f"Secured variable '{var['key']}' will not be exported. Use --export-secret-keys for a list of secure keys.")
    log.debug(f"Preparing to export {len(export_vars)} variables")
    count = len(export_vars)
    with open(output_file, "w") as f:
        json.dump(export_vars, f, indent=4)
    log.info(f"Non-secured variables({count}) exported to {output_file}")
    
def export_all_variables(workspace, repo_slug, deployment_name, output_file, auth):
    """Export all environment variables to a JSON file."""
    log.info(f"Exporting all variables to {output_file}")
    environment_uuid = get_environment_uuid(workspace, repo_slug, deployment_name, auth)
    variables = get_variables(workspace, repo_slug, environment_uuid, auth)
    if not variables:
        return
    export_vars = []
    for var in variables:
        if var["secured"]:
            export_vars.append({"key": var["key"], "value": "", "secured": True})
        else:
            export_vars.append({"key": var["key"], "value": var["value"], "secured": False})
    log.debug(f"Preparing to export {len(export_vars)} variables")
    with open(output_file, "w") as f:
        json.dump(export_vars, f, indent=4)
    log.info(f"All variables for {deployment_name} exported to {output_file}")

def export_secret_keys(workspace, repo_slug, deployment_name, output_file, auth):
    """Export keys of secured environment variables to a JSON file."""
    log.info(f"Exporting secured variable keys to {output_file}")
    environment_uuid = get_environment_uuid(workspace, repo_slug, deployment_name, auth)
    variables = get_variables(workspace, repo_slug, environment_uuid, auth)
    if not variables:
        return
    secret_keys = [var["key"] for var in variables if var["secured"]]
    log.debug(f"Preparing to export {len(secret_keys)} secured variable keys")
    count = len(secret_keys)
    with open(output_file, "w") as f:
        json.dump(secret_keys, f, indent=4)
    log.info(f"Secured variable keys({count}) exported to {output_file}")

def update_vars(workspace, repo_slug, environment_uuid, existing_vars, var, auth):
    existing_var = next((v for v in existing_vars if v["key"] == var["key"]), None)
    if existing_var:
        log.debug(f"Variable '{var['key']}' exists, updating")
        url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}/deployments_config/environments/{environment_uuid}/variables/{existing_var['uuid']}"
        payload = {
            "key": var["key"],
            "value": var["value"],
            "secured": False,
            "environment": {
                "type": "deployment_environment",
                "uuid": environment_uuid
            }
        }
        response = requests.put(url, json=payload, auth=auth)
        response.raise_for_status()
        log.info(f"Updated variable '{var['key']}'")
    else:
        log.debug(f"Variable '{var['key']}' does not exist, creating")
        url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}/deployments_config/environments/{environment_uuid}/variables"
        payload = {
            "key": var["key"],
            "value": var["value"],
            "secured": False,
            "environment": {
                "type": "deployment_environment",
                "uuid": environment_uuid
            }
        }
        response = requests.post(url, json=payload, auth=auth)
        response.raise_for_status()
        log.info(f"Created variable '{var['key']}'")

def import_variables(workspace, repo_slug, deployment_name, input_file, update_all, auth):
    """Import variables from a JSON file into Bitbucket."""
    log.info(f"Importing variables from {input_file}")
    environment_uuid = get_environment_uuid(workspace, repo_slug, deployment_name, auth)
    existing_vars = get_variables(workspace, repo_slug, environment_uuid, auth)
    with open(input_file, "r") as f:
        import_vars = json.load(f)
    log.debug(f"Loaded {len(import_vars)} variables from {input_file}")
    if update_all:
        for var in import_vars:
            update_vars(workspace=workspace, repo_slug=repo_slug, environment_uuid=environment_uuid, existing_vars=existing_vars, var=var, auth=auth)
    else:
        for var in import_vars:
            if var.get("secured", False):
                log.info(f"Skipping secured variable '{var['key']}'")
                continue
            update_vars(workspace=workspace, repo_slug=repo_slug, environment_uuid=environment_uuid, existing_vars=existing_vars, var=var, auth=auth)
    log.info("Variable import completed")

def main():
    log.info("Starting Bitbucket environment variable manager")
    log.debug(f"Command-line arguments: {vars(args)}")

    # Load credentials
    log.debug("Loading credentials from bitbucket.env")
    load_dotenv('bitbucket.env')
    username = os.environ.get("BITBUCKET_USERNAME")
    app_password = os.environ.get("BITBUCKET_APP_PASSWORD")
    if not username or not app_password:
        log.error("BITBUCKET_USERNAME and BITBUCKET_APP_PASSWORD must be set in bitbucket.env")
        exit(1)
    auth = HTTPBasicAuth(username, app_password)
    log.debug("Authentication credentials loaded successfully")

    try:
        if args.output:
            export_variables(workspace=args.workspace, repo_slug=args.repo_slug, deployment_name=args.deployment_name, output_file=args.output, auth=auth)
        elif args.all_vars_output:
            export_all_variables(workspace=args.workspace, repo_slug=args.repo_slug, deployment_name=args.deployment_name, output_file=args.all_vars_output, auth=auth)
        elif args.export_secret_keys:
            export_secret_keys(workspace=args.workspace, repo_slug=args.repo_slug, deployment_name=args.deployment_name, output_file=args.export_secret_keys, auth=auth)
        elif args.import_file:
            import_variables(workspace=args.workspace, repo_slug=args.repo_slug, deployment_name=args.deployment_name, input_file=args.import_file, auth=auth, update_all=False)
        elif args.import_all:
            import_variables(workspace=args.workspace, repo_slug=args.repo_slug, deployment_name=args.deployment_name, input_file=args.import_all, auth=auth, update_all=True)
        log.info("Operation completed successfully")
    except requests.RequestException as e:
        log.error(f"API error: {e}")
        exit(1)
    except ValueError as e:
        log.error(f"Error: {e}")
        exit(1)
    except FileNotFoundError as e:
        log.error(f"File error: {e}")
        exit(1)

if __name__ == "__main__":
    # Args
    args = arg_parser()

    # Configure logging
    level='DEBUG' if args.verbose else 'INFO'
    writeLog=True if args.logfile else False
    log = Logger(enable_log_file=writeLog, log_level=level).create_logger()
    
    # Main
    main()