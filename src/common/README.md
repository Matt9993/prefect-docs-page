# This folder contains the customs Tasks used by the pipelines

### Slack notifier (state handler)

The Slack notifer custom task is basically Prefects own implementation updated
to make sure you can easily configure it and use it locally and or on any platform.
This task needs a Slack webhook url to be able to successfully send slack notification.
The webhook url is stored in as an ENV variable that is coming from a Kubernetes secret.

You can easily add this state handler to any Prefect flow and task.
Usage:
```python
from src.common.slack_not import slack_notifier
from prefect.engine.state import Failed, Success

# state handler for Slack notification
handler = slack_notifier(only_states=[Failed, Success])

example_task = ExampleTask()
example_task.state_handlers = [handler]
```

### Snowflake task logger (state handler)

This custom task is based on the logic of the Slack notifier which means it is like a wrapper
that is checking the status of the specified Task, and logs the most essential informations about
the Task.
Requirement for this is the custom Snowflake Task, and an existing LOG table created with the right
permissions. Since this state handler is using Snowflake to store the logs the Snowflake custom task
should be initialised with the credentials. Credentials retrieved from an Azure Key Vault secret.

Example usage:
```python
from src.common.snowflake_state_handler import snowflake_logger
from prefect.engine.state import Failed, Success

sf_handler = snowflake_logger(only_states=[Failed, Success])

example_task = ExampleTask()
example_task.state_handlers = [sf_handler]
```

For the Snowflake table log here is the query:
```text
-- create LOG database
CREATE SCHEMA RAW_DEV.LOG;


-- create log table
CREATE TABLE RAW_DEV.LOG.PIPELINE_LOGS (
    FLOW_ID VARCHAR,
    FLOW_NAME VARCHAR, 
    TASK_NAME VARCHAR, 
    STATE VARCHAR, 
    MESSAGE VARCHAR, 
    INGESTED_AT TIMESTAMP_TZ
)


-- if we need to give permissions to a different role
grant usage on database "RAW_DEV" to role {ROLE_NAME};
grant usage on schema "RAW_DEV"."LOG" to role {ROLE_NAME};
grant select on all tables in schema "RAW_DEV"."LOG" to {ROLE_NAME};
```


###Snowflake Custom Executor Task

This task is used to interact with the Snowflake Data Warehouse.
It need a dictionary with the Snowflake credentials, account name, warehouse.
Secret is stored in Azure Key Vault.
Usage:
```python
import json
from src.common.snowflake_custom import SFExecutor
from src.common.azure_key_vault_task import KeyVaultTask

# get the secret
sf_secret = KeyVaultTask().run(secret_name="snowflake-secret")
sf_secret_dict = json.loads(sf_secret)

sql_query = "SELECT col FROM DB.SCHEMA.TABLE;"

sf_task = SFExecutor()
sf_res = sf_task(credentials=sf_secret, query=sql_query)
```


###Azure Blog Storage Upload and Delete

So every pipeline needs a temporary staging area that we use as external tables from the
ingestion into Snowflake.
For that we have 2 Tasks, 1 for uploading a file into Azure Blob Storage and 1 for deleting.

Usage:
```python
import os
from src.common.azure_blob_upload_task import BlobStorageUpload
from src.common.azure_blob_delete import BlobStorageDelete
from src.common.azure_key_vault_task import KeyVaultTask
from src.common.extract_azure_secret_task import ExtractKeyVaultSecretByName

blob_name = "test.txt"
container = "test-files"

kv_azure = KeyVaultTask()
extract_secret = ExtractKeyVaultSecretByName()

# get secret variable name injected to pod as secret
secret = kv_azure(secret_name=os.getenv("BLOB_SECRET_NAME", None))
blob_connection_dict = extract_secret(secret)

upload = BlobStorageUpload()
upload_task = upload(
        blob_name=blob_name,
        data="test-content",
        blob_secret_dict=blob_connection_dict
    )

delete = BlobStorageDelete()
delete_task = delete(
        blob_name=blob_name,
        blob_secret_dict=blob_connection_dict
    )
```