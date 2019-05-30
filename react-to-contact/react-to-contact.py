
import typing
import datetime
import discord
from discord.ext import commands

from core import checks
from core.models import PermissionLevel


class ReactToContact(commands.Cog):
    """
    Make users start modmail thread by clicking an emoji
    """
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.plugin_db.get_partition(self)

    @commands.command(aliases=["setmessage"])
    @commands.guild_only()
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def setreaction(self, ctx: commands.Context, channel: typing.Optional[discord.TextChannel],
                          messageid: discord.Message.id):
        """
        Set the message on which the bot will look reactions on.
        Creates an interactive session to use emoji **(Supports Unicode Emoji Too)**

        **Usage:**
        {prefix}setreaction [channel] <message_id>
        """

        if channel is None:
            channel: discord.TextChannel = ctx.channel
        else:
            channel = ctx.channel
        msg: discord.Message = await channel.fetch_message(int(messageid))
        await ctx.send(f"Message with Message id `{messageid}` found.")
        await ctx.send()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return

        config = await self.db.find_one({"_id": "config"})

        if config is None:
            return

        if config["emoji"] is None or (config["emoji"] != payload.emoji.id):
            return

        if config["channel"] is None or (payload.channel_id != config["channel"]):
            return

        if config["mid"] is None or (payload.message_id != config["mid"]):
            return

        guild: discord.Guild = discord.utils.find(lambda g: g.id == payload.guild_id, self.bot.guilds)

        member: discord.Member = guild.get_member(payload.user_id)

        channel = guild.get_channel(int(config["channel"]))

        msg: discord.Message = await channel.fetch_message(int(config["mid"]))

        await msg.remove_reaction(payload.emoji, member)

        try:
            await member.send(embed=discord.Embed(
                description="Hello, how may we help you?",
                color=self.bot.main_color,
            ))
        except (discord.HTTPException, discord.Forbidden):
            ch = self.bot.get_channel(int(self.bot.config.get('log_channel_id')))

            await ch.send(embed=discord.Embed(
                title="User Contact failed",
                description=f"**{member.name}#{member.discriminator}** tried contacting, but the bot couldnt dm him/her.",
                color=self.bot.main_color,
                timestamp=datetime.datetime.utcnow()
            ))


def setup(bot):
    bot.add_cog(ReactToContact(bot))



