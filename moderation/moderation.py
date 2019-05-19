import discord
import typing
import datetime
from discord.ext import commands

from core import checks
from core.models import PermissionLevel


@commands.guild_only()
class ModerationPlugin(commands.Cog):
    def __init__(self, bot):
        self.bot: discord.Client = bot
        self.db = bot.plugin_db.get_partition(self)
        self.mute_list = []

    @commands.command(aliases=["lc", "setmodlogs", "modlogs"])
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def logchanel(self, ctx, channel: discord.TextChannel):
        """Set Up The Log Channel For posting mod-logs

        Usage:
        logchannel #channel
        """
        await self.db.find_one_and_update(
        {'_id': 'config'},
        {'$set': {'logs': {'channel': str(channel.id)}}},
        upsert=True
        )
        await ctx.send(f"{channel.mention} set for mod-logs!")

    @commands.command(aliases=["banhammer"])
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def ban(self, ctx, members: commands.Greedy[discord.Member], delete_days: typing.Optional[int] = 0, *,
                  reason: str = None):
        """Ban A Single User or a group of members

        Usage:
        ban @member Gave a ban
        ban @member1 @member2 @member3 Spammers
        """

        config = (await self.db.find_one({'_id': 'config'}))
        if config is None:
            await ctx.send("No mod-log channel configured")
            return
        else:
            channel = ctx.guild.get_channel(int(config["logs"]['channel']))

        if channel:
            try:
                for member in members:
                    await member.ban(delete_message_days=delete_days, reason=f'{reason if reason else None}')
                    embed = discord.Embed(
                        color=discord.Color.red(),
                        title=f"{member.display_name}#{member.discriminator} was banned",
                        timestamp=datetime.datetime.utcnow()
                    )
                    embed.add_field(name="Moderator", value=f"{ctx.author.name}#{ctx.author.discriminator}",
                                    inline=False)
                    if reason:
                        embed.add_field(name="Reason", value=reason, inline=False)

                    await channel.send(embed=embed)
            except discord.Forbidden:
                await ctx.send("I Have No Permission To ban the user")
            except Exception as e:
                await ctx.send("An Error Occurred, Check Logs For More Details")
                raise e

    @commands.command(aliases=["getout"])
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def kick(self, ctx, members: commands.Greedy[discord.Member], *, reason: str = None):
        """Kick a Single member or a group of members

                Usage:
                kick @member Gave a kick
                kick @member1 @member2 @member3 Spammers
                """

        config = (await self.db.find_one({'_id': 'config'}))
        if config is None:
            await ctx.send("No mod-log channel configured")
            return
        else:
            channel = ctx.guild.get_channel(int(config["logs"]['channel']))

        if channel:
            try:
                for member in members:
                    await member.kick(reason=f'{reason if reason else None}')
                    embed = discord.Embed(
                        color=discord.Color.red(),
                        title=f"{member.display_name}#{member.discriminator} was kicked",
                        timestamp=datetime.datetime.utcnow()
                    )
                    embed.add_field(name="Moderator", value=f"{ctx.author.name}#{ctx.author.discriminator}",
                                    inline=False)
                    if reason:
                        embed.add_field(name="Reason", value=reason, inline=False)

                    await channel.send(embed=embed)
            except discord.Forbidden:
                await ctx.send("I Have No Permission To kick the user")
            except Exception as e:
                await ctx.send("An Error Occurred, Check Logs For More Details")
                raise e

    # @commands.command()
    # @checks.has_permissions(PermissionLevel.MODERATOR)
    # async def mute(self, ctx, members: commands.Greedy[discord.Member], *, reason: str = None):
    #     """Mute a Single member or a group of members
    #
    #                     Usage:
    #                     mute @member Gave a kick
    #                     mute @member1 @member2 @member3 Spammers
    #                     """
    #
    #     config = (await self.db.find_one({'_id': 'config'}))
    #     if config is None:
    #         await ctx.send("No mod-log channel configured")
    #         return
    #     else:
    #         channel = ctx.guild.get_channel(int(config["logs"]['channel']))
    #
    #      if channel:

    @commands.command()
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def warn(self, ctx: commands.Context,  member: discord.Member, *, reason: str):
        """Warn a member

        Usage:
        warn @member <...reason>
        """
        if member.bot:
            await ctx.send("Bot's Cannot be warned")
            return

        chconfig = (await self.db.find_one({'_id': 'config'}))
        if chconfig is None:
            await ctx.send("No mod-log channel configured")
            return
        else:
            channel = ctx.guild.get_channel(int(chconfig["logs"]['channel']))
        if channel:
            config = await self.db.find_one({"_id": "warns"})

            if config:
                userwarns = config[str(member.id)]

                if userwarns is None:
                    userw = []
                    userw.append({"reason": reason, "mod": ctx.author.id})
                    await self.db.find_one_and_update(
                        {"_id": "warns"},
                        {"$set": {str(member.id): userw}},
                        upsert=True
                    )
                    await ctx.send(f"Successfully warned **{member.name}#{member.discriminator}**`({reason})`")
                    await channel.send(
                        embed=self.generateWarnEmbed(str(member.id), str(ctx.author.id), len(userw), reason))
                    del userw
                    return
                else:
                    userw = userwarns.copy()
                    userw.append({"reason": reason, "mod": ctx.author.id})
                    await self.db.find_one_and_update(
                        {"_id": "warns"},
                        {"$set": {str(member.id): userw}},
                        upsert=True)
                    await ctx.send(f"Successfully warned **{member.name}#{member.discriminator}**`({reason})`")
                    await channel.send(embed=self.generateWarnEmbed(str(member.id), str(ctx.author.id), len(userw), reason))
                    del userw
                    return
            else:
                userw = []
                userw.append({"reason": reason, "mod": ctx.author.id})
                await self.db.find_one_and_update(
                    {"_id": "warns"},
                    {"$set": {str(str(member.id)): userw}},
                    upsert=True)
                await ctx.send(f"Successfully warned **{member.name}#{member.discriminator}**`({reason})`")
                await channel.send(embed=self.generateWarnEmbed(str(member.id), str(ctx.author.id), len(userw), reason))
                del userw
                return

    async def generateWarnEmbed(self, memberid, modid, warning, reason):
        member: discord.User = await self.bot.fetch_user(int(memberid))
        mod: discord.User = self.bot.fetch_user(int(modid))
        embed = discord.Embed()
        embed.colour = discord.Colour.red()
        embed.set_author(name=f"Warn | {member.name}", icon_url=member.avatar_url)
        embed.add_field(name="User", value=f"{member.name}#{member.discriminator}")
        embed.add_field(name="Moderator", value=f"<@{modid}>`({mod.name}#{mod.discriminator})`")
        embed.add_field(name="Reason", value=reason)
        embed.add_field(name="Total Warnings", value=warning)
        return embed

def setup(bot):
    bot.add_cog(ModerationPlugin(bot))
