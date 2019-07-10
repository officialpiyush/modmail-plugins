import logging

import discord
from discord.ext import commands

logger = logging.getLogger("Modmail")


class DmOnJoinPlugin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.plugin_db.get_partition(self)

    @commands.command(aliases=["sdms"])
    @commands.has_permissions(manage_guild=True)
    async def setdmmessage(self, ctx, *, message):
        """Set a message to DM a user after they join."""
        if message.startswith("https://") or message.startswith("http://"):
            # message is a URL
            if message.startswith("https://hasteb.in/"):
                message = "https://hasteb.in/raw/" + message.split("/")[-1]

            async with self.bot.session.get(message) as resp:
                message = await resp.text()

        await self.db.find_one_and_update(
            {"_id": "dm-config"},
            {"$set": {"dm-message": {"message": message}}},
            upsert=True,
        )

        await ctx.send("Successfully set the message.")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        config = await self.db.find_one({"_id": "dm-config"})
        
        if config is None:
            logger.info("User joined, but no DM message was set.")
            return

        try:
            message = config["dm-message"]["message"]
            await member.send(message)
        except:
            return

    @commands.Cog.listener()
    async def on_ready(self):
        async with self.bot.session.post(
            "https://counter.modmail-plugins.ionadev.ml/api/instances/dmonjoin",
            json={"id": self.bot.user.id},
        ):
            print("Posted to plugin API")


def setup(bot):
    bot.add_cog(DmOnJoinPlugin(bot))
