import json
import os
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient

from core import checks
from core.models import PermissionLevel


class BackupDB(commands.Cog):
    """
    Take Backup of your mongodb database with a single command!

    **Requires `BACKUP_MONGO_URI` in environment variables or config.json**
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @checks.has_permissions(PermissionLevel.OWNER)
    async def backup(self, ctx: commands.Context):
        """
        Backup Your Mongodb database using this command.

        **Deletes Existing data from the backup db**
        """
        if os.path.exists("../config.json"):
            with open("../config.json") as f:

                jd = json.load(f)
            try:
                backup_url = jd["BACKUP_MONGO_URI"]
            except KeyError:
                backup_url = os.getenv("BACKUP_MONGO_URI")
                if backup_url is None:
                    await ctx.send(":x: | No `BACKUP_MONGO_URI` found in `config.json` or environment variables")
                    return
        else:
            backup_url = os.getenv("BACKUP_MONGO_URI")
            if backup_url is None:
                await ctx.send(":x: | No `BACKUP_MONGO_URI` found in `config.json` or environment variables")
                return
        db_name = (backup_url.split("/"))[-1]
        backup_client = AsyncIOMotorClient(backup_url)
        bdb = backup_client[db_name]
        await ctx.send("Connected to backup DB. Removing all documents")
        collections = await bdb.list_collection_names()

        if len(collections) > 0:
            for collection in collections:
                if collection == "system.indexes":
                    continue

                await bdb[collection].drop()
            await ctx.send("Deleted all documents from backup db")
        else:
            await ctx.send("No Existing collections found! Nothing was deleted!")
        du = await self.bot.db.list_collection_names()
        for collection in du:
            if collection == "system.indexes":
                continue

            le = await self.bot.db[str(collection)].find().to_list(None)
            for item in le:
                await bdb[str(collection)].insert_one(item)
                del item
            del le
            await ctx.send(f"Backed up `{str(collection)}`")
        await ctx.send(":tada: | Backed Up Everything!")


def setup(bot):
    bot.add_cog(BackupDB(bot))
