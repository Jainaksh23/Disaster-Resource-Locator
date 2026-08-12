import asyncio
from core.database import async_session_maker
from routers.resources import list_resources
from schemas.resource import ResourceListResponse
from fastapi import HTTPException
import logging

logging.basicConfig(level=logging.DEBUG)

async def main():
    async with async_session_maker() as db:
        try:
            response = await list_resources(db=db, page=1, page_size=20, resource_type=None, status=None)
            print(f"Success! Total: {response.total}")
            for item in response.items:
                print(item.name)
        except Exception as e:
            print(f"Exception during list_resources: {e}")

if __name__ == "__main__":
    asyncio.run(main())
