import asyncio
import asyncpg
import ssl

async def main():
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        conn = await asyncpg.connect('postgresql://neondb_owner:npg_fP3WqRpCEQ8i@ep-billowing-dew-ay3r59t9.c-5.us-east-2.aws.neon.tech/neondb?sslmode=require')
        rows = await conn.fetch('SELECT id, name, status, resource_type FROM resources LIMIT 5;')
        for row in rows:
            print(dict(row))
        await conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    asyncio.run(main())
