# Copyright (c) 2015 Rapptz
from discord.ext import commands
import discord
import asyncio
import datetime

from core import checks
from core.models import PermissionLevel


def to_emoji(c):
    base = 0x1F1E6
    return chr(base + c)


class Polls(commands.Cog):
    """Poll voting system."""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="poll", invoke_without_command=True)
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def poll(self, ctx: commands.Context):
        """Easily create Polls."""
        await ctx.send_help(ctx.command)

    @poll.command()
    @commands.guild_only()
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def start(self, ctx, *, question):
        """Interactively creates a poll with the following question.

        To vote, use reactions!
        """
        perms = ctx.channel.permissions_for(ctx.me)
        if not perms.add_reactions:
            return await ctx.send("Need Add Reactions permissions.")

        # a list of messages to delete when we're all done
        messages = [ctx.message]
        answers = []

        def check(m):
            return (
                m.author == ctx.author
                and m.channel == ctx.channel
                and len(m.content) <= 100
            )

        for i in range(20):
            messages.append(
                await ctx.send(
                    f"Say a Poll option or {ctx.prefix}done to publish the Poll."
                )
            )

            try:
                entry = await self.bot.wait_for("message", check=check, timeout=60.0)
            except asyncio.TimeoutError:
                break

            messages.append(entry)

            if entry.clean_content.startswith(f"{ctx.prefix}done"):
                break

            answers.append((to_emoji(i), entry.clean_content))

        try:
            await ctx.channel.delete_messages(messages)
        except:
            pass  # oh well

        answer = "\n".join(f"{keycap}: {content}" for keycap, content in answers)
        embed = discord.Embed(
            color=self.bot.main_color,
            timestamp=datetime.datetime.utcnow(),
            description=f"**{question}**\n{answer}",
        )
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
        poll = await ctx.send(embed=embed)
        for emoji, _ in answers:
            await poll.add_reaction(emoji)

    @start.error
    async def poll_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send("Missing the question.")

    @poll.command()
    @commands.guild_only()
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def quick(self, ctx, *questions_and_choices: str):
        """Makes a poll quickly.
        The first argument is the question and the rest are the choices.
        for example: `?poll quick "Green or Light Green?" Green "Light Green"`

        or it can be a simple yes or no poll, like:
        `?poll quick "Do you watch Anime?"`
        """

        if len(questions_and_choices) == 0:
            return await ctx.send("You need to specify a question.")
        elif len(questions_and_choices) == 2:
            return await ctx.send("You need at least 2 choices.")
        elif len(questions_and_choices) > 21:
            return await ctx.send("You can only have up to 20 choices.")

        perms = ctx.channel.permissions_for(ctx.me)
        if not perms.add_reactions:
            return await ctx.send("Need Add Reactions permissions.")
        try:
            await ctx.message.delete()
        except:
            pass
        question = questions_and_choices[0]

        if len(questions_and_choices) == 1:
            embed = discord.Embed(
                color=self.bot.main_color, description=f"**{question}**"
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
            poll = await ctx.send(embed=embed)
            reactions = ["👍", "👎"]
            for emoji in reactions:
                await poll.add_reaction(emoji)

        else:
            choices = [
                (to_emoji(e), v) for e, v in enumerate(questions_and_choices[1:])
            ]

            body = "\n".join(f"{key}: {c}" for key, c in choices)
            embed = discord.Embed(
                color=self.bot.main_color,
                timestamp=datetime.datetime.utcnow(),
                description=f"**{question}**\n{body}",
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
            poll = await ctx.send(embed=embed)
            for emoji, _ in choices:
                await poll.add_reaction(emoji)


def setup(bot):
    bot.add_cog(Polls(bot))
