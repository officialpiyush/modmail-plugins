import json
import os
import datetime
import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient

from core import checks
from core.models import PermissionLevel


class BackupDB(commands.Cog):
    """
    Take Backup of your mongodb database with a single command!

    **Requires `BACKUP_MONGO_URI` in environment variables or config.json** (different from your original db)
    """

    def __init__(self, bot):
        self.bot = bot
        self.db = bot.plugin_db.get_partition(self)
        self.running = False

    @commands.group()
    @checks.has_permissions(PermissionLevel.OWNER)
    async def backup(self, ctx: commands.Context):
        """
        Backup Your Mongodb database using this command.

        **Deletes Existing data from the backup db**
        """
        if ctx.invoked_subcommand is None:
            if self.running is True:
                await ctx.send(
                    "A backup/restore process is already running, please wait until it finishes"
                )
                return
            if os.path.exists("./config.json"):
                with open("./config.json") as f:

                    jd = json.load(f)
                try:
                    backup_url = jd["BACKUP_MONGO_URI"]
                except KeyError:
                    backup_url = os.getenv("BACKUP_MONGO_URI")
                    if backup_url is None:
                        await ctx.send(
                            ":x: | No `BACKUP_MONGO_URI` found in `config.json` or environment variables, please add one.\nNote: Backup db is different from original db!"
                        )
                        return
            else:
                backup_url = os.getenv("BACKUP_MONGO_URI")
                if backup_url is None:
                    await ctx.send(
                        ":x: | No `BACKUP_MONGO_URI` found in `config.json` or environment variables, please add one.\nNote: Backup db is different from original db!"
                    )
                    return
            self.running = True
            db_name = (backup_url.split("/"))[-1]
            backup_client = AsyncIOMotorClient(backup_url)
            if "mlab.com" in backup_url:
                bdb = backup_client[db_name]
            else:
                bdb = backup_client["backup_modmail_bot"]
            await ctx.send(
                embed=await self.generate_embed(
                    "Connected to backup DB. Removing all documents"
                )
            )
            collections = await bdb.list_collection_names()

            if len(collections) > 0:
                for collection in collections:
                    if collection == "system.indexes":
                        continue

                    await bdb[collection].drop()
                await ctx.send(
                    embed=await self.generate_embed(
                        "Deleted all documents from backup db"
                    )
                )
            else:
                await ctx.send(
                    embed=await self.generate_embed(
                        "No Existing collections found! Nothing was deleted!"
                    )
                )
            du = await self.bot.db.list_collection_names()
            for collection in du:
                if collection == "system.indexes":
                    continue

                le = await self.bot.db[str(collection)].find().to_list(None)
                for item in le:
                    await bdb[str(collection)].insert_one(item)
                    del item
                del le
                await ctx.send(
                    embed=await self.generate_embed(f"Backed up `{str(collection)}`")
                )
            await self.db.find_one_and_update(
                {"_id": "config"},
                {"$set": {"backedupAt": str(datetime.datetime.utcnow())}},
                upsert=True,
            )
            await ctx.send(
                embed=await self.generate_embed(
                    f":tada: Backed Up Everything!\nTo restore your backup at any time, type `{self.bot.prefix}backup restore`."
                )
            )
            self.running = False
            return

    @backup.command()
    @checks.has_permissions(PermissionLevel.OWNER)
    async def restore(self, ctx: commands.Context):
        """
        Restore Your Mongodb database using this command.

        **Deletes Existing data from the original db and overwrites it with data in backup db**
        """

        def check(msg: discord.Message):
            return ctx.author == msg.author and ctx.channel == msg.channel

        if self.running is True:
            await ctx.send(
                "A backup/restore process is already running, please wait until it finishes"
            )
            return

        config = await self.db.find_one({"_id": "config"})

        if config is None or config["backedupAt"] is None:
            await ctx.send("No previous backup found, exiting")
            return

        await ctx.send(
            embed=await self.generate_embed(
                f"Are you sure you wanna restore data from backup db which"
                f" was last updated on **{config['backedupAt']} UTC**? `[y/n]`"
            )
        )
        msg: discord.Message = await self.bot.wait_for("message", check=check)
        if msg.content.lower() == "n":
            await ctx.send("Exiting!")
            return
        self.running = True
        if os.path.exists("./config.json"):
            with open("./config.json") as f:

                jd = json.load(f)
            try:
                backup_url = jd["BACKUP_MONGO_URI"]
            except KeyError:
                backup_url = os.getenv("BACKUP_MONGO_URI")
                if backup_url is None:
                    await ctx.send(
                        ":x: | No `BACKUP_MONGO_URI` found in `config.json` or environment variables"
                    )
                    return
        else:
            backup_url = os.getenv("BACKUP_MONGO_URI")
            if backup_url is None:
                await ctx.send(
                    ":x: | No `BACKUP_MONGO_URI` found in `config.json` or environment variables"
                )
                return

        db_name = (backup_url.split("/"))[-1]
        backup_client = AsyncIOMotorClient(backup_url)
        if "mlab.com" in backup_url:
            bdb = backup_client[db_name]
        else:
            bdb = backup_client["backup_modmail_bot"]
        await ctx.send(
            embed=await self.generate_embed(
                "Connected to backup DB. Removing all documents from original db."
            )
        )
        collections = await self.bot.db.list_collection_names()

        if len(collections) > 0:
            for collection in collections:
                if collection == "system.indexes":
                    continue

                await self.bot.db[collection].drop()
            await ctx.send(
                embed=await self.generate_embed("Deleted all documents from main db")
            )
        else:
            await ctx.send(
                embed=await self.generate_embed(
                    "No Existing collections found! Nothing was deleted!"
                )
            )
        du = await bdb.list_collection_names()
        for collection in du:
            if collection == "system.indexes":
                continue

            le = await bdb[str(collection)].find().to_list(None)
            for item in le:
                await self.bot.db[str(collection)].insert_one(item)
                del item
            del le
            await ctx.send(
                embed=await self.generate_embed(f"Restored `{str(collection)}`")
            )
        await self.db.find_one_and_update(
            {"_id": "config"},
            {"$set": {"restoredAt": str(datetime.datetime.utcnow())}},
            upsert=True,
        )
        await ctx.send(embed=await self.generate_embed(":tada: Restored Everything!"))
        self.running = False
        return

    async def generate_embed(self, msg: str):
        embed = discord.Embed(description=msg, color=discord.Colour.blurple())
        return embed


def setup(bot):
    bot.add_cog(BackupDB(bot))
