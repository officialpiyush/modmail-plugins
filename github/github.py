import discord
import re
import asyncio
from discord.ext import commands

from core import checks
from core.models import PermissionLevel


class GithubPlugin(commands.Cog):
    def __init__(self, bot):
        self.bot: discord.Client = bot
        self.db = bot.plugin_db.get_partition(self)
        self.colors = {
            "pr": {
                "open": 0x2CBE4E,
                "closed": discord.Embed.Empty,
                "merged": discord.Embed.Empty,
            },
            "issues": {"open": 0xE68D60, "closed": discord.Embed.Empty},
        }
        self.repo = "kyb3r/modmail"
        asyncio.create_task(self._set_repo)
        self.regex = r"(?:^|\s)#(\d+)\b"

    async def _set_repo(self):
        config = await self.db.find_one({"_id": "config"})
        if config is None:
            return
        self.repo = config.get("repo", "kyb3r/modmail")

    async def _update(self):
        await self.db.find_one_and_update(
            {"_id": "config"}, {"$set": {"repo": self.repo}}, upsert=True
        )

    @commands.group(invoke_without_command=True)
    @checks.has_permissions(PermissionLevel.OWNER)
    async def github(self, ctx: commands.Context):
        """
		Get github project's issue / PR info from bot.
		"""
        await ctx.send_help(ctx.command)

    @github.command(aliases=["repo"])
    @checks.has_permissions(PermissionLevel.OWNER)
    async def repository(self, ctx: commands.Context, repo: str):
        """
		Set the repo on which the bot will look for issues/pr's.
		"""
        if "https://github.com" not in repo:
            await ctx.send(":x: | Not a valid repo url")
            return
        else:
            raw = repo.split("/")
            self.repo = f"{raw[-2]}/{raw[-1]}"
            await self._update()

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        def check(reaction: discord.Reaction, user: discord.User):
            return (
                msg.author.id == user.id
                and reaction.message.id == rm.id
                and reaction.emoji == "🔖"
            )

        match = re.search(self.regex, msg.content)
        if match:
            num = match.group(1)
            async with self.bot.session.get(
                f"https://api.github.com/repos/{self.repo}/pulls/{num}"
            ) as prr:
                prj = await prr.json()
                if "message" not in prj:
                    rm = await msg.add_reaction("🔖")
                    try:
                        has_reacted = await self.bot.wait_for(
                            "reaction_add", timeout=30.0, check=check
                        )
                    except asyncio.TimeoutError:
                        await msg.remove_reaction(emoji="🔖", member=self.bot.user)
                        return
                    e = await self.handlePR(prj)
                    await msg.channel.send(embed=e)
                    return
                else:
                    async with self.bot.session.get(
                        f"https://api.github.com/repos/{self.repo}/issues/{num}"
                    ) as err:
                        erj = await err.json()
                        if "message" in erj and erj["message"] == "Not Found":
                            await msg.channel.send(
                                embed=discord.Embed(
                                    colour=discord.Colour.red(),
                                    description="Issue/PR not found.",
                                )
                            )
                            return
                        else:
                            rm = await msg.add_reaction("🔖")
                            try:
                                has_reacted = await self.bot.wait_for(
                                    "reaction_add", timeout=30.0, check=check
                                )
                            except asyncio.TimeoutError:
                                await msg.remove_reaction(
                                    emoji="🔖", member=self.bot.user
                                )
                                return
                            e = await self.handleIssue(erj)
                            await msg.channel.send(embed=e)
                            return

    async def handlePR(self, data):
        state = (
            "merged"
            if (data["state"] == "closed" and data["merged"])
            else data["state"]
        )
        embed = self._base(data, issue=False)
        embed.colour = self.colors["pr"][state]
        embed.add_field(name="Additions", value=data["additions"])
        embed.add_field(name="Deletions", value=data["deletions"])
        embed.add_field(name="Commits", value=data["commits"])
        # embed.set_footer(text=f"Pull Request #{data['number']}")
        return embed

    async def handleIssue(self, data):
        embed = self._base(data)
        embed.colour = self.colors["issues"][data["state"]]
        # embed.set_footer(text=f"Issue #{data['number']}")
        return embed

    def _base(self, data, issue=True):
        description = (
            f"{data['body'].slice(0, 2045)}..."
            if len(data["body"]) > 2048
            else data["body"]
        )

        _type = "Issue" if issue else "Pull request"

        rtitle = f"[kyb3r/modmail] {_type}: #{data['number']} {data['title']}"
        title = f"{rtitle.slice(0, 253)}..." if len(rtitle) > 256 else rtitle
        embed = discord.Embed()
        # embed.set_thumbnail(url="https://images.ionadev.ml/b/8rs7vC7.png")
        embed.set_author(
            name=data["user"]["login"],
            icon_url=data["user"]["avatar_url"],
            url=data["user"]["html_url"],
        )
        embed.title = title
        embed.url = data["html_url"]
        embed.description = description
        embed.add_field(name="Status", value=data["state"], inline=True)
        if len(data["labels"]) > 0:
            embed.add_field(
                name="Labels",
                value=", ".join(str(label["name"]) for label in data["labels"]),
            )
        return embed


def setup(bot):
    bot.add_cog(GithubPlugin(bot))
