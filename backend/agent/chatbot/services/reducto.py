import os
from pathlib import Path

from dotenv import load_dotenv
from reducto import Reducto
from sqlalchemy.ext.asyncio import AsyncSession

load_dotenv()


class ReductoService:
    """Service for Reducto operations."""

    def __init__(self, db: AsyncSession):
        self.client = Reducto(api_key=os.environ.get("REDUCTO_API_KEY"), timeout=300)
        self.db = db

    async def upload_document(self):
        """Upload a document to Reducto."""
        file_path = (
            Path(__file__).parent.parent.parent / "pg_essays" / "credentials.pdf"
        )
        upload = self.client.upload(file=file_path)

        parsed_result = self.client.parse.run(input=upload)

        print(parsed_result.to_json())

        return parsed_result.to_json()
