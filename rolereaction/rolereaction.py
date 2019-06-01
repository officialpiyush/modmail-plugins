import asyncio
import discord
from discord.ext import commands

from core import checks
from core.models import PermissionLevel


class ReactionRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.plugin_db.get_partition(self)
        self.roles = dict()
        asyncio.create_task(self._set_config())

    async def _set_config(self):
        config = await self.db.find_one({"_id": "config"})
        if config is None:
            return
        self.roles = dict(config.get("roles", {}))

    @commands.group(aliases=["rr"])
    async def rolereaction(self, ctx):
        if ctx.invoked_subcommand is None:
            return

    @rolereaction.command()
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def add(self, ctx, emoji: discord.Emoji, role: discord.Role):
        emote = emoji.name if emoji.id is None else emoji.id

        if emote in self.roles:
            updated = True
        else:
            updated = False
        self.roles[emote] = role.id

        await self.db.find_one_and_update(
            {"_id": "config"}, {"$set": {"roles": self.roles}}, upsert=True
        )

        await ctx.send(
            f"Successfully {'updated'if updated else 'pointed'} {emoji} towards {role.name}"
        )

    @rolereaction.command()
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def remove(self, ctx, emoji: discord.Emoji):
        """Remove a role from the role reaction list"""
        emote = emoji.name if emoji.id is None else emoji.id

        if emote not in self.roles:
            await ctx.send("The Given Emote Was Not Configured")
            return

        self.roles.pop(emote)

        await self.db.find_one_and_update(
            {"_id": "config"}, {"$set": {"roles": self.roles}}, upsert=True
        )

        await ctx.send(f"Removed {emoji} from rolereaction list")
        return

    @rolereaction.command(aliases=["sc"])
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def set_channel(self, ctx, channel=discord.TextChannel):
        await self.db.find_one_and_update(
            {"_id": "config"}, {"$set": {"channel": str(channel.id)}}, upsert=True
        )

        await ctx.send(f"{channel.mention} has been set!")

    @rolereaction.command()
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def react(self, ctx, id: discord.Message.id):
        """React On The Message"""
        config = await self.db.find_one({"_id": "config"})
        if config is None:
            return

        dbchannel = config["channel"]

        channel: discord.TextChannel = await ctx.guild.get_channel(int(dbchannel))

        if channel:
            msg: discord.Message = await channel.fetch_message(int(id))
            for x in self.roles:
                await msg.add_reaction(x)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        user: discord.User = self.bot.get_user(int(payload.user_id))
        guild: discord.Guild = self.bot.config.get("GUILD_ID")

        if user.bot:
            return

        member: discord.Member = await guild.fetch_member(payload.user_id)

        if member is None:
            return

        if payload.emoji.name in self.roles or payload.emoji.id in self.roles:
            role = await guild.get_role(
                self.roles[payload.emoji.name or payload.emoji.id]
            )
            await member.add_roles(role)


def setup(bot):
    bot.add_cog(ReactionRole(bot))
