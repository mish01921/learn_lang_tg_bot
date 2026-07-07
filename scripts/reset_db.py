import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))) # Adjust path for src module

from src.database.models import close_db_pool, full_reset, init_db_pool


async def main():
    print("🚀 Initializing DB pool...")
    await init_db_pool()
    print("⚠️  Performing FULL RESET of the database...")
    try:
        await full_reset()
        print("✅ Database has been cleared and re-initialized.")
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
    finally:
        await close_http_session()
        await close_db_pool()

async def close_http_session():
    # Need to import it here to avoid top-level import issues if session wasn't opened
    from src.data.api_words import HTTPClient
    await HTTPClient.close()

if __name__ == "__main__":
    asyncio.run(main())
