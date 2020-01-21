import discord

from discord.ext import commands

from core import checks
from core.models import PermissionLevel


class BirthdayPlugin(commands.Cog):
    """
    A birthday plugin.
    """

    def __init__(self, bot):
        self.bot = bot
        self.db = bot.plugin_db.get_partition(self)
        self.birthdays = dict()
        self.role = None
        self.channel = None
        self.timezone = "America/Chicago"
        self.message = None
        self.bot.create_task(self._set_db())

    async def _set_db(self):
        birthdays = await self.db.find_one({"_id": "birthdays"})
        config = await self.db.find_one({"_id": "config"})

        if birthday is None:
            await self.db.find_one_and_update(
                {"_id": "birthdays"}, {"$set": {"birthdays": dict()}}, upsert=True
            )

        if config is None:
            await self.db.find_one_and_update(
                {"_id": "config"},
                {
                    "$set": {
                        "role": None,
                        "channel": None,
                        "timezone": "America/Chicago",
                        "message": None,
                    }
                },
                upsert=True,
            )

        self.birthdays = birthdays.get("birthdays", dict())
        self.role = config.get("role", None)
        self.channel = config.get("channel", None)
        self.timezone = config.get("timezone", "America/Chicago")
        self.message = config.get("message", None)

    async def _update_birthdays(self):
        await self.db.find_one_and_update(
            {"_id": "birthdays"}, {"$set": {"birthdays": self.birthdays}}, upsert=True
        )

    async def _update_config(self):
        await self.db.find_one_and_update(
            {"_id": "config"},
            {
                "$set": {
                    "role": self.role,
                    "channel": self.channel,
                    "timezone": self.timezone,
                    "message": self.message,
                }
            },
            upsert=True,
        )

    @commands.group(invoke_without_command=True)
    async def birthday(self, ctx: commands.Context):
        """
        Birthday stuff.
        """

        await ctx.send_help(ctx.command)
        return

    @birthday.command()
    async def set(self, ctx: commands.Context, date: str):
        """
        Set your birthdate.

        **Format:**
        DD/MM/YYYY

        **Example:**
        {p}birthday set 26/12/2002
        """

        try:
            birthday = date.split("/")
            if int(birthday[1]) > 13:
                await ctx.send(":x: | Invalid month provided.")
                return
            birthday_obj = {}
            birthday_obj["date"] = int(birthday[0])
            birthday_obj["month"] = int(birthday[1])
            birthday_obj["year"] = int(birthday[2])
            birthday_obj["guild"] = str(ctx.guild._id)

            self.birthdays.pop[str(ctx.author.id)]
            self.birthdays[str(ctx.author.id)] = birthday_obj
            await self._update_birthdays()
            await ctx.send(f"Done! You'r birthday was set to {date}")
            return
        except KeyError:
            await ctx.send("Please check the format of the date")
            return
        except Exception as e:
            await ctx.send(f":x: | An error occurred\n```{e}```")
            return

    @birthday.command()
    async def clear(self, ctx: commands.Context):
        """
        Clear your birthday from the database.
        """

        self.birthdays.pop[str(ctx.author.id)]
        await self._update_birthdays()
        await ctx.send(f"Done!")
        return

    @birthday.command()
    @checks.has_permission(PermissionLevel.ADMIN)
    async def channel(self, ctx: command.Context, channel: discord.TextChannel):
        """
        Configure a channel for sending birthday announcements
        """

        self.channel = str(channel.id)
        await self._update_config()
        await ctx.send("Done!")
        return

    @birthday.command()
    @checks.has_permission(PermissionLevel.ADMIN)
    async def role(self, ctx: command.Context, role: discord.Role):
        """
        Configure a role which will be added to the birthay boizzzz
        """

        self.role = str(role.id)
        await self._update_config()
        await ctx.send("Done!")
        return

    @birthday.command()
    @checks.has_permission(PermissionLevel.ADMIN)
    async def message(self, ctx: command.Context, *, msg: str):
        """
        Set a message to announce when wishing someone's birthday
        """

        self.message = msg
        await self._update_config()
        await ctx.send("Done!")
        return
