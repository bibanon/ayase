from databases import Database
from src.core.config import config

DB_ENGINE = config["database"]["default"]
DATABASE_URL = "{engine}://{user}:{password}@{host}:{port}/{database}"

global database
database = None


async def init_db():
    database = None
    url = DATABASE_URL.format(
        engine=DB_ENGINE,
        host=config["database"][DB_ENGINE]["host"],
        port=config["database"][DB_ENGINE]["port"],
        user=config["database"][DB_ENGINE]["user"],
        password=config["database"][DB_ENGINE]["password"],
        database=config["database"][DB_ENGINE]["db"],
    )
    database = Database(url)
    await database.connect()


async def shutdown_db():
    if database:
        await database.disconnect()


async def db_handler(sql: str, fetchall: bool):
    try:
        if "debug" not in config or config["debug"] is False:
            return (
                (await database.fetch_all(query=sql))
                if fetchall
                else (await database.fetch_one(query=sql))
            )
        else:
            await database.fetch_one(query="select 1")
            start = timeit.default_timer()
            if fetchall:
                result = await database.fetch_all(query=sql)
                end = timeit.default_timer()
                print("Time waiting for query: ", end - start)
                return result
            else:
                result = await database.fetch_one(query=sql)
                end = timeit.default_timer()
                print("Time waiting for query: ", end - start)
                return result
    except Exception as e:
        logging.error(f"Query failed!: {e}")
        return ""

