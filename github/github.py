import re

import discord
from discord.ext import commands


class GithubPlugin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.colors = {
            "pr": {
                "open": 0x2CBE4E,
                "closed": discord.Embed.Empty,
                "merged": discord.Embed.Empty,
            },
            "issues": {"open": 0xE68D60, "closed": discord.Embed.Empty},
        }
        self.regex = r"(\S+)#(\d+)"

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        match = re.search(self.regex, msg.content)

        if match:
            repo = match.group(1)
            num = match.group(2)

            if repo == "modmail":
                repo = "kyb3r/modmail"
            elif repo == "logviewer":
                repo = "kyb3r/logviewer"

            async with self.bot.session.get(
                f"https://api.github.com/repos/{repo}/pulls/{num}"
            ) as prr:
                prj = await prr.json()

                if "message" not in prj:
                    em = await self.handlePR(prj, repo)
                    return await msg.channel.send(embed=em)
                else:
                    async with self.bot.session.get(
                        f"https://api.github.com/repos/{repo}/issues/{num}"
                    ) as err:
                        erj = await err.json()

                        if "message" in erj and erj["message"] == "Not Found":
                            pass
                        else:
                            em = await self.handleIssue(erj, repo)
                            return await msg.channel.send(embed=em)

    async def handlePR(self, data, repo):
        state = (
            "merged"
            if (data["state"] == "closed" and data["merged"])
            else data["state"]
        )
        embed = self._base(data, repo, issue=False)
        embed.colour = self.colors["pr"][state]
        embed.add_field(name="Additions", value=data["additions"])
        embed.add_field(name="Deletions", value=data["deletions"])
        embed.add_field(name="Commits", value=data["commits"])
        # embed.set_footer(text=f"Pull Request #{data['number']}")
        return embed

    async def handleIssue(self, data, repo):
        embed = self._base(data, repo)
        embed.colour = self.colors["issues"][data["state"]]
        # embed.set_footer(text=f"Issue #{data['number']}")
        return embed

    def _base(self, data, repo, issue=True):
        description = (
            f"{data['body'].slice(0, 2045)}..."
            if len(data["body"]) > 2048
            else data["body"]
        )

        _type = "Issue" if issue else "Pull request"

        rtitle = f"[{repo}] {_type}: #{data['number']} {data['title']}"
        title = f"{rtitle.slice(0, 253)}..." if len(rtitle) > 256 else rtitle
        embed = discord.Embed()
        # embed.set_thumbnail(url="https://images.piyush.codes/b/8rs7vC7.png")
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
