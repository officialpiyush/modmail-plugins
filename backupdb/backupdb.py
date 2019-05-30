
import os
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient

from core import checks
from core.models import PermissionLevel


class BackupDB(commands.Cog):
    """
    Take Backup of your mongodb database with a single command!

    **Requires `BACKUP_MONGO_URI` in Heroku environment variables**
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
        backup_url = os.getenv("BACKUP_MONGO_URI", None)
        if backup_url is None:
            await ctx.send(":x: | No `BACKUP_MONGO_URI` found in env variables.")
            return
        db_name = (backup_url.split("/"))[-1]
        backup_client = AsyncIOMotorClient(backup_url)
        bdb = backup_client[db_name]
        await ctx.send("Connected to backup DB. Removing all documents")
        collections = await bdb.list_collection_names()
        await ctx.send(collections)
        if len(collections) > 0:
            for collection in collections:
                if collection == "system.indexes":
                    continue

                await bdb[collection].drop()
            await ctx.send("Deleted all documents from backup db")
        else:
            await ctx.send("No Existing collections found! Nothing was deleted!")
        du = self.bot.db.list_collection_names()
        for coll in du:
            if coll == "system.indexes":
                continue
            for doc in self.bot.db[coll].find():
                await bdb[coll].insert_one(doc)
            await ctx.send(f"Backed up `{coll}` collection!")


def setup(bot):
    bot.add_cog(BackupDB(bot))
