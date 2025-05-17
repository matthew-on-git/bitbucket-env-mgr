#!/usr/bin/env bash

source bitbucket.env

# Get environments example
curl -u $BITBUCKET_USERNAME:$BITBUCKET_APP_PASSWORD \
  "https://api.bitbucket.org/2.0/repositories/${shell_workspace}/${shell_repo_slug}/environments" \
  | jq

# Get variables example
curl -u $BITBUCKET_USERNAME:$BITBUCKET_APP_PASSWORD \
  "https://api.bitbucket.org/2.0/repositories/${shell_workspace}/${shell_repo_slug}/deployments_config/environments/${shell_environment_uuid}/variables?pagelen=20" \
  | jq