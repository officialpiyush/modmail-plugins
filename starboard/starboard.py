from datetime import datetime

import discord
from discord import Client
from discord.ext import commands
from pymongo.collection import Collection

from core import checks
from core.models import PermissionLevel, getLogger

logger = getLogger(__name__)


class Starboard(commands.Cog):
    def __init__(self, bot):
        self.bot: Client = bot
        self.db: Collection = bot.plugin_db.get_partition(self)
        self.channel = None
        self.stars = 2
        self.user_blacklist: list = list()
        self.channel_blacklist: list = list()
        self.bot.loop.create_task(self._set_val())

    async def _update_db(self):
        await self.db.find_one_and_update(
            {"_id": "config"},
            {
                "$set": {
                    "channel": self.channel,
                    "stars": self.stars,
                    "blacklist": {
                        "user": self.user_blacklist,
                        "channel": self.channel_blacklist,
                    },
                }
            },
            upsert=True,
        )

    async def _set_val(self):
        config = await self.db.find_one({"_id": "config"})

        if config is None:
            await self._update_db()
            return

        self.channel = config.get("channel", None)
        self.stars = config.get("stars", 2)
        self.user_blacklist = config["blacklist"]["user"]
        self.channel_blacklist = config["blacklist"]["channel"]

    @commands.group(aliases=["st", "sb"], invoke_without_command=True)
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def starboard(self, ctx: commands.Context):
        await ctx.send_help(ctx.command)

    @starboard.command(aliases=["setchannel", "setch", "sc"])
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """
        Set the starboard channel where the messages will go
        **Usage:**
        starboard channel **#this-is-a-channel**
        """
        self.channel = str(channel.id)
        await self._update_db()

        await ctx.send(f"Done! {channel.mention} is the Starboard Channel now!")

    @starboard.command(aliases=["setstars", "ss"])
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def stars(self, ctx: commands.Context, stars: int):
        """
        Set the number of stars the message needs to appear on the starboard channel
        **Usage:**
        starboard stars 2
        """
        self.stars = stars
        await self._update_db()

        await ctx.send(
            f"Done.Now this server needs `{stars}` :star: to appear on the starboard channel."
        )

    @starboard.group()
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def blacklist(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help()

    @blacklist.command(aliases=["user"])
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def member(self, ctx: commands.Context, member: discord.Member):
        """
        Blacklist a user so that the user's reaction dosen't get counted
        **Usage:**
        starboard blacklist member @user
        """

        if str(member.id) in self.user_blacklist:
            self.user_blacklist.remove(str(member.id))
            removed = True
        else:
            self.user_blacklist.append(str(member.id))
            removed = False

        await ctx.send(
            f"{'Un' if removed else None}Blacklisted **{member.name}#{member.discriminator}**"
        )
        return

    @blacklist.command(name="channel")
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def blacklist_channel(
            self, ctx: commands.Context, channel: discord.TextChannel
    ):
        """
        Blacklist Channels so that messages sent in those channels dont appear on starboard
        **Usage:**
        starboard blacklist channel **#channel**
        """
        if str(channel.id) in self.channel_blacklist:
            self.channel_blacklist.remove(str(channel.id))
            await self._update_db()
            removed = True
        else:
            self.channel_blacklist.append(str(channel.id))
            await self._update_db()
            removed = False

        await ctx.send(f"{'Un' if removed else None}Blacklisted {channel.mention}")
        return

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        await self.handle_reaction(payload=payload)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        await self.handle_reaction(payload=payload)

    async def handle_reaction(self, payload: discord.RawReactionActionEvent):
        config = await self.db.find_one({"_id": "config"})

        if not config or not self.channel:
            logger.info("No config or channel")
            return

        # check for blacklist
        if self.channel_blacklist.__contains__(str(payload.channel_id)) or self.user_blacklist.__contains__(
                str(payload.user_id)):
            logger.info("Blacklisted")
            return

        guild: discord.Guild = self.bot.get_guild(int(self.bot.config["guild_id"]))
        starboard_channel: discord.TextChannel = guild.get_channel(int(self.channel))
        channel: discord.TextChannel = guild.get_channel(payload.channel_id)
        user: discord.User = await self.bot.fetch_user(payload.user_id)

        if not channel or not starboard_channel:
            logger.info("No channel found")
            return

        message: discord.Message = await channel.fetch_message(payload.message_id)

        if message.author.id == payload.user_id:
            logger.info("Author added the reaction")
            return

        found_emote = False
        for emote in message.reactions:
            if emote.emoji == "⭐":
                found_emote = True
                reaction: discord.Reaction = emote
                count = reaction.count

                should_delete = False

                if count < self.stars:
                    should_delete = True

                messages = await starboard_channel.history(
                    limit=70,
                    around=message.created_at
                ).flatten()
                found = False

                for msg in messages:
                    if len(msg.embeds) <= 0:
                        logger.info("No embeds")
                        continue

                    if not msg.embeds[0].footer or not msg.embeds[0].footer.text or "⭐" not in msg.embeds[
                        0].footer.text:
                        print(msg.embeds)
                        logger.info("No stars")
                        continue

                    if msg.embeds[0].footer.text.endswith(str(payload.message_id)):
                        logger.info("got one")
                        found = True
                        if should_delete:
                            logger.info("delete message")
                            await msg.delete()
                            break
                        e = msg.embeds[0]
                        e.set_footer(text=f"⭐ {count} | {payload.message_id}")
                        await msg.edit(content=f"<#{payload.channel_id}>", embed=e)
                        break

                if not found:
                    if should_delete:
                        logger.info("Should Delete")
                        return

                    embed = discord.Embed(
                        color=discord.Colour.gold(),
                        description=message.content,
                        timestamp=datetime.utcnow(),
                        title="Jump to message ►",
                        url=message.jump_url
                    )
                    embed.set_author(
                        name=f"{user.name}#{user.discriminator}",
                        icon_url=user.avatar_url,
                    )
                    embed.set_footer(text=f"⭐ {count} | {payload.message_id}")
                    if len(message.attachments) > 1:
                        try:
                            embed.set_image(url=message.attachments[0].url)
                        except:
                            pass

                    await starboard_channel.send(
                        f"{channel.mention}", embed=embed
                    )

        if not found_emote:
            messages = await starboard_channel.history(
                limit=70,
                around=message.created_at
            ).flatten()
            found = False

            for msg in messages:
                if len(msg.embeds) <= 0:
                    logger.info("No embeds")
                    continue

                if not msg.embeds[0].footer or not msg.embeds[0].footer.text or "⭐" not in msg.embeds[0].footer.text:
                    print(msg.embeds)
                    logger.info("No stars")
                    continue

                if msg.embeds[0].footer.text.endswith(str(payload.message_id)):
                    logger.info("got one")
                    found = True
                    await msg.delete()


def setup(bot):
    bot.add_cog(Starboard(bot))
