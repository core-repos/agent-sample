"""
Database connection management for LangChain
"""
import json
from typing import Optional
from sqlalchemy import create_engine
from langchain_community.utilities import SQLDatabase
from google.cloud import bigquery
from google.oauth2 import service_account
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

class BigQueryConnection:
    """Manages BigQuery database connections"""
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        dataset_id: Optional[str] = None,
        credentials_json: Optional[str] = None
    ):
        self.project_id = project_id or settings.gcp_project_id
        self.dataset_id = dataset_id or settings.bq_dataset
        self.credentials_json = credentials_json or settings.gcp_service_account_key
        self._engine = None
        self._database = None
        self._client = None
        
    def get_credentials(self):
        """Get Google Cloud credentials"""
        if self.credentials_json:
            return service_account.Credentials.from_service_account_info(
                json.loads(self.credentials_json)
            )
        return None
    
    def get_bigquery_client(self) -> bigquery.Client:
        """Get BigQuery client instance"""
        if not self._client:
            credentials = self.get_credentials()
            self._client = bigquery.Client(
                credentials=credentials,
                project=self.project_id
            )
            logger.info(f"Created BigQuery client for project: {self.project_id}")
        return self._client
    
    def get_sqlalchemy_engine(self):
        """Get SQLAlchemy engine for BigQuery"""
        if not self._engine:
            credentials = self.get_credentials()
            
            if credentials:
                self._engine = create_engine(
                    f"bigquery://{self.project_id}/{self.dataset_id}",
                    credentials_info=json.loads(self.credentials_json)
                )
            else:
                self._engine = create_engine(
                    f"bigquery://{self.project_id}/{self.dataset_id}"
                )
            
            logger.info(f"Created SQLAlchemy engine for {self.project_id}.{self.dataset_id}")
        return self._engine
    
    def get_langchain_database(self) -> SQLDatabase:
        """Get LangChain SQLDatabase instance"""
        if not self._database:
            engine = self.get_sqlalchemy_engine()
            self._database = SQLDatabase(engine)
            logger.info("Created LangChain SQLDatabase instance")
        return self._database
    
    def test_connection(self) -> bool:
        """Test the database connection"""
        try:
            db = self.get_langchain_database()
            # Try to get table info as a connection test
            db.get_table_info()
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def get_connection(self):
        """Get SQLAlchemy connection for pandas/direct SQL operations"""
        engine = self.get_sqlalchemy_engine()
        return engine

    def get_dataset_info(self) -> dict:
        """Get information about the dataset"""
        client = self.get_bigquery_client()
        dataset_ref = client.dataset(self.dataset_id)
        dataset = client.get_dataset(dataset_ref)

        tables = list(client.list_tables(dataset))

        return {
            "project_id": self.project_id,
            "dataset_id": self.dataset_id,
            "location": dataset.location,
            "created": dataset.created,
            "tables": [table.table_id for table in tables],
            "table_count": len(tables)
        }