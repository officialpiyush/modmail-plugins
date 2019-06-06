import discord
import re
from discord.ext import commands


class GithubPlugin(commands.Cog):
    def init(self, bot):
        self.bot = bot
        self.colors = {
            "pr": {"open": 0x2CBE4E, "closed": 0xCB2431, "merged": 0x6F42C1},
            "issues": {"open": 0xD1D134, "closed": 0x2D32BE},
        }
        self.regex = r"modmail#(\d+)"

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        match = re.match(self.regex, msg.content)
        if match:
            num = match.group(1)
            async with self.bot.session.get(
                f"https://api.github.com/repos/kyb3r/modmail/pulls/{num}"
            ) as prr:
                prj = await prr.json()
                if "message" not in prj:
                    e = await self.handlePR(prj)
                    await msg.channel.send(embed=e)
                    return
                else:
                    async with self.bot.session.get(
                        f"https://api.github.com/repos/kyb3r/modmail/issues/{num}"
                    ) as err:
                        erj = await err.json()
                        if "message" in erj and erj["message"] == "Not Found":
                            await msg.channel.send(embed=discord.Embed(
                                colour=discord.Colour.red(),
                                description="Issue/PR not found."
                            ))
                            return
                        else:
                            e = await self.handleIssue(erj)
                            await msg.channel.send(embed=e)
                            return

    async def handlePR(self, data):
        state = (
            "merged"
            if (data["state"] == "closed" and data["merged"])
            else data["state"]
        )
        embed = self._base(data)
        embed.colour = self.colors["pr"][state]
        embed.add_field(name="**Additions**", value=data["additions"])
        embed.add_field(name="**Deletions**", value=data["deletions"])
        embed.add_field(name="**Commits**", value=data["commits"])
        # embed.set_footer(text=f"Pull Request #{data['number']}")
        return embed

    async def handleIssue(self, data):
        embed = self._base(data)
        embed.colour = self.colors["issues"][data["state"]]
        # embed.set_footer(text=f"Issue #{data['number']}")
        return embed

    def _base(self, data):
        description = (
            f"{data['body'].slice(0, 2045)}..."
            if len(data["body"]) > 2048
            else data["body"]
        )

        rtitle = f"[kyb3r/modmail] #{data['number']}: {data['title']}"
        title = (
            f"{rtitle.slice(0, 253)}..."
            if len(rtitle) > 256
            else rtitle
        )
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
        embed.add_field(name="**Status**", value=data["state"], inline=True)
        if len(data["labels"]) > 0:
            embed.add_field(
                name="**Labels**",
                value=", ".join(str(label["name"]) for label in data["labels"]),
            )
        return embed


def setup(bot):
    bot.add_cog(GithubPlugin(bot))
