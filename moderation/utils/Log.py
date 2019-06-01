import discord


class Log:
    def __init__(self, guild: discord.Guild, db):
        self.guild: discord.Guild = guild
        self.db = db
        self.channel = None

    async def _set_channel(self):
        config = await self.db.find_one({"_id": "config"})
        if config is None or config["channel"] is None:
            return
        self.channel: discord.TextChannel = await self.guild.get_channel(
            int(config["channel"])
        )

    async def log(
        self, type: str, user: discord.User, mod: discord.User, *, reason: str
    ):
        if self.channel is None:
            return f"No Log Channel has been setup for {self.guild.name}"
        else:
            embed = discord.Embed()
            embed.set_author(name=f"{type} | {user.name}#{user.discriminator}")
            embed.add_field(
                name="User", value=f"<@{user.id}> `({user.name}#{user.discriminator})`"
            )
