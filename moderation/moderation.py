import discord
import typing
import datetime

# import time
# import os
# import asyncio
from discord.ext import commands

from core import checks
from core.models import PermissionLevel

# from core.time import UserFriendlyTime, human_timedelta


@commands.guild_only()
class ModerationPlugin(commands.Cog):
    def __init__(self, bot):
        self.bot: discord.Client = bot
        self.db = bot.plugin_db.get_partition(self)
        # self.mutes = list()

    # @commands.Cog.listener()
    # async def on_plugin_ready(self):
    #     config = await self.db.find_one({'_id': 'mutes'})
    #     if config is None:
    #         return
    #     self.mutes = set(config.get('mute_list', []))
    #     for mute in self.mutes:
    #         guild: discord.Guild = await self.bot.get_guild(os.getenv("GUILD_ID"))
    #         member = await guild.get_member(mute)
    #         if member:
    #             timeleft = mute["time"]
    #             if timeleft is None:
    #                 continue
    #             self.mutes.append(self.bot.loop.create_task(self.check_mute(member, timeleft)))
    #     self.loop_list.append(self.bot.loop.create_task(self.mute_list_check()))
    #
    # async def mute_list_check(self, member: discord.Member, timeleft):
    #     no_mute = []
    #     for mute in self.mutes:
    #         guild: discord.Guild = await self.bot.get_guild(os.getenv("GUILD_ID"))
    #         member = await guild.get_member(mute)
    #         if member:
    #             if mute["time"] is None:
    #                 continue

    @commands.command(aliases=["lc", "setmodlogs", "modlogs"])
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def logchannel(self, ctx, channel: discord.TextChannel):
        """Set up a logchannel for the mod logs.

        Usage:
        {prefix}logchannel #channel
        """

        await self.db.find_one_and_update(
            {"_id": "config"},
            {"$set": {"logs": {"channel": str(channel.id)}}},
            upsert=True,
        )
        await ctx.send(f"{channel.mention} is now set up for moderation logs!")

    @commands.command(aliases=["banhammer"])
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def ban(
        self,
        ctx,
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
            channel = ctx.guild.get_channel(int(config["logs"]["channel"]))

        if channel is None:
            return

        try:
            for member in members:
                await member.ban(
                    delete_message_days=days, reason=f"{reason if reason else None}"
                )

                embed = discord.Embed(
                    color=discord.Color.red(),
                    title=f"{member.display_name}#{member.discriminator} was banned!",
                    timestamp=datetime.datetime.utcnow(),
                )

                embed.add_field(
                    name="Moderator",
                    value=f"{ctx.author.name}#{ctx.author.discriminator}",
                    inline=False,
                )

                if reason:
                    embed.add_field(name="Reason", value=reason, inline=False)

                await ctx.send(f"{member.name} is banned!")
                await channel.send(embed=embed)

        except discord.Forbidden:
            await ctx.send("I don't have the proper permissions to ban people.")

        except Exception as e:
            await ctx.send(
                "An unexpected error occurred, please check the Heroku logs for more details."
            )
            raise e

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
            channel = ctx.guild.get_channel(int(config["logs"]["channel"]))

        if channel is None:
            return

        try:
            for member in members:
                await member.kick(reason=f"{reason if reason else None}")
                embed = discord.Embed(
                    color=discord.Color.red(),
                    title=f"{member.display_name}#{member.discriminator} was kicked!",
                    timestamp=datetime.datetime.utcnow(),
                )

                embed.add_field(
                    name="Moderator",
                    value=f"{ctx.author.name}#{ctx.author.discriminator}",
                    inline=False,
                )

                if reason is not None:
                    embed.add_field(name="Reason", value=reason, inline=False)

                await ctx.send(f"{member.name} is kicked!")
                await channel.send(embed=embed)

        except discord.Forbidden:
            await ctx.send("I don't have the proper permissions to kick people.")

        except Exception as e:
            await ctx.send(
                "An unexpected error occurred, please check the Heroku logs for more details."
            )
            raise e

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
            channel = ctx.guild.get_channel(int(channel_config["logs"]["channel"]))

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

        await ctx.send(
            f"Successfully warned **{member.name}#{member.discriminator}**\n`{reason}`"
        )

        await channel.send(
            embed=self.generateWarnEmbed(
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
            channel = ctx.guild.get_channel(int(channel_config["logs"]["channel"]))

        if channel is None:
            return

        config = await self.db.find_one({"_id": "warns"})

        if config is None:
            return

        try:
            userwarns = config[str(member.id)]
        except KeyError:
            return await ctx.send(f"{member.name} doesn't have any warnings.")

        if userwarns is None:
            await ctx.send(f"{member.name} doesn't have any warnings.")

        await self.db.find_one_and_update(
            {"_id": "warns"}, {"$set": {str(member.id): []}}
        )

        await ctx.send(
            f"Successfully pardoned **{member.name}#{member.discriminator}**\n`{reason}`"
        )

        embed = discord.Embed(color=discord.Color.blue())

        embed.set_author(
            name=f"Pardon | {member.name}#{member.discriminator}",
            icon_url=member.avatar_url,
        )
        embed.add_field(name="User", value=f"{member.name}#{member.discriminator}")
        embed.add_field(
            name="Moderator",
            value=f"<@{ctx.author.id}> - `{ctx.author.name}#{ctx.author.discriminator}`",
        )
        embed.add_field(name="Reason", value=reason)
        embed.add_field(name="Total Warnings", value="0")

        return await channel.send(embed=embed)

    @commands.command()
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def mute(
        self, ctx, members: commands.Greedy[discord.Member], *, reason: str = None
    ):
        """Mute one or more users.

        Usage:
        {prefix}mute @member Trashtalking
        {prefix}mute @member1 @member2 @member3 Discussing illegal things
        """

        config = await self.db.find_one({"_id": "config"})

        if config is None:
            return await ctx.send("There's no configured log channel.")

        channel = ctx.guild.get_channel(int(config["logs"]["channel"]))

        if channel is None:
            return

        for member in members:

            for channel in ctx.guild.channels:
                if not type(channel) is discord.TextChannel:
                    continue

                overs = channel.overwrites_for(member)
                if overs.send_messages is not False:
                    overs.send_messages = False
                    overs.add_reactions = False

                    try:
                        await channel.set_permissions(member, overwrite=overs)
                    except Exception as e:
                        raise e

            embed = discord.Embed(color=discord.Color.blue())

            embed.set_author(
                name=f"Mute | {member.name}#{member.discriminator}",
                icon_url=member.avatar_url,
            )
            embed.add_field(name="User", value=f"{member.name}#{member.discriminator}")
            embed.add_field(
                name="Moderator",
                value=f"<@{ctx.author.id}> - `{ctx.author.name}#{ctx.author.discriminator}`",
            )

            if reason is not None:
                embed.add_field(name="Reason", value=reason)

            await channel.send(embed=embed)
            await ctx.send(
                f"Muted **{member.name}#{member.discriminator}**\n`{reason}`"
            )

    @commands.command()
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def unmute(
        self, ctx, members: commands.Greedy[discord.Member], *, reason: str = None
    ):
        """Unmute one or more users.

        Usage:
        {prefix}unmute @member It's been two months now...
        {prefix}unmute @member1 @member2 @member3 Pardoned
        """

        config = await self.db.find_one({"_id": "config"})

        if config is None:
            return await ctx.send("There's no configured log channel.")

        channel = ctx.guild.get_channel(int(config["logs"]["channel"]))

        if channel is None:
            return

        for member in members:

            for channel in ctx.guild.channels:
                if not type(channel) is discord.TextChannel:
                    continue

                overs = channel.overwrites_for(member)

                if overs.send_messages is not True:
                    overs.send_messages = True
                    overs.add_reactions = True

                    try:
                        await channel.set_permissions(member, overwrite=overs)
                    except Exception as e:
                        raise e

            embed = discord.Embed(color=discord.Colour.blue())

            embed.set_author(
                name=f"Unmute | {member.name}#{member.discriminator}",
                icon_url=member.avatar_url,
            )
            embed.add_field(name="User", value=f"{member.name}#{member.discriminator}")
            embed.add_field(
                name="Moderator",
                value=f"<@{ctx.author.id}> - `{ctx.author.name}#{ctx.author.discriminator}`",
            )

            if reason:
                embed.add_field(name="Reason", value=reason)

            await channel.send(embed=embed)
            await ctx.send(
                f"Unmuted **{member.name}#{member.discriminator}**\n`{reason}`"
            )

    # async def handle_mute(self, member: discord.Member, now):
    #     self.mutes[str(member.id)] = now
    #     await self.update_mute_db()
    #     time = datetime.datetime.utcnow() - now
    #     guild: discord.guild = await self.bot.get_guild(os.getenv("GUILD_ID"))
    #     if time > 0:
    #         for channel in guild.channels:
    #             if not type(channel) is discord.TextChannel:
    #                 continue
    #             overs = channel.overwrites_for(member)
    #             if not overs.send_messages == False:
    #                 overs.send_messages = False
    #                 overs.add_reactions = False
    #                 try:
    #                     await channel.set_permissions(member, overwrite=overs)
    #                 except Exception as e:
    #                     raise e
    #         await asyncio.sleep(time)
    #         for channel in guild.channels:
    #             if not type(channel) is discord.TextChannel:
    #                 continue
    #             overs = channel.overwrites_for(member)
    #             otherPerms = False
    #             for perm in overs:
    #                 if not perm[1] == None and not str(perm[0]) == 'send_messages' and not str(perm[0]) == 'add_reactions':
    #                     otherPerms = True
    #             if overs.send_messages == False:
    #                 if otherPerms:
    #                     overs.send_messages = None
    #                     overs.add_reactions = None
    #                     try:
    #                         await channel.set_permissions(member, overwrite=overs)
    #                     except Exception as e:
    #                         raise e
    #                 else:
    #                     try:
    #                         await channel.set_permissions(member, overwrite=None)
    #                     except Exception as e:
    #                         raise e
    #             self.mutes.pop(str(member.id))
    #             await self.update_mute_db()
    #             return
    #     else:
    #         for channel in guild.channels:
    #             if not type(channel) is discord.TextChannel:
    #                 continue
    #             overs = channel.overwrites_for(member)
    #             otherPerms = False
    #             for perm in overs:
    #                 if not perm[1] == None and not str(perm[0]) == 'send_messages' and not str(perm[0]) == 'add_reactions':
    #                     otherPerms = True
    #             if overs.send_messages == False:
    #                 if otherPerms:
    #                     overs.send_messages = None
    #                     overs.add_reactions = None
    #                     try:
    #                         await channel.set_permissions(member, overwrite=overs)
    #                     except Exception as e:
    #                         raise e
    #                 else:
    #                     try:
    #                         await channel.set_permissions(member, overwrite=None)
    #                     except Exception as e:
    #                         raise e
    #             self.mutes.pop(str(member.id))
    #             await self.update_mute_db()
    #             return
    #
    # async def update_mute_db(self):
    #     await self.db.find_one_and_update(
    #         {"_id": "mutes"},
    #         {"$set": {"mute_list": self.mutes}},
    #         upsert=True
    #     )
    #     return

    async def generateWarnEmbed(self, memberid, modid, warning, reason):
        member: discord.User = await self.bot.fetch_user(int(memberid))
        mod: discord.User = await self.bot.fetch_user(int(modid))

        embed = discord.Embed(color=discord.Color.red())

        embed.set_author(
            name=f"Warn | {member.name}#{member.discriminator}",
            icon_url=member.avatar_url,
        )
        embed.add_field(name="User", value=f"{member.name}#{member.discriminator}")
        embed.add_field(
            name="Moderator", value=f"<@{modid}>` - ({mod.name}#{mod.discriminator})`"
        )
        embed.add_field(name="Reason", value=reason)
        embed.add_field(name="Total Warnings", value=warning)
        return embed


def setup(bot):
    bot.add_cog(ModerationPlugin(bot))
