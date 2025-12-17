"""Script to ingest the test document for RAG testing."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from chatbot.database import AsyncSessionLocal
from chatbot.models import Document, DocumentSection
from chatbot.services.ingestion import IngestionService
from chatbot.services.reducto import ReductoService
from sqlalchemy import func, select


async def ingest_all_pg_essays():
    """Ingest all PDF files from pg_essays directory."""
    essays_dir = Path("pg_essays")

    if not essays_dir.exists():
        print(f"❌ Error: Directory not found at {essays_dir.absolute()}")
        return

    # Get all PDF files
    all_pdf_files = sorted(essays_dir.glob("*.pdf"))

    if not all_pdf_files:
        print("❌ No PDF files found")
        return

    print(f"📚 Found {len(all_pdf_files)} total PDF files in {essays_dir}")
    print("-" * 80)

    async with AsyncSessionLocal() as db:
        # Query existing documents from database
        result = await db.execute(select(Document.filename))
        existing_filenames = {row[0] for row in result.all()}

        print(f"📊 Already in database: {len(existing_filenames)} documents")

        if existing_filenames:
            print("   Existing files:")
            for filename in sorted(existing_filenames):
                print(f"   - {filename}")

        # Filter out already ingested files
        pdf_files = [f for f in all_pdf_files if f.name not in existing_filenames]

        if not pdf_files:
            print("\n✅ All documents already ingested!")
            return

        print(f"\n🔄 Need to ingest: {len(pdf_files)} documents")
        print("-" * 80)

        reducto_service = ReductoService(db)
        ingestion_service = IngestionService(db, reducto_service)

        success_count = 0
        failed_count = 0
        skipped_count = len(existing_filenames)

        for idx, pdf_path in enumerate(pdf_files, 1):
            print(f"\n[{idx}/{len(pdf_files)}] 📄 Ingesting: {pdf_path.name}")

            try:
                document = await ingestion_service.ingest_document(pdf_path)

                # Count sections
                result = await db.execute(
                    select(func.count())
                    .select_from(DocumentSection)
                    .where(DocumentSection.document_id == document.id)
                )
                section_count = result.scalar()

                print(f"✅ Success!")
                print(f"   - Document ID: {document.id}")
                print(f"   - Sections: {section_count}")
                success_count += 1

            except Exception as e:
                print(f"❌ Failed: {e}")
                failed_count += 1

        print("\n" + "=" * 80)
        print(f"📊 Final Summary:")
        print(f"   - Total files: {len(all_pdf_files)}")
        print(f"   - Already in DB: {skipped_count}")
        print(f"   - Newly ingested: {success_count}")
        print(f"   - Failed: {failed_count}")


if __name__ == "__main__":
    asyncio.run(ingest_all_pg_essays())
