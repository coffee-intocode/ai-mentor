"""Script to initialize the database with initial migration."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from chatbot.database import init_db


async def main():
    """Initialize database tables."""
    print("Initializing database...")
    try:
        await init_db()
        print("✓ Database initialized successfully!")
    except Exception as error:
        print(f"✗ Error initializing database: {error}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
