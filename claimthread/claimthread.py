import typing
import discord
from discord.ext import commands

from core import checks
from core.models import PermissionLevel


class ClaimThreadPlugin(commands.Cog):
    """
    Let support members claim the threads
    """

    def __init__(self, bot):
        self.bot = bot
        self.db = bot.plugin_db.get_partition(self)
        self.staff_cat = {}
        bot.loop.create_task(self._set_db())

    async def _set_db(self):
        config = await self.db.find_one({"_id": "config"})
        if config is None:
            await self.db.find_one_and_update(
                {"_id": "config"}, {"$set": {"cat_ids": dict()}}, upsert=True,
            )

        self.staff_cat = config.get("cat_ids", {})

    async def _update_db(self):
        await self.db.find_one_and_update(
            {"_id": "config"}, {"$set": {"cat_ids": self.staff_cat}}, upsert=True,
        )

    @commands.command(name="create_categories")
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def create_categories(
        self, ctx: commands.Context, someone: typing.Union[discord.Role, discord.User]
    ):
        """
        Create categories for support members
        """
        if isinstance(someone, discord.Role):
            for member in someone.members:
                if str(member.id) in self.staff_cat:
                    continue

                category: discord.CategoryChannel = await ctx.guild.create_category_channel(
                    str(member),
                    overwrites={
                        ctx.guild.default_role: discord.PermissionOverwrite(
                            read_messages=False
                        ),
                        ctx.guild.get_member(member.id): discord.PermissionOverwrite(
                            read_messages=True
                        ),
                    },
                )
                self.staff_cat[str(member.id)] = category.id
                await self._update_db()
            await ctx.send("Done")
            return
        elif isinstance(someone, discord.User):
            if str(someone.id) in self.staff_cat:
                await ctx.send("Already exists")
                return

            category: discord.CategoryChannel = await ctx.guild.create_category_channel(
                str(someone),
                overwrites={
                    ctx.guild.default_role: discord.PermissionOverwrite(
                        read_messages=False
                    ),
                    ctx.guild.get_member(someone.id): discord.PermissionOverwrite(
                        read_messages=True
                    ),
                },
            )
            self.staff_cat[str(someone.id)] = category.id
            await self._update_db()
            await ctx.send("Done")
            return

    @commands.command(name="claim")
    @checks.thread_only()
    @checks.has_permissions(PermissionLevel.SUPPORTER)
    async def claim(self, ctx: commands.Context):
        """
        Claim this thread
        """
        if str(ctx.author.id) not in self.staff_cat:
            await ctx.send("Set up yourself first")
            return

        dupe_message = ctx.message
        dupe_message.content = f"{str(ctx.author)} claimed thi thread."

        await ctx.thread.note(dupe_message)
        await ctx.channel.edit(
            category=ctx.guild.get_channel(self.staff_cat[str(ctx.author.id)]),
            sync_permissions=True,
            reason=f"{str(ctx.author)} claimed this thread",
        )
        return

    @commands.command(name="allow")
    @checks.has_permissions(PermissionLevel.SUPPORTER)
    async def allow(self, ctx: commands.Context, member: discord.Member):
        """
        Allow an user to join the thread
        """
        if str(ctx.author.id) not in self.staff_cat:
            await ctx.send("Set up yourself first")
            return

        await ctx.channel.edit(
            overwrites={
                ctx.guild.default_role: discord.PermissionOverwrite(
                    read_messages=False
                ),
                member: discord.PermissionOverwrite(read_messages=True),
            }
        )

        await ctx.send("Done")
        return

    @commands.command(name="remove")
    @checks.has_permissions(PermissionLevel.SUPPORTER)
    async def remove(self, ctx: commands.Context, member: discord.Member):
        """
        Remove an user from the thread
        """
        if str(ctx.author.id) in self.staff_cat:
            await ctx.send("Set up yourself first")
            return

        await ctx.channel.edit(
            overwrites={
                ctx.guild.default_role: discord.PermissionOverwrite(
                    read_messages=False
                ),
                member: discord.PermissionOverwrite(read_messages=False),
            }
        )

        await ctx.send("Done")
        return

    @commands.Cog.listener()
    async def on_user_update(self, before: discord.User, after: discord.User):
        if str(before.id) in self.staff_cat:
            category: discord.CategoryChannel = self.bot.get_channel(
                self.staff_cat[str(before.id)]
            )
            await category.edit(
                name=str(after),
                reason=f"Changed username from {str(before)} to {str(after)}",
            )
            return


def setup(bot):
    bot.add_cog(ClaimThreadPlugin(bot))
