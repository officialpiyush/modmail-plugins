
import typing
import datetime
from discord import Embed, Emoji, Message, TextChannel, RawReactionActionEvent, utils, Guild, Member, HTTPException, Forbidden
from discord.ext import commands

from core import checks
from core.models import PermissionLevel

class ReactToContact(commands.Cog):
    """
    Make users start modmail thread by clicking an emoji
    """
    def __init__(self,bot):
        self.bot = bot
        self.db = bot.plugin_db.get_partition(self)

    @commands.command(aliases=["setmsg","smsg","smessage"])
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def setmessage(self, ctx: commands.Context, *, content: str):
        """
        Set the description of the emebd

        **Usage:**
        setmessage Click on he reaction to contact staff
        """
        if len(content) > 2048:
            await ctx.send(f"You can have only **maximum 2048** characters.\nYou entered `{len(content)}` characters, which is `{len(content) - 2048}` characters more.")
            return

        await self.db.find_one_and_update(
            {"_id": "config"},
            {"$set": {"message": content}},
            upsert=True
        )

        await ctx.send(f"Done!\nHere is the **preview** of the embed:", embed=Embed(
            color=self.bot.main_color,
            title=f"Title Will Be Here, if any. Set it using {ctx.prefix}settitle command.",
            description=content
        ))

    @commands.command()
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def settitle(self,ctx: commands.Context, *, title: str):
        """
        Set the title of the embed

        **Usage:**
        settitle Yo This is a title
        """
        if len(title) > 256:
            await ctx.send(f"You can have only **maximum 256** characters.\nYou entered `{len(title)}` characters, which is `{len(title) - 256}` characters more.")
            return

        await self.db.find_one_and_update(
            {"_id": "config"},
            {"$set": {"title": title}},
            upsert=True
        )

        await ctx.send(f"Done!\nHere is the **preview** of the embed:", embed=Embed(
            color=self.bot.main_color,
            title=title,
            description=f"`( Message Will Be Here, if any\nSet it by {ctx.prefix}setmsg )`"
        ))

    @commands.command()
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def setreaction(self, ctx, emoji: Emoji):
        """
        Set the emoji which the bot would react, and get the reactions on the message

        **Custom Emoji Only**

        """

        id = emoji.id

        await self.db.find_one_and_update(
            {"_id": "config"},
            {"$set": {"emoji": id}},
            upsert=True
        )

        msg: Message = await ctx.send(f"Done! Bot will react on this msg to preview")

        guild: Guild = ctx.guild
        emote = await guild.fetch_emoji(emoji.id)
        await msg.add_reaction(emote)
        return


    @commands.command()
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def sendembed(self, ctx: commands.Context, channel: typing.Optional[TextChannel]):
        """
        Send The Embed To The Channel
        """
        config = await self.db.find_one({"_id": "config"})

        if config is None:
            await ctx.send(
                f"You haven't set the emoji or the message of the embed. Set it up first with `{ctx.prefix}setmessage` "
                f"and `{ctx.prefix}setreaction` command.")
            return

        if config["emoji"] is None or config["message"] is None:
            await ctx.send(f"Either you haven't set the emoji or the message of the embed. Set it up first with `{ctx.prefix}setmessage` and `{ctx.prefix}setreaction` command.")
            return

        embed = Embed(
            color=self.bot.main_color,
            description=config["message"]
        )

        if config["title"]:
            embed.title = config["title"]

        await ctx.message.delete()

        if channel:
            msg: Message = await channel.send(embed=embed)
        else:
            msg: Message = await ctx.send(embed=embed)

        await self.db.find_one_and_update(
            {"_id": "config"},
            {"$set": {"channel": msg.channel.id,"mid": msg.id}},
            upsert=True
        )
        guild: Guild = ctx.guild
        emote = await guild.fetch_emoji(config["emoji"])
        await msg.add_reaction(emote)
        return


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        config = await self.db.find_one({"_id": "config"})

        if config is None:
            return

        if config["emoji"] is None or (config["emoji"] != payload.emoji.id):
            return

        if config["channel"] is None or (payload.channel_id != config["channel"]):
            return

        if config["mid"] is None or (payload.message_id != config["mid"]):
            return

        guild: Guild = utils.find(lambda g: g.id == payload.guild_id, self.bot.guilds)

        member: Member = guild.get_member(payload.user_id)

        channel = guild.get_channel(int(config["channel"]))

        msg: Message = await channel.fetch_message(int(config["mid"]))

        await msg.remove_reaction(payload.emoji, member)

        try:
            await member.send(embed=Embed(
                description="Hello, how may we help you?",
                color=self.bot.main_color,
            ))
        except (HTTPException, Forbidden):
            ch= await self.bot.get_channel(int(self.bot.config.get('log_channel_id')))

            await ch.send(embed=Embed(
                title="User Contact failed",
                description=f"**{member.name}#{member.discriminator}** tried contacting, but the bot couldnt dm him/her.",
                color=self.bot.main_color,
                timestamp=datetime.datetime.utcnow()
            ))

def setup(bot):
    bot.add_cog(ReactToContact(bot))



