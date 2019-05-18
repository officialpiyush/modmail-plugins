import discord
import typing
from datetime import datetime
from discord.ext import commands

from core import checks
from core.models import PermissionLevel


@commands.guild_only()
class ModerationPlugin:
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.plugin_db.get_partition(self)

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
                        timestamp=datetime.utcnow()
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
                        timestamp=datetime.utcnow()
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


def setup(bot):
    bot.add_cog(ModerationPlugin(bot))
