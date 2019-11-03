import asyncio

from discord.ext import commands


class Dasboard(commands.Cog):
    def __init__(self, bot):
        self.bot: discord.Client = bot
        self.db = bot.plugin_db.get_partition(self)
        asyncio.create_task(self.set_db())

    async def set_db(self):
        await self.db.find_one_and_update(
            {"_id": "config"},
            {"$set": {"log_uri": self.bot.config["log_url"].strip("/")}},
            upsert=True,
        )


def setup(bot):
    bot.add_cog(Dasboard(bot))
