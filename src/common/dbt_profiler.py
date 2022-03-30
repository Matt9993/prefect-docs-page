# This class is responsible for creating a dbt profile file
# during runtime based on the provided flow Parameter/Secret

import os, shutil
import re
import boto3
from pathlib import Path
from prefect import Task
from prefect.client import Secret

from prefect.utilities.aws import get_boto_client
from prefect.utilities.tasks import defaults_from_attrs


DBT_ROOT = "DBT"
my_path = os.path.dirname(os.path.abspath(__file__))
current = os.path.join(my_path, "../.dbt")
DBT_TMP_FOLDER = f"{current}/"
PROFILE_ROOT_FOLDER = f"{current}/"

LIST_OF_FILES = ["catalog.json", "index.html", "manifest.json", "run_results.json"]


class DbtProfiler(Task):
    """
    This task creates a dbt profile file for you based on the connection
    details dictionary what you should provide.

    Args:
        - profile_infos: a dictionary containing all the connection infos
    """

    def __init__(self, profile_infos: dict = None, **kwargs):
        self.profile_infos = profile_infos
        super().__init__(**kwargs)

    @defaults_from_attrs("profile_infos")
    def run(self, profile_infos: dict = None):
        """
        Task run method.

        Args:
            - profile_infos: a dictionary containing all the connection infos
        """
        self.profile_parent_path = (
            PROFILE_ROOT_FOLDER  # '{}{}'.format(PROFILE_ROOT_FOLDER, str(uuid.uuid4()))
        )
        self.profile_file_name = "profiles.yml"
        self.profile = profile_infos.get("profile")
        self.env = profile_infos.get("env")
        self.warehouse = profile_infos.get("warehouse")
        self.database = profile_infos.get("database")
        self.account = profile_infos.get("account")
        self.user = profile_infos.get("user")
        self.password = profile_infos.get("password")
        self.schema = profile_infos.get("schema")
        self.role = profile_infos.get("role")
        self.write_profile_file()

    def get_profile_parent_path(self):
        return self.profile_parent_path

    def get_profile_file_path(self):
        return os.path.join(self.profile_parent_path, self.profile_file_name)

    def write_profile_file(self):
        Path(self.profile_parent_path).mkdir(parents=True, exist_ok=True)
        with open(self.get_profile_file_path(), "w+") as f:
            f.write(self.get_profile())
        f.close()

    def read_profile_file(self):
        with open(self.get_profile_file_path(), "r") as f:
            profile_file = f.read()
        return profile_file

    def get_profile(self):
        return """
{profile}:
  outputs:
    {env}:
      type: snowflake
      account: {account}
      user: {user}
      password: {password}
      role: {role}
      database: {database}
      warehouse: {warehouse}
      schema: {schema}
      threads: 1
      client_session_keep_alive: False
  target: {env}
            """.format(
            profile=self.profile,
            env=self.env,
            warehouse=self.warehouse,
            database=self.database,
            account=self.account,
            user=self.user,
            password=self.password,
            schema=self.schema,
            role=self.role,
        )


class CleanUpProfile(Task):
    """
    Deletes the generated profile file to not leave any credentials
    after run finished.

    Args:
        - profile_parent_path (str): _description_
    """

    def __init__(self, profile_parent_path: str = None, **kwargs):
        self.profile_parent_path = profile_parent_path
        super().__init__(**kwargs)

    @defaults_from_attrs("profile_parent_path")
    def run(self, profile_parent_path: str = None):
        """
        The run method of the CleanUpProfile Custom Task.

        Args:
            - profile_parent_path (str, optional): _description_. Defaults to None.
        """
        try:
            shutil.rmtree(profile_parent_path)
            print("#########  DELETED PROFILE FILE  ###############")
        except Exception as e:
            print(
                "Problem removing temporary profiles.yml file and"
                " parent directory {}:".format(profile_parent_path)
            )
            print(e)


class PutDocsToS3(Task):
    """
    This custom Task is uploading the generated docs into a specified
    S3 folder where the dbt docs would be hosted.

    Args:
        - project_folder (str): The name of the dbt project
    """

    def __init__(self, project_folder: str = None, **kwargs):
        self.project_folder = project_folder
        super().__init__(**kwargs)

    @defaults_from_attrs("project_folder")
    def run(self, project_folder: str = None):
        """
        The actual run function of the PutDocsToS3 Custom Task.

        Args:
            - project_folder (str): The name of the dbt project
        """
        bucket_name = Secret("s3_bucket_name").get()
        for each in LIST_OF_FILES:
            self.copy_from_local_to(
                project_folder + "/target/" + each, bucket_name + each
            )
            self.logger.info(
                "{} object is copied".format(project_folder + "/target/" + each)
            )

    def _get_bucket_name_from_path(self, path):
        res = re.findall("s3:\/\/([a-zA-Z0-9_-]*)\/.*", path)
        if res is not None:
            return res[0]
        else:
            return None

    def _get_folder_name_from_path(self, path):
        res = re.findall("s3:\/\/[a-zA-Z0-9_-]*\/(.*)", path)
        if res is not None:
            return res[0]
        else:
            return None

    def save_object_as_file(self, file_object, path, content_type="string"):
        client = boto3.client(
            "s3",
            aws_access_key_id=Secret("aws_access_key_id").get(),
            aws_secret_access_key=Secret("aws_secret_access_key").get(),
        )
        bucket = self._get_bucket_name_from_path(path)
        file = self._get_folder_name_from_path(path)
        if type(file_object) != bytes:
            file_object = file_object.encode()
        client.put_object(
            Body=file_object, Bucket=bucket, Key=file, ContentType=content_type
        )

    def copy_from_local_to(self, localpath, targetpath):
        with open(localpath, "rb") as data:
            file_content = data.read()
        data.close()
        if ".html" in targetpath:
            self.save_object_as_file(file_content, targetpath, content_type="text/html")
        else:
            self.save_object_as_file(file_content, targetpath)
