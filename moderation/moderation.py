import datetime
import logging

logger = logging.getLogger("Modmail")

import discord
import typing
from discord.ext import commands

from core import checks
from core.models import PermissionLevel


class ModerationPlugin(commands.Cog):
    """
    Moderate ya server using modmail pog
    """

    def __init__(self, bot):
        self.bot = bot
        self.db = bot.plugin_db.get_partition(self)

    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def moderation(self, ctx: commands.Context):
        """
        Settings and stuff
        """
        await ctx.send_help(ctx.command)
        return

    @moderation.command()
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """
        Set the log channel for moderation actions.
        """

        await self.db.find_one_and_update(
            {"_id": "config"}, {"$set": {"channel": channel.id}}, upsert=True
        )

        await ctx.send("Done!")
        return

    @commands.command(aliases=["banhammer"])
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def ban(
        self,
        ctx: commands.Context,
        members: commands.Greedy[discord.Member],
        days: typing.Optional[int] = 0,
        *,
        reason: str = None,
    ):
        """Ban one or more users.
        Usage:
        {prefix}ban @member 10 Advertising their own products
        {prefix}ban @member1 @member2 @member3 Spamming
        """

        config = await self.db.find_one({"_id": "config"})

        if config is None:
            return await ctx.send("There's no configured log channel.")
        else:
            channel = ctx.guild.get_channel(int(config["channel"]))

        if channel is None:
            await ctx.send("There is no configured log channel.")
            return

        try:
            for member in members:
                await member.ban(
                    delete_message_days=days, reason=f"{reason if reason else None}"
                )

                embed = discord.Embed(
                    color=discord.Color.red(),
                    title=f"{member} was banned!",
                    timestamp=datetime.datetime.utcnow(),
                )

                embed.add_field(
                    name="Moderator",
                    value=f"{ctx.author}",
                    inline=False,
                )

                if reason:
                    embed.add_field(name="Reason", value=reason, inline=False)

                await ctx.send(f"🚫 | {member} is banned!")
                await channel.send(embed=embed)

        except discord.Forbidden:
            await ctx.send("I don't have the proper permissions to ban people.")

        except Exception as e:
            await ctx.send(
                "An unexpected error occurred, please check the logs for more details."
            )
            logger.error(e)
            return

    @commands.command(aliases=["getout"])
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def kick(
        self, ctx, members: commands.Greedy[discord.Member], *, reason: str = None
    ):
        """Kick one or more users.
        Usage:
        {prefix}kick @member Being rude
        {prefix}kick @member1 @member2 @member3 Advertising
        """

        config = await self.db.find_one({"_id": "config"})

        if config is None:
            return await ctx.send("There's no configured log channel.")
        else:
            channel = ctx.guild.get_channel(int(config["channel"]))

        if channel is None:
            await ctx.send("There is no configured log channel.")
            return

        try:
            for member in members:
                await member.kick(reason=f"{reason if reason else None}")
                embed = discord.Embed(
                    color=discord.Color.red(),
                    title=f"{member} was kicked!",
                    timestamp=datetime.datetime.utcnow(),
                )

                embed.add_field(
                    name="Moderator",
                    value=f"{ctx.author}",
                    inline=False,
                )

                if reason is not None:
                    embed.add_field(name="Reason", value=reason, inline=False)

                await ctx.send(f"🦶 | {member} is kicked!")
                await channel.send(embed=embed)

        except discord.Forbidden:
            await ctx.send("I don't have the proper permissions to kick people.")

        except Exception as e:
            await ctx.send(
                "An unexpected error occurred, please check the Heroku logs for more details."
            )
            logger.error(e)
            return

    @commands.command()
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def warn(self, ctx, member: discord.Member, *, reason: str):
        """Warn a member.
        Usage:
        {prefix}warn @member Spoilers
        """

        if member.bot:
            return await ctx.send("Bots can't be warned.")

        channel_config = await self.db.find_one({"_id": "config"})

        if channel_config is None:
            return await ctx.send("There's no configured log channel.")
        else:
            channel = ctx.guild.get_channel(int(channel_config["channel"]))

        if channel is None:
            return

        config = await self.db.find_one({"_id": "warns"})

        if config is None:
            config = await self.db.insert_one({"_id": "warns"})

        try:
            userwarns = config[str(member.id)]
        except KeyError:
            userwarns = config[str(member.id)] = []

        if userwarns is None:
            userw = []
        else:
            userw = userwarns.copy()

        userw.append({"reason": reason, "mod": ctx.author.id})

        await self.db.find_one_and_update(
            {"_id": "warns"}, {"$set": {str(member.id): userw}}, upsert=True
        )

        await ctx.send(f"Successfully warned **{member}**\n`{reason}`")

        await channel.send(
            embed=await self.generateWarnEmbed(
                str(member.id), str(ctx.author.id), len(userw), reason
            )
        )
        del userw
        return

    @commands.command()
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def pardon(self, ctx, member: discord.Member, *, reason: str):
        """Remove all warnings of a  member.
        Usage:
        {prefix}pardon @member Nice guy
        """

        if member.bot:
            return await ctx.send("Bots can't be warned, so they can't be pardoned.")

        channel_config = await self.db.find_one({"_id": "config"})

        if channel_config is None:
            return await ctx.send("There's no configured log channel.")
        else:
            channel = ctx.guild.get_channel(int(channel_config["channel"]))

        if channel is None:
            return

        config = await self.db.find_one({"_id": "warns"})

        if config is None:
            return

        try:
            userwarns = config[str(member.id)]
        except KeyError:
            return await ctx.send(f"{member} doesn't have any warnings.")

        if userwarns is None:
            await ctx.send(f"{member} doesn't have any warnings.")

        await self.db.find_one_and_update(
            {"_id": "warns"}, {"$set": {str(member.id): []}}
        )

        await ctx.send(f"Successfully pardoned **{member}**\n`{reason}`")

        embed = discord.Embed(color=discord.Color.blue())

        embed.set_author(
            name=f"Pardon | {member}",
            icon_url=member.avatar_url,
        )
        embed.add_field(name="User", value=f"{member}")
        embed.add_field(
            name="Moderator",
            value=f"<@{ctx.author.id}> - `{ctx.author}`",
        )
        embed.add_field(name="Reason", value=reason)
        embed.add_field(name="Total Warnings", value="0")

        return await channel.send(embed=embed)

    async def generateWarnEmbed(self, memberid, modid, warning, reason):
        member: discord.User = await self.bot.fetch_user(int(memberid))
        mod: discord.User = await self.bot.fetch_user(int(modid))

        embed = discord.Embed(color=discord.Color.red())

        embed.set_author(
            name=f"Warn | {member}",
            icon_url=member.avatar_url,
        )
        embed.add_field(name="User", value=f"{member}")
        embed.add_field(name="Moderator", value=f"<@{modid}>` - ({mod})`")
        embed.add_field(name="Reason", value=reason)
        embed.add_field(name="Total Warnings", value=warning)
        return embed


def setup(bot):
    bot.add_cog(ModerationPlugin(bot))
