import asyncio
import math
import time
from discord.ext import commands

from core import checks
from core.models import PermissionLevel, getLogger

logger = getLogger(__name__)


class ReminderPlugin(commands.Cog):
    """
    Create Reminders.
    """

    def __init__(self, bot):
        self.bot = bot
        self.db = bot.plugin_db.get_partition(self)
        self.active_reminders = {}

    async def _update_db(self):
        await self.db.find_one_and_update(
            {"_id": "reminders"},
            {"$set": {"active": self.active_reminders}},
            upsert=True,
        )

    async def _set_from_db(self):
        config = await self.db.find_one({"_id": "reminders"})
        if config is None:
            await self.db.find_one_and_update(
                {"_id": "reminders"},
                {"$set": {"reminders": dict()}},
                upsert=True,
            )

        for key, reminder in config.get("reminders", {}).items():
            if key in self.active_reminders:
                continue
            self.active_reminders[str(key)] = reminder
            self.bot.loop.create_task(self._handle_reminder(reminder))

    async def _handle_reminder(self, reminder_obj):
        logger.info("In Handle Reminder")
        _time = reminder_obj["time"] - time.time()
        logger.info(_time)
        await asycio.sleep(_time if _time >= 0 else 0)
        logger.info("Timeout finished")

        if str(reminder_obj["message"]) not in self.active_reminders:
            logger.info("No Reminder in cache")
            return

        channel = self.bot.get_channel(reminder_obj["channel"])
        if channel is None:
            logger.info("Channel Not Found")
            try:
                self.active_reminders.pop(str(reminder_obj["message"]))
            except KeyError:
                pass
            return

        days = math.floor(g_time // 86400)
        hours = math.floor(g_time // 3600 % 24)
        minutes = math.floor(g_time // 60 % 60)
        seconds = math.floor(g_time % 60)

        to_send = f"{f'{days} Days ' if days > 0 else ''}{f'{hours} Hours ' if hours > 0 else ''}{f'{minutes} Minutes ' if minutes > 0 else ''}{f'{seconds} Seconds ' if seconds > 0 else ''} ago: {reminder_obj['reminder']}\n\n{reminder_obj['jump_url']}"
        try:
            await channel.send(to_send)
            self.active_reminders.pop(str(reminder_obj["message"]))
        except:
            logger.info("Cant POP")
            pass
        await self._update_db()

    @commands.command(name="reminder", aliases=["remindme", "remind", "rme"])
    @checks.has_permissions(PermissionLevel.REGULAR)
    async def reminder(self, ctx: commands.Context, *, message: str):
        """
        Create a reminder

        **Example:**
        {prefix}remind in 2 hours Test This
        """
        resp = await self.bot.session.get(
            "https://dateparser.piyush.codes/fromstr",
            params={
                "message": message[: len(message) // 2]
                if len(message) > 20
                else message
            },
        )
        try:
            json = await resp.json()
        except:
            await ctx.send("API appears to be down, please try sometime later")
        if resp.status == 400:
            await ctx.send(json["message"])
            return
        elif resp.status == 500:
            await ctx.send(json["message"])
            return
        else:
            time = json["message"]
            message = message.replace(json["readable_time"], "")

            await ctx.send(
                f"Alright <@{ctx.author.id}>, {json['readable_time']}: {message}"
            )
            reminder_obj = {
                "message": ctx.message.id,
                "channel": ctx.channel.id,
                "guild": ctx.guild.id,
                "reminder": message,
                "time": time,
                "url": ctx.message.jump_url,
            }
            self.active_reminders[str(ctx.message.id)] = reminder_obj
            self.bot.loop.create_task(self._handle_reminder(reminder_obj))
            await self._update_db()


def setup(bot):
    bot.add_cog(ReminderPlugin(bot))
