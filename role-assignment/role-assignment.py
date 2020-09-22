# This file contains edited code from https://github.com/papiersnipper/modmail-plugins/blob/master/role-assignment/role-assignment.py . Copyright reserved with respective owners
import logging

import asyncio
import discord
from discord.ext import commands

from core import checks
from core.models import PermissionLevel

Cog = getattr(commands, "Cog", object)

logger = logging.getLogger("Modmail")


class RoleAssignment(Cog):
    """Assign roles using reactions.
    More info: [click here](https://github.com/officialpiyush/modmail-plugins/tree/master/role-assignment)
    """

    def __init__(self, bot):
        self.bot = bot
        self.db = bot.plugin_db.get_partition(self)
        self.ids = []
        asyncio.create_task(self.sync())

    async def update_db(self):

        await self.db.find_one_and_update(
            {"_id": "role-config"}, {"$set": {"ids": self.ids}}
        )

    async def _set_db(self):

        config = await self.db.find_one({"_id": "role-config"})

        if config is None:
            return

        self.ids = config["ids"]

    async def sync(self):

        await self._set_db()

        category_id = int(self.bot.config["main_category_id"])

        if category_id is None:
            print("No main_category_id found!")
            return

        guild = self.bot.get_guild(int(self.bot.config["guild_id"]))

        if guild is None:
            print("No guild_id found!")
            return

        for c in guild.categories:
            if c.id != category_id:
                continue
            else:
                channel_genesis_ids = []
                for channel in c.channels:
                    if not isinstance(channel, discord.TextChannel):
                        continue

                    if channel.topic is None:
                        continue

                    if channel.topic[:9] != "User ID: ":
                        continue

                    messages = await channel.history(oldest_first=True).flatten()
                    genesis_message = str(messages[0].id)
                    channel_genesis_ids.append(genesis_message)

                    if genesis_message not in self.ids:
                        self.ids.append(genesis_message)
                    else:
                        continue

                for id in self.ids:
                    if id not in channel_genesis_ids:
                        self.ids.remove(id)
                    else:
                        continue

                await self.update_db()
                logger.info("Synced role with the database")

    @commands.group(name="role", aliases=["roles"], invoke_without_command=True)
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def role(self, ctx):
        """Automaticly assign roles when you click on the emoji."""

        await ctx.send_help(ctx.command)

    @role.command(name="add")
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def add(self, ctx, emoji: discord.Emoji, *, role: discord.Role):
        """Add a clickable emoji to each new message."""

        config = await self.db.find_one({"_id": "role-config"})

        if config is None:
            await self.db.insert_one({"_id": "role-config", "emoji": {}})

            config = await self.db.find_one({"_id": "role-config"})

        emoji_dict = config["emoji"]

        try:
            emoji_dict[str(emoji.id)]
            failed = True
        except KeyError:
            failed = False

        if failed:
            return await ctx.send("That emoji already assigns a role.")

        emoji_dict[f"<:{emoji.name}:{emoji.id}>"] = role.name

        await self.db.update_one(
            {"_id": "role-config"}, {"$set": {"emoji": emoji_dict}}
        )

        await ctx.send(
            f'I successfully pointed <:{emoji.name}:{emoji.id}> to "{role.name}"'
        )

    @role.command(name="remove")
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def remove(self, ctx, emoji: discord.Emoji):
        """Remove a clickable emoji from each new message."""

        config = await self.db.find_one({"_id": "role-config"})

        if config is None:
            return await ctx.send("There are no emoji set for this server.")

        emoji_dict = config["emoji"]

        try:
            del emoji_dict[f"<:{emoji.name}:{emoji.id}>"]
        except KeyError:
            return await ctx.send("That emoji is not configured")

        await self.db.update_one(
            {"_id": "role-config"}, {"$set": {"emoji": emoji_dict}}
        )

        await ctx.send(f"I successfully deleted <:{emoji.name}:{emoji.id}>.")

    @Cog.listener()
    async def on_thread_ready(self, thread):
        message = thread.genesis_message

        try:
            for k, v in (await self.db.find_one({"_id": "role-config"}))[
                "emoji"
            ].items():
                await message.add_reaction(k)
        except TypeError:
            return

        self.ids.append(str(message.id))
        await self.update_db()

    @Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):

        await asyncio.sleep(1)

        if str(payload.message_id) not in self.ids:
            return

        guild: discord.Guild = self.bot.main_guild

        if payload.user_id == self.bot.user.id:
            return

        member_id = int(guild.get_channel(payload.channel_id).topic[9:])

        role = (await self.db.find_one({"_id": "role-config"}))["emoji"][
            f"<:{payload.emoji.name}:{payload.emoji.id}>"
        ]

        role = discord.utils.get(guild.roles, name=role)

        if role is None:
            return await guild.get_channel(payload.channel_id).send(
                "I couldn't find that role..."
            )

        for m in guild.members:
            if m.id == member_id:
                member = m
            else:
                continue

        await member.add_roles(role)
        await guild.get_channel(payload.channel_id).send(
            f"Successfully added {role} to {member.name}"
        )

    @Cog.listener()
    async def on_raw_reaction_remove(self, payload):

        await asyncio.sleep(1)

        if str(payload.message_id) not in self.ids:
            return

        guild = self.bot.main_guild

        member_id = int(guild.get_channel(payload.channel_id).topic[9:])

        role = (await self.db.find_one({"_id": "role-config"}))["emoji"][
            f"<:{payload.emoji.name}:{payload.emoji.id}>"
        ]

        role = discord.utils.get(guild.roles, name=role)

        if role is None:
            return await guild.get_channel(payload.channel_id).send(
                "Configured role not found."
            )

        for m in guild.members:
            if m.id == member_id:
                member = m
            else:
                continue

        await member.remove_roles(role)
        await guild.get_channel(payload.channel_id).send(
            f"Successfully removed {role} from {member.name}"
        )


def setup(bot):
    bot.add_cog(RoleAssignment(bot))
