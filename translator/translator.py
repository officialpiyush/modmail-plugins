import discord
import asyncio
import datetime
from discord.ext import commands
from discord import NotFound, HTTPException, User

from core import checks
from core.models import PermissionLevel

from googletrans import Translator


class TranslatePlugin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.plugin_db.get_partition(self)
        self.translator = Translator()
        self.tt = set()
        self.enabled = True
        asyncio.create_task(self._set_config())

    async def _set_config(self):
        config = await self.db.find_one({"_id": "config"})
        if config is None:
            await self.db.find_one_and_update(
                {"_id": "config"},
                {"$set": {"enabled": True, "translateSet": list([])}},
                upsert=True,
            )
        self.enabled = config.get("enabled", True)
        self.tt = set(config.get("translateSet", []))

    @commands.command()
    async def translate(self, ctx, msgid: int):
        """Translate a sent message or a modmail thread message into english."""
        try:
            msg = await ctx.channel.fetch_message(msgid)
            if not msg.embeds:
                ms = msg.content
            elif msg.embeds and msg.embeds[0] is not None:
                ms = msg.embeds[0].description
            else:
                await ctx.send("Something wrong!")
                return
            tmsg = self.translator.translate(ms)
            embed = discord.Embed()
            embed.color = 4388013
            embed.description = tmsg.text
            await ctx.channel.send(embed=embed)
        except NotFound:
            await ctx.send("The provided message Was not found.")
        except HTTPException:
            await ctx.send("Failed to retrieve the message.")

    @commands.command(aliases=["tt"])
    async def translatetext(self, ctx, *, message):
        """Translates a provided message into english"""
        tmsg = self.translator.translate(message)
        embed = discord.Embed()
        embed.color = 4388013
        embed.description = tmsg.text
        await ctx.channel.send(embed=embed)

    @commands.command(aliases=["att"])
    @checks.has_permissions(PermissionLevel.SUPPORTER)
    async def auto_translate_thread(self, ctx):
        """Turn on auto translations for the ongoing thread."""
        if "User ID:" not in ctx.channel.topic:
            await ctx.send("The channel is not a modmail thread")
            return
        if ctx.channel.id in self.tt:
            self.tt.remove(ctx.channel.id)
            removed = True
        else:
            self.tt.add(ctx.channel.id)
            removed = False

        await self.db.update_one(
            {"_id": "config"}, {"$set": {"translateSet": list(self.tt)}}, upsert=True
        )

        await ctx.send(
            f"{'Removed' if removed else 'Added'} Channel {'from' if removed else 'to'} Auto Translations List."
        )

    @commands.command(aliases=["tat"])
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def toggle_auto_translations(self, ctx, enabled: bool):
        """Enable/Disable automatic translations"""
        self.enabled = enabled
        await self.db.update_one(
            {"_id": "config"}, {"$set": {"enabled": self.enabled}}, upsert=True
        )
        await ctx.send(f"{'Enabled' if enabled else 'Disabled'} Auto Translations")

    @commands.Cog.listener()
    async def on_message(self, message):
        if not self.enabled:
            return

        channel = message.channel

        if channel.id not in self.tt:
            return

        if isinstance(message.author, User):
            return

        if "User ID:" not in channel.topic:
            return

        if not message.embeds:
            return

        if (
            message.embeds[0].footer.text
            and "Message ID" not in message.embeds[0].footer.text
        ):
            return

        embed = message.embeds[0]

        tmsg = await self.bot.loop.run_in_executor(
            None, self.translator.translate, message.embeds[0].description
        )

        if tmsg.src == "en":
            return

        field = {
            "inline": False,
            "name": f"Translation [{(tmsg.src).upper()}]",
            "value": tmsg.text,
        }

        try:
            embed._fields.insert(0, field)
        except AttributeError:
            embed._fields = [field]

        await message.edit(embed=embed)

    @commands.Cog.listener()
    async def on_ready(self):
        async with self.bot.session.post(
            "https://counter.modmail-plugins.piyush.codes/api/instances/translator",
            json={"id": self.bot.user.id},
        ):
            print("Posted to Plugin API")


def setup(bot):
    bot.add_cog(TranslatePlugin(bot))
