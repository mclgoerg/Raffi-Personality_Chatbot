import os
from dotenv import load_dotenv


class Helper:

    @staticmethod
    def loadEnvKey(
            name
    ):
        """
        Method to load API keys from environment variables.
        :@param name: string
            Name of environment variable to load.
        :@return envKey: string
            Actual API key or configuration value.
        """

        load_dotenv()

        envKey = (
            os.environ.get(name)
        )
        return envKey


