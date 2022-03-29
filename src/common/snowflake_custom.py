#
# This task is responsible for creating a Snowflake connection
# Needs account, username, password and warehouse as secret
# Requires 1 argument an SQL query

from prefect import Task
from prefect.utilities.tasks import defaults_from_attrs

from snowflake import connector


class SFExecutor(Task):
    """
        Custom Snowflake execute query Task

    Args:
        - credentials (dict): connection information
    """

    def __init__(self, credentials: dict = None, **kwargs):
        self.credentials = credentials
        super().__init__(**kwargs)

    @defaults_from_attrs("credentials")
    def run(self, credentials: dict, query: str, **kwargs) -> list:
        """
            Executing an SQL query in Snowflake

        Args:
            credentials (dict): connection informations
            query (str): SQL query to be executed

        Returns:
            list: list containing the result set
        """

        sf_client = connector.connect(
            user=credentials.get("SNOWFLAKE_SECRET_USERNAME", None),
            account=credentials.get("SNOWFLAKE_SECRET_ACCOUNT", None),
            password=credentials.get("SNOWFLAKE_SECRET_PASSWORD", None),
            warehouse=credentials.get("SNOWFLAKE_SECRET_WAREHOUSE", None),
            **kwargs
        )

        with sf_client.cursor() as cur:
            res = cur.execute(query).fetchall()
        cur.close()
        return res
