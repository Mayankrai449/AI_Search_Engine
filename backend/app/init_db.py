from database import engine, Base
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection
import models.db_models

async def init_db():
    print("Creating database tables...")
    async with engine.begin() as conn:
        print("Setting search_path to public...")
        await conn.execute(text("SET search_path TO public"))
        print("Dropping existing tables...")
        await conn.run_sync(lambda sync_conn: Base.metadata.drop_all(sync_conn))
        print("Creating tables...")
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn))
        print("Verifying table creation...")
        tables = await conn.run_sync(lambda sync_conn: sync_conn.dialect.get_table_names(sync_conn, schema="public"))
        print(f"Tables created in public schema: {tables}")
        if not tables:
            print("Warning: No tables were created. Check database connection, permissions, or schema.")
        else:
            print("Table creation successful.")

if __name__ == "__main__":
    asyncio.run(init_db())