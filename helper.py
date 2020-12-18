import os
from dotenv import load_dotenv
from slack_bolt import App


class Helper:

    @staticmethod
    def loadEnvKey(
            name
    ):
        """
        Static method to load API keys from environment variables.
        :@param name: string, default=None, required
            Name of environment variable to load.
        :@return envKey: string
            Actual API key or configuration value.
        """

        load_dotenv()

        envKey = (
            os.environ.get(name)
        )
        return envKey


