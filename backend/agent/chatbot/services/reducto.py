import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from reducto import AsyncReducto
from sqlalchemy.ext.asyncio import AsyncSession

load_dotenv()


class ReductoService:
    """Service for Reducto operations with pipelining support."""

    def __init__(self, db: AsyncSession):
        self.client = AsyncReducto(
            api_key=os.environ.get("REDUCTO_API_KEY"), timeout=300
        )
        self.db = db

    async def parse_document(
        self, file_path: Path, options: Optional[dict] = None
    ) -> tuple[str, str]:
        """Parse a document using Reducto with pipelining support.

        Args:
            file_path: Path to the document file
            options: Optional parsing configurations

        Returns:
            Tuple of (extracted_text, job_id) for potential pipelining
        """
        upload = await self.client.upload(file=file_path)
        parsed_result = await self.client.parse.run(
            input=upload.file_id, **(options or {})
        )

        text_blocks = []
        for chunk in parsed_result.result.chunks:
            for block in chunk.blocks:
                if block.type.lower() == "text":
                    text_blocks.append(block.content)

        extracted_text = "\n\n".join(text_blocks)
        return extracted_text, parsed_result.job_id

    async def extract_from_job(
        self, job_id: str, schema: dict, system_prompt: Optional[str] = None
    ) -> dict:
        """Extract structured data using a previous parse job_id (pipelining).

        Args:
            job_id: The job_id from a previous parse operation
            schema: JSON schema for extraction
            system_prompt: Optional prompt for extraction

        Returns:
            Extracted data matching the schema
        """
        extract_result = await self.client.extract.run(
            input=f"jobid://{job_id}",
            schema=schema,
            system_prompt=system_prompt,
        )
        return extract_result.result
