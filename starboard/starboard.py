import asyncio
from datetime import datetime
import discord
from discord.ext import commands

from core import checks
from core.models import PermissionLevel


class StarboardPlugin(commands.Cog):
    """
    A starboard is a popular feature in bots that serve as a channel of messages that users of the server find funny, stupid, or both.
    With this plugin, you can add starboard service to your Modmail bot.
    """

    def __init__(self, bot):
        self.bot: discord.Client = bot
        self.db = bot.plugin_db.get_partition(self)
        self.channel = None
        self.stars = 2
        self.user_blacklist = list()
        self.channel_blacklist = list()
        asyncio.create_task(self._set_val())

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
            return

        self.channel = config["channel"]
        self.stars = config["stars"]
        self.user_blacklist = config["blacklist"]["user"]
        self.channel_blacklist = config["blacklist"]["channel"]

    @commands.group(aliases=["st"])
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def starboard(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help()

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
            self.user_blacklist.pop(str(member.id))
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
            self.channel_blacklist.pop(str(channel.id))
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
        await self.handleReaction(payload=payload)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        await self.handleReaction(payload=payload)

    async def handleReaction(self, payload: discord.RawReactionActionEvent):
        config = await self.db.find_one({"_id": "config"})

        if config is None or self.channel is None:
            return

        if (
            str(payload.channel_id) in self.channel_blacklist
            or str(payload.user_id) in self.user_blacklist
        ):
            return

        guild: discord.Guild = self.bot.get_guild(int(self.bot.config["guild_id"]))
        starboard_channel: discord.TextChannel = guild.get_channel(int(self.channel))
        channel: discord.TextChannel = guild.get_channel(int(payload.channel_id))
        user: discord.User = await self.bot.fetch_user(payload.user_id)

        if channel is None or starboard_channel is None:
            return

        message: discord.Message = await channel.fetch_message(payload.message_id)

        if message.author.id == payload.user_id:
            return

        if message.reactions[0] is None:
            return

        for em in message.reactions:
            if em.emoji == "⭐":
                reaction: discord.Reaction = em

                # list_reaction = await reaction.users().flatten()
                count = reaction.count

                if count < self.stars:
                    should_delete = True
                else:
                    should_delete = False

                messages = await starboard_channel.history(
                    limit=30, around=message.created_at
                ).flatten()

                for mesg in messages:
                    if not mesg.embeds or mesg.embeds[0] is None:
                        continue

                    if (
                        mesg.embeds[0].footer.text is None
                        or "⭐" in mesg.embeds[0].footer.text
                    ):
                        continue

                    if mesg.embeds[0].footer.text.endswith(str(payload.message_id)):
                        msg: discord.Message = mesg
                        break
                        # re_res = re.search(r'^\⭐\s([0-9]{1,3})\s\|\s([0-9]{17,20})', message.embeds[0].footer.text)
                        # if (re_res):
                        #     arr = [s for s in re_res.groups()]
                        #     stars = arr[0]
                        #     break

                if msg:
                    if should_delete:
                        await msg.delete()
                        return
                    else:
                        msg.embeds[0].footer.text = f"⭐ {count} | {payload.message_id}"

                else:
                    if should_delete:
                        return
                    embed = discord.Embed(
                        color=discord.Colour.gold(),
                        description=msg.content,
                        timestamp=datetime.utcnow(),
                    )
                    embed.set_author(
                        name=f"{user.name}#{user.discriminator}",
                        icon_url=user.avatar_url,
                    )
                    embed.set_footer(text=f"⭐ {count} | {payload.message_id}")
                    if len(msg.attachments) > 1:
                        try:
                            embed.set_image(url=msg.attachments[0].url)
                        except:
                            pass
                    await starboard_channel.send(f"{channel.mention}", embed=embed)
                    return


def setup(bot):
    bot.add_cog(StarboardPlugin(bot))
