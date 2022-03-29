from prefect import Flow, Parameter, task
from prefect.client import Secret
from prefect.tasks.dbt.dbt import DbtShellTask
from prefect.engine.state import Failed, Success
from prefect.utilities.notifications import slack_notifier
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from src.common.dbt_profiler import DbtProfiler, CleanUpProfile, PutDocsToS3

from src.common.util import extract_value

# add some "global" vars
handler = slack_notifier(only_states=[Failed, Success])
my_path = os.path.dirname(os.path.abspath(__file__))
PROFILES_DIR = os.path.join(my_path, "../.dbt")


# get s3 website endpoint
web_endpoint = "ds"  # Secret("s3_dbt_docs_endpoint").get()

# init the custom tasks
profiler = DbtProfiler()

s3_task = PutDocsToS3()
s3_task.state_handlers = [handler]

cleaner = CleanUpProfile()
cleaner.name = "Profile clean up task"
cleaner.state_handlers = [handler]

# get dbt profile from secret and destruct secret
secret = {
    "account": "",
    "user": "",
    "password": "",
    "role": "",
    "warehouse": "",
    "schema": "",
    "profile": "",
    "environment": "",
    "helper_script": "helper script",
    "database": "",
}
conf_info = secret  # Secret("DBT--PROFILE-DEV").get()
account = conf_info["account"]
user = conf_info["user"]
password = conf_info["password"]
role = conf_info["role"]
warehouse = conf_info["warehouse"]
schema = conf_info["schema"]
profile = conf_info["profile"]
env = conf_info["environment"]
helper = conf_info["helper_script"]
db = conf_info["database"]


dbt = DbtShellTask(
    return_all=True,
    profile_name=profile,
    environment=env,
    profiles_dir=PROFILES_DIR,
    overwrite_profiles=True,
    log_stdout=True,
    helper_script=helper,
    log_stderr=True,
    dbt_kwargs={
        "type": "snowflake",
        "account": account,
        # User/password auth
        "user": user,
        "password": password,
        "role": role,
        "database": db,
        "warehouse": warehouse,
        "schema": schema,
        "threads": 4,
        "client_session_keep_alive": False,
    },
)
dbt.stream_output = True

profile_info = {
    "profile": profile,
    "env": env,
    "warehouse": warehouse,
    "db": db,
    "schema": schema,
    "user": user,
    "password": password,
    "role": role,
    "account": account,
}


with Flow("dbt daily run flow") as flow:

    # run the daily dbt tasks, generate docs, S3 docs, custom artifact and clean up
    profiler(profile_info).set_downstream(
        dbt(command="dbt run").set_downstream(
            dbt(command="dbt docs generate").set_downstream(
                s3_task(helper.split(" ")[1]).set_downstream(
                    cleaner(profile_parent_path=PROFILES_DIR)
                )
            )
        )
    )
