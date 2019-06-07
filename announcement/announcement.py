import discord
import typing
import re
from discord.ext import commands

from core import checks
from core.models import PermissionLevel


class AnnoucementPlugin(commands.Cog):
    """
    Easily Make plain text or Embedded Announcements
    """

    def __init__(self, bot):
        self.bot = bot
        self.db = bot.plugin_db.get_partition(self)

    @commands.group(aliases=["a"], invoke_without_command=True)
    @commands.guild_only()
    @checks.has_permissions(PermissionLevel.REGULAR)
    async def announcement(self, ctx: commands.Context):
        """
        Make Announcements Easily
        """
        await ctx.send_help(ctx.command)

    @announcement.command()
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def start(self, ctx: commands.Context,role: typing.Optional[discord.Role]):
        """
        Start an interactive session to make announcement
        Give the role in the command if you wanna mention any

        **Example:**
        __Announcement With Role Mention:__
        {prefix}announcement start everyone

        __Announcement Without Role Mention__
        {prefix}announcement start
        """

        role_mention = f"<@&{role.id}>" if role else ""

        # TODO: Make use of reactions
        def check(msg: discord.Message):
            return ctx.author == msg.author and ctx.channel == msg.channel

        # def check_reaction(reaction: discord.Reaction, user: discord.Member):
        #     return ctx.author == user and (str(reaction.emoji == "✅") or str(reaction.emoji) == "❌")

        def title_check(msg: discord.Message):
            return (
                ctx.author == msg.author
                and ctx.channel == msg.channel
                and (len(msg.content) < 256)
            )

        def description_check(msg: discord.Message):
            return (
                ctx.author == msg.author
                and ctx.channel == msg.channel
                and (len(msg.content) < 2048)
            )

        def footer_check(msg: discord.Message):
            return (
                ctx.author == msg.author
                and ctx.channel == msg.channel
                and (len(msg.content) < 2048)
            )

        # def author_check(msg: discord.Message):
        #     return (
        #             ctx.author == msg.author and ctx.channel == msg.channel and (len(msg.content) < 256)
        #     )

        def cancel_check(msg: discord.Message):
            if msg.content == "cancel" or msg.content == f"{ctx.prefix}cancel":
                return True
            else:
                return False

        if role:
            guild: discord.Guild = ctx.guild
            grole: discord.Role = guild.get_role(role.id)
            await grole.edit(mentionable=True)

        await ctx.send("Starting an interactive process to make an announcement")

        await ctx.send(
            embed=await self.generate_embed("Do you want it to be an embed? `[y/n]`")
        )

        embed_res: discord.Message = await self.bot.wait_for("message", check=check)
        if cancel_check(embed_res) is True:
            await ctx.send("Cancelled!")
            return
        elif cancel_check(embed_res) is False and embed_res.content.lower() == "n":
            await ctx.send(
                embed=await self.generate_embed(
                    "Okay, Lets do a no-embed announcement."
                    "\nWhat's The Announcement?"
                )
            )
            announcement = await self.bot.wait_for("message", check=check)
            if cancel_check(announcement) is True:
                await ctx.send("Cancelled!")
                return
            else:
                await ctx.send(
                    embed=await self.generate_embed(
                        "In which channel should I send the announcement?"
                    )
                )
                channel: discord.Message = await self.bot.wait_for(
                    "message", check=check
                )
                if cancel_check(channel) is True:
                    await ctx.send("Cancelled!")
                    return
                else:
                    if channel.channel_mentions[0] is None:
                        await ctx.send("Cancelled as no channel was provided")
                        return
                    else:
                        await channel.channel_mentions[0].send(
                            f"{role_mention}\n{announcement.content}"
                        )
        elif cancel_check(embed_res) is False and embed_res.content.lower() == "y":
            embed = discord.Embed()
            await ctx.send(
                embed=await self.generate_embed(
                    "Should the embed have an title? `[y/n]`"
                )
            )
            t_res = await self.bot.wait_for("message", check=check)
            if cancel_check(t_res) is True:
                await ctx.send("Cancelled")
                return
            elif cancel_check(t_res) is False and t_res.content.lower() == "y":
                await ctx.send(
                    embed=await self.generate_embed(
                        "What should be the title of the embed?"
                        "\n**Must not exceed 256 characters**"
                    )
                )
                tit = await self.bot.wait_for("message", check=title_check)
                embed.title = tit.content
            await ctx.send(
                embed=await self.generate_embed(
                    "Will the embed have an description?`[y/n]`"
                )
            )
            d_res: discord.Message = await self.bot.wait_for("message", check=check)
            if cancel_check(d_res) is True:
                await ctx.send("Cancelled")
                return
            elif cancel_check(d_res) is False and d_res.content.lower() == "y":
                await ctx.send(
                    embed=await self.generate_embed(
                        "What should be the description of the embed?"
                        "\n**Must not exceed 2048 characters**"
                    )
                )
                des = await self.bot.wait_for("message", check=description_check)
                embed.description = des.content

            await ctx.send(
                embed=await self.generate_embed(
                    "Will the embed have a thumbnail?`[y/n]`"
                )
            )
            th_res: discord.Message = await self.bot.wait_for("message", check=check)
            if cancel_check(th_res) is True:
                await ctx.send("Cancelled")
                return
            elif cancel_check(th_res) is False and th_res.content.lower() == "y":
                await ctx.send(
                    embed=await self.generate_embed(
                        "What should be the thumbnail of the embed?Give a " "valid URL"
                    )
                )
                thu = await self.bot.wait_for("message", check=check)
                embed.set_thumbnail(url=thu.content)

            await ctx.send(
                embed=await self.generate_embed("Will the embed have a footer?`[y/n]`")
            )
            f_res: discord.Message = await self.bot.wait_for("message", check=check)
            if cancel_check(f_res) is True:
                await ctx.send("Cancelled")
                return
            elif cancel_check(f_res) is False and f_res.content.lower() == "y":
                await ctx.send(
                    embed=await self.generate_embed(
                        "What should be the footer of the embed?"
                        "\n**Must not exceed 2048 characters**"
                    )
                )
                foo = await self.bot.wait_for("message", check=footer_check)
                embed.set_footer(text=foo.content)

            await ctx.send(
                embed=await self.generate_embed("Do you want it to have a color?`[y/n]`")
            )
            c_res: discord.Message = await self.bot.wait_for("message", check=check)
            if cancel_check(c_res) is True:
                await ctx.send("Cancelled!")
                return
            elif cancel_check(c_res) is False and c_res.content.lower() == "y":
                await ctx.send(
                    embed=await self.generate_embed(
                        "What Colour should the embed have? "
                        "Please provide a valid hex color"
                    )
                )
                colo = await self.bot.wait_for("message", check=check)
                if cancel_check(colo) is True:
                    await ctx.send("Cancelled!")
                    return
                else:
                    match = re.search(
                        r"^#(?:[0-9a-fA-F]{3}){1,2}$", colo.content
                    )  # uwu thanks stackoverflow
                    if match:
                        embed.colour = int(
                            colo.content.replace("#", "0x"), 0
                        )  # Basic Computer Science
                    else:
                        await ctx.send(
                            "Failed! Not a valid hex color, get yours from "
                            "https://www.google.com/search?q=color+picker"
                        )
                        return

            await ctx.send(
                embed=await self.generate_embed(
                    "In which channel should I send the announcement?"
                )
            )
            channel: discord.Message = await self.bot.wait_for("message", check=check)
            if cancel_check(channel) is True:
                await ctx.send("Cancelled!")
                return
            else:
                if channel.channel_mentions[0] is None:
                    await ctx.send("Cancelled as no channel was provided")
                    return
                else:
                    schan = channel.channel_mentions[0]
            await ctx.send(
                "Here is how the embed looks like: Send it? `[y/n]`", embed=embed
            )
            s_res = await self.bot.wait_for("message", check=check)
            if cancel_check(s_res) is True or s_res.content.lower() == "n":
                await ctx.send("Cancelled")
                return
            else:
                await schan.send(f"{role_mention}", embed=embed)
        if role:
            guild: discord.Guild = ctx.guild
            grole: discord.Role = guild.get_role(role.id)
            if grole.mentionable is True:
                await grole.edit(mentionable=False)

    @announcement.command(aliases=["native", "n", "q"])
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def quick(
        self,
        ctx: commands.Context,
        channel: discord.TextChannel,
        role: typing.Optional[discord.Role],
        *,
        msg: str,
    ):
        """
        An Old way of making announcements

        **Usage:**
        {prefix}announcement quick #channel <OPTIONAL role> message
        """
        if role:
            guild: discord.Guild = ctx.guild
            grole: discord.Role = guild.get_role(role.id)
            await grole.edit(mentionable=True)

        role_mention = f"<@&{role.id}>" if role else ""

        await channel.send(f"{role_mention}\n{msg}")

        if role:
            guild: discord.Guild = ctx.guild
            grole: discord.Role = guild.get_role(role.id)
            if grole.mentionable is True:
                await grole.edit(mentionable=False)

    @commands.Cog.listener()
    async def on_ready(self):
        async with self.bot.session.post(
            "https://counter.modmail-plugins.ionadev.ml/api/instances/announcement",
            json={"id": self.bot.user.id},
        ):
            print("Posted to Plugin API")

    @staticmethod
    async def generate_embed(description: str):
        embed = discord.Embed()
        embed.colour = discord.Colour.blurple()
        embed.description = description

        return embed


def setup(bot):
    bot.add_cog(AnnoucementPlugin(bot))
