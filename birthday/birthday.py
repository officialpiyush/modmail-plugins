import asyncio
import datetime
import discord
import logging

from discord.ext import commands
from pytz import timezone

from core import checks
from core.models import PermissionLevel

logger = logging.getLogger("Modmail")

class BirthdayPlugin(commands.Cog):
    """
    A birthday plugin.
    """

    def __init__(self, bot):
        self.bot = bot
        self.db = bot.plugin_db.get_partition(self)
        self.birthdays = dict()
        self.roles = dict()
        self.channels = dict()
        self.timezone = "America/Chicago"
        self.messagess = None
        self.enabled = True
        self.booted = True
        self.bot.loop.create_task(self._set_db())

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
                        "roles": dict(),
                        "channels": dict(),
                        "enabled": True,
                        "timezone": "America/Chicago",
                        "messages": None,
                    }
                },
                upsert=True,
            )

        self.birthdays = birthdays.get("birthdays", dict())
        self.roles = config.get("roles", dict())
        self.channels = config.get("channels", dict())
        self.enabled = config.get("enabled", True)
        self.timezone = config.get("timezone", "America/Chicago")
        self.messages = config.get("messages", None)

    async def _update_birthdays(self):
        await self.db.find_one_and_update(
            {"_id": "birthdays"}, {"$set": {"birthdays": self.birthdays}}, upsert=True
        )

    async def _update_config(self):
        await self.db.find_one_and_update(
            {"_id": "config"},
            {
                "$set": {
                    "roles": self.roles,
                    "channels": self.channels,
                    "enabled": self.enabled,
                    "timezone": self.timezone,
                    "messages": self.messages,
                }
            },
            upsert=True,
        )

    async def _handle_birthdays(self):
        while True:
            if not self.enabled:
                return

            if self.booted:
                custom_timezone = timezone(self.timezone)
                now = datetime.datetime.now(custom_timezone)
                sleep_time = 86400 - (now - (datetime.datetime.combine(now.date(), datetime.time()))).seconds
                self.booted = False
                await asyncio.sleep(sleep_time)
                continue

            today = now.strftime("%d/%m/%Y").split("/")

            for user, obj in self.birthdays.keys():
                if obj["month"] != today[1] or obj["day"] != today[0]:
                    continue
                guild = self.bot.get_guild(int(obj["guild"]))
                if guild is None:
                    continue
                member = guild.get_member(int(user))
                if member is None:
                    continue

                if self.roles[obj["guild"]]:
                    role = guild.get_role(int(self.roles[obj["guild"]]))
                    if role:
                        await member.add_roles(role, reason="Birthday Boi")

                if self.messages[obj["guild"]] and self.channels[obj["guild"]]:
                    channel = guild.get_channel(int(self.channels[obj["guild"]]))
                    if channel is None:
                        continue
                    age = today[2] - year[2]
                    await channel.send(self.messages[obj["guild"]].replace("{user.mention}", member.mention).replace("{user}", str(member)).replcae("{age}", age))
                    continue

            custom_timezone = timezone(self.timezone)
            now = datetime.datetime.now(custom_timezone)
            sleep_time = 86400 - (now - (datetime.datetime.combine(now.date(), datetime.time()))).seconds
            await asyncio.sleep(sleep_time)




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
            birthday_obj["day"] = int(birthday[0])
            birthday_obj["month"] = int(birthday[1])
            birthday_obj["year"] = int(birthday[2])
            birthday_obj["guild"] = str(ctx.guild.id)

            self.birthdays.pop(str(ctx.author.id))
            self.birthdays[str(ctx.author.id)] = birthday_obj
            await self._update_birthdays()
            await ctx.send(f"Done! You'r birthday was set to {date}")
            return
        except KeyError:
            logger.info(birthday[0])
            logger.info(birthday[1])
            logger.info(birthday[2])

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

        self.birthdays.pop(str(ctx.author.id))
        await self._update_birthdays()
        await ctx.send(f"Done!")
        return

    @birthday.command()
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """
        Configure a channel for sending birthday announcements
        """

        self.channels
        self.channels[str(ctx.guild.id)] = str(channel.id)
        await self._update_config()
        await ctx.send("Done!")
        return

    @birthday.command()
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def role(self, ctx: commands.Context, role: discord.Role):
        """
        Configure a role which will be added to the birthay boizzzz
        """

        self.roles[str(ctx.guild.id)] = str(role.id)
        await self._update_config()
        await ctx.send("Done!")
        return

    @birthday.command()
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def message(self, ctx: commands.Context, *, msg: str):
        """
        Set a message to announce when wishing someone's birthday

        **Formatting:**
        • {user} - Name of he birthday boi
        • {user.mention} - Mention the birthday boi
        • {age} - Age of the birthday boiiii
        """

        self.messages[str(ctx.guild.id)] = msg
        await self._update_config()
        await ctx.send("Done!")
        return

    @birthday.command()
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def toggle(self, ctx: commands.Context):
        """
        Enable / Disable this plugin
        """

        self.enabled = not self.enabled
        await self._update_config()
        await ctx.send(f"{'Enabled' if self.enabled else 'Disabled'} the plugin :p")
        return


def setup(bot):
    bot.add_cog(BirthdayPlugin(bot))