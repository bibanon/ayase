import logging
import timeit
from databases import Database
from src.core.settings import config

DB_ENGINE = config["database"]["default"]
DATABASE_URL = "{engine}://{user}:{password}@{host}:{port}/{database}"


class DB:
    __instance = None

    @staticmethod
    def getInstance():
        if DB.__instance is None:
            DB()
        return DB.__instance

    def __init__(self):
        DB.__instance = self

    async def init_db(self):
        self.database = None
        url = DATABASE_URL.format(
            engine=DB_ENGINE,
            host=config["database"][DB_ENGINE]["host"],
            port=config["database"][DB_ENGINE]["port"],
            user=config["database"][DB_ENGINE]["user"],
            password=config["database"][DB_ENGINE]["password"],
            database=config["database"][DB_ENGINE]["db"],
        )
        self.database = Database(url)
        await self.database.connect()


    async def shutdown_db(self):
        if self.database:
            await self.database.disconnect()


    async def db_handler(self, sql: str, fetchall: bool):
        try:
            if "debug" not in config or config["debug"] is False:
                return (
                    (await self.database.fetch_all(query=sql))
                    if fetchall
                    else (await self.database.fetch_one(query=sql))
                )
            else:
                await self.database.fetch_one(query="select 1")
                start = timeit.default_timer()
                if fetchall:
                    result = await self.database.fetch_all(query=sql)
                    end = timeit.default_timer()
                    print("Time waiting for query: ", end - start)
                    return result
                else:
                    result = await self.database.fetch_one(query=sql)
                    end = timeit.default_timer()
                    print("Time waiting for query: ", end - start)
                    return result
        except Exception as e:
            logging.error(f"Query failed!: {e}")
            return ""
