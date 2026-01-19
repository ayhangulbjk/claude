import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Azure OpenAI Configuration
    AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
    AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
    AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4')
    AZURE_OPENAI_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview')

    # Oracle Database Configuration
    ORACLE_HOST = os.getenv('ORACLE_HOST')
    ORACLE_PORT = os.getenv('ORACLE_PORT', '1521')
    ORACLE_SERVICE_NAME = os.getenv('ORACLE_SERVICE_NAME')
    ORACLE_USER = os.getenv('ORACLE_USER')
    ORACLE_PASSWORD = os.getenv('ORACLE_PASSWORD')

    @property
    def oracle_dsn(self):
        return f"{self.ORACLE_HOST}:{self.ORACLE_PORT}/{self.ORACLE_SERVICE_NAME}"
