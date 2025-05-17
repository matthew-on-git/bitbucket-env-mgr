# Bitbucket Environment Variable Manager

## Description
This script allows you to manage Bitbucket deployment environment variables. It can export non-secured variables, export all variables (with secured ones having empty values), export the keys of secured variables, and import variables back into Bitbucket for a specified deployment environment.

## Features
- **Export Non-Secured Variables**: Retrieves non-secured environment variables and saves them to a JSON file.
- **Export All Variables**: Retrieves all environment variables (non-secured and secured) and saves them to a JSON file, with secured variables having an empty value.
- **Export Secured Variable Keys**: Retrieves the keys (names) of secured (secret) variables and saves them to a JSON file.
- **Import Non-Secured Variables**: Reads non-secured variables from a JSON file and sets them in Bitbucket, updating existing variables or creating new ones as needed.
- **Import All Variables**: Reads all variables from a JSON file, including secured ones, and attempts to set them in Bitbucket. Note that secured variables may require additional handling.

## Requirements
- Python 3.x
- `coloredlogs` library (`pip install coloredlogs`)
- `requests` library (`pip install requests`)
- `python-dotenv` library (`pip install python-dotenv`)
- Bitbucket account with appropriate permissions
- `bitbucket.env` file with Bitbucket credentials

## Setup
1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create `bitbucket.env` file:**
   Create a file named `bitbucket.env` in the same directory as the script with the following content:
   ```
   BITBUCKET_USERNAME=your_username
   BITBUCKET_APP_PASSWORD=your_app_password
   ```
   Replace `your_username` and `your_app_password` with your actual Bitbucket credentials.

   Your Bitbucket username is listed under Bitbucket profile settings on your [Bitbucket Personal settings page](https://bitbucket.org/account/settings/).   

   To generate an app password in Bitbucket:
   1. Go to your Bitbucket account settings.
   2. Under "Access management," select "App passwords."
   3. Click "Create app password."
   4. Give it a label and select the necessary permissions (at least "Pipelines: Write").
   5. Click "Create" and copy the generated password.

## Usage
### Command-Line Arguments
- `-w, --workspace`: Bitbucket workspace (required)
- `-r, --repo-slug`: Repository slug (required)
- `-d, --deployment-name`: Deployment environment name (required)
- `-l, --logfile`: Output a log file
- `-v, --verbose`: Enable debug logging

Mutually exclusive options (one required):
- `-o, --output`: Output JSON file for exporting non-secured variables
- `-a, --all-vars-output`: Output JSON file for exporting all variables
- `-e, --export-secret-keys`: Output JSON file for exporting secured variable keys
- `-i, --import`: Input JSON file for importing non-secured variables
- `--import-all`: Input JSON file for importing all variables, including secured ones

### Examples
#### Export Non-Secured Variables
To export non-secured variables from the "development" environment to `variables.json`:
```
./manage-bitbucket-env.py -w your_workspace -r your_repo -d development -o variables.json
```

#### Export All Variables
To export all variables from the "development" environment to `all_variables.json`:
```
./manage-bitbucket-env.py -w your_workspace -r your_repo -d development -a all_variables.json
```

#### Export Secured Variable Keys
To export the keys of secured variables from the "development" environment to `secret_keys.json`:
```
./manage-bitbucket-env.py -w your_workspace -r your_repo -d development -e secret_keys.json
```

#### Import Non-Secured Variables
To import non-secured variables from `variables.json` to the "development" environment:
```
./manage-bitbucket-env.py -w your_workspace -r your_repo -d development -i variables.json
```

#### Import All Variables
To import all variables from `all_variables.json` to the "development" environment:
```
./manage-bitbucket-env.py -w your_workspace -r your_repo -d development --import-all all_variables.json
```

## JSON File Formats
### For Non-Secured Variables
The JSON file should be an array of objects, each containing `key`, `value`, and `secured` (set to `false`):
```json
[
    {
        "key": "VAR1",
        "value": "value1",
        "secured": false
    },
    {
        "key": "VAR2",
        "value": "value2",
        "secured": false
    }
]
```

### For All Variables
The JSON file will include all variables, with secured variables having an empty value:
```json
[
    {
        "key": "VAR1",
        "value": "value1",
        "secured": false
    },
    {
        "key": "SECRET_VAR",
        "value": "",
        "secured": true
    }
]
```

### For Secured Variable Keys
The JSON file will be a simple array of strings representing the keys:
```json
[
    "SECRET_KEY_1",
    "SECRET_KEY_2"
]
```

## Logging
- Use the `-v` or `--verbose` flag to enable debug logging.
- Use the `-l` or `--logfile` flag to output logs to a file.

## Notes
- Secured variables' values cannot be exported or imported due to API limitations.
- When exporting all variables, secured variables will have an empty value in the JSON file.
- When importing all variables, secured variables may require additional handling or manual intervention.
- Ensure that the `bitbucket.env` file is kept secure and not committed to version control.
- The script assumes that `bitbucket.env` is in the same directory as the script.

## Limitations
- Imported values cannot be empty
- The script can only handle values for non-secured variables for export and import of values. Secure variables will have an empty value
- Secured variables must be managed manually in each environment via the Bitbucket UI or through other means.