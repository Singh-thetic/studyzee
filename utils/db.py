"""
Database client wrapper for Supabase interactions.

Provides a centralized interface for all database operations with proper error handling.
"""

import logging
from typing import Any, Optional
from supabase import create_client, Client

logger = logging.getLogger(__name__)


class DatabaseClient:
    """Wrapper for Supabase client with error handling."""

    def __init__(self, url: str, key: str) -> None:
        """
        Initialize Supabase client.

        Args:
            url: Supabase project URL.
            key: Supabase API key.

        Raises:
            ValueError: If URL or key is empty.
        """
        if not url or not key:
            raise ValueError("Supabase URL and key must not be empty")
        self.client: Client = create_client(url, key)

    def insert(self, table: str, data: dict) -> Optional[dict]:
        """
        Insert a single record into a table.

        Args:
            table: Table name.
            data: Record data as dictionary.

        Returns:
            Inserted record data or None if failed.
        """
        try:
            response = self.client.table(table).insert(data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Insert failed for table {table}: {str(e)}")
            return None

    def insert_many(self, table: str, data: list[dict]) -> bool:
        """
        Insert multiple records into a table.

        Args:
            table: Table name.
            data: List of record dictionaries.

        Returns:
            True if successful, False otherwise.
        """
        try:
            response = self.client.table(table).insert(data).execute()
            return bool(response.data)
        except Exception as e:
            logger.error(f"Batch insert failed for table {table}: {str(e)}")
            return False

    def select(self, table: str, columns: str = "*") -> Optional[list[dict]]:
        """
        Select all records from a table.

        Args:
            table: Table name.
            columns: Comma-separated column names (default: all columns).

        Returns:
            List of records or None if failed.
        """
        try:
            response = self.client.table(table).select(columns).execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Select failed for table {table}: {str(e)}")
            return None

    def select_where(
        self, table: str, column: str, value: Any, columns: str = "*"
    ) -> Optional[list[dict]]:
        """
        Select records matching a condition.

        Args:
            table: Table name.
            column: Column to filter on.
            value: Value to match.
            columns: Comma-separated column names (default: all columns).

        Returns:
            List of matching records or None if failed.
        """
        try:
            response = (
                self.client.table(table)
                .select(columns)
                .eq(column, value)
                .execute()
            )
            return response.data if response.data else []
        except Exception as e:
            logger.error(
                f"Select where failed for table {table}, {column}={value}: {str(e)}"
            )
            return None

    def select_one(self, table: str, column: str, value: Any) -> Optional[dict]:
        """
        Select a single record matching a condition.

        Args:
            table: Table name.
            column: Column to filter on.
            value: Value to match.

        Returns:
            Single record or None if not found or failed.
        """
        try:
            response = (
                self.client.table(table)
                .select("*")
                .eq(column, value)
                .maybe_single()
                .execute()
            )
            return response.data
        except Exception as e:
            logger.error(
                f"Select one failed for table {table}, {column}={value}: {str(e)}"
            )
            return None

    def update(self, table: str, column: str, value: Any, data: dict) -> bool:
        """
        Update records matching a condition.

        Args:
            table: Table name.
            column: Column to filter on.
            value: Value to match.
            data: Dictionary of fields to update.

        Returns:
            True if successful, False otherwise.
        """
        try:
            response = (
                self.client.table(table)
                .update(data)
                .eq(column, value)
                .execute()
            )
            return bool(response.data)
        except Exception as e:
            logger.error(
                f"Update failed for table {table}, {column}={value}: {str(e)}"
            )
            return False

    def delete(self, table: str, column: str, value: Any) -> bool:
        """
        Delete records matching a condition.

        Args:
            table: Table name.
            column: Column to filter on.
            value: Value to match.

        Returns:
            True if successful, False otherwise.
        """
        try:
            response = (
                self.client.table(table)
                .delete()
                .eq(column, value)
                .execute()
            )
            return True
        except Exception as e:
            logger.error(
                f"Delete failed for table {table}, {column}={value}: {str(e)}"
            )
            return False

    def storage_upload(
        self, bucket: str, path: str, file_data: bytes
    ) -> Optional[str]:
        """
        Upload file to Supabase storage.

        Args:
            bucket: Storage bucket name.
            path: File path in bucket.
            file_data: File content as bytes.

        Returns:
            Public URL of uploaded file or None if failed.
        """
        try:
            response = (
                self.client.storage.from_(bucket)
                .upload(path, file_data, {"content_type": "application/octet-stream"})
            )
            if hasattr(response, "model_dump"):
                res_dict = response.model_dump()
            else:
                res_dict = response

            if isinstance(res_dict, dict) and res_dict.get("error"):
                logger.error(f"Storage upload failed: {res_dict['error']}")
                return None

            # Construct public URL
            base_url = self.client.supabase_url
            return f"{base_url}/storage/v1/object/public/{bucket}/{path}"
        except Exception as e:
            logger.error(f"Storage upload failed: {str(e)}")
            return None
