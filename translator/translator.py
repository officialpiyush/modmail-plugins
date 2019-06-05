import discord
import asyncio
import datetime
import typing
from discord.ext import commands
from discord import NotFound, HTTPException, User, Embed

from core import checks
from core.models import PermissionLevel
from core.paginator import PaginatorSession, MessagePaginatorSession

from googletrans import Translator as CoreTranslator
from googletrans import LANGUAGES


class Language:
    def __init__(self, argument):
        if argument not in LANGUAGES:
            raise commands.BadArgument(
                ":x: Invalid language, use `languages` to get a list of supported languages!"
            )
        else:
            self.lang = argument


class Translator:
    def __init__(self):
        self.t = CoreTranslator()

    def translate(self, msg: str, dest: str = "en"):
        return CoreTranslator.translate(msg, dest=dest)


class TranslatePlugin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.plugin_db.get_partition(self)
        self.translator = Translator()
        self.tt = set()
        self.gt = False
        self.enabled = True
        asyncio.create_task(self._set_config())

    async def _set_config(self):
        config = await self.db.find_one({"_id": "config"})
        if config is None:
            await self.db.find_one_and_update(
                {"_id": "config"},
                {
                    "$set": {
                        "enabled": True,
                        "globalTranslate": False,
                        "translateSet": list([]),
                    }
                },
                upsert=True,
            )
        self.enabled = config.get("enabled", True)
        self.gt = config.get("globalTranslate", False)
        self.tt = set(config.get("translateSet", []))

    @commands.command(aliases=["languages"])
    @checks.has_permissions(PermissionLevel.SUPPORTER)
    async def language(self, ctx: commands.Context):
        # if lang is None:
        messages = []

        msg = "```css\n"

        for ll, fl in LANGUAGES.items():
            if msg != "```css\n":
                if len(f"{ll} - {fl}\n") + len(msg) + 3 > 2000:
                    msg += "```"
                    messages.append(msg)
                    msg = "```css\n"
            msg += f"{ll} - {fl}\n"
            if len(msg) + 3 > 2000:
                msg = msg[:1993] + "[...]```"
                messages.append(msg)
                msg = "```css\n"
        if msg != "```css\n":
            msg += "```"
            messages.append(msg)

        embed = Embed(color=self.bot.main_color)
        embed.set_footer(text="Available languages")

        session = MessagePaginatorSession(ctx, *messages, embed=embed)
        session.current = len(messages) - 1
        return await session.run()
        # else:


    @commands.command()
    async def translate(self, ctx, msgid: int):
        """Translate A Sent Message, or a modmail thread message into English."""
        try:
            msg = await ctx.channel.get_message(msgid)
            if len(msg.embeds) <= 0:
                ms = msg.content
            else:
                ms = msg.embeds[0].description

            embed = msg.embeds[0]
            tmsg = self.translator.translate(ms)
            embed = discord.Embed()
            embed.color = 4388013
            embed.description = tmsg.text
            await ctx.channel.send(embed=embed)
        except NotFound:
            await ctx.send("The Given Message Was Not Found.")
        except HTTPException:
            await ctx.send("The Try To Retrieve The Message Failed.")

    @commands.command(aliases=["egt", "toggle_global_translations", "tgt"])
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def enable_global_translate(self, ctx: commands.Context):
        """
            Toggle Global translations for all threads.

            **Usage:**
            {prefix}egt
        """
        if self.gt is True:
            self.gt = False
            enabled = False
        else:
            self.gt = True
            enabled = True
            enabled = True

        await self.db.find_one_and_update(
            {"_id": "config"}, {"$set": {"globalTranslate": self.gt}}, upsert=True
        )

        await ctx.send(f"{'Enabled' if self.gt else 'Disabled'} Global Translations")
        return

    @commands.command(aliases=["tt"])
    async def translatetext(self, ctx, *, message):
        """Translates Given Message Into English"""
        tmsg = self.translator.translate(message)
        embed = discord.Embed()
        embed.color = 4388013
        embed.description = tmsg.text
        await ctx.channel.send(embed=embed)

    @commands.command(aliases=["att"])
    @checks.has_permissions(PermissionLevel.SUPPORTER)
    async def auto_translate_thread(self, ctx):
        """Turn On Autotranslate for the ongoing thread."""
        if "User ID:" not in ctx.channel.topic:
            await ctx.send("The Channel Is Not A Modmail Thread")
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
        """Enable/Disable Auto Translations"""
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

        if self.gt is False:
            if channel.id not in self.tt:
                return

        if isinstance(message.author, User):
            return

        if "User ID:" not in channel.topic:
            return

        if len(message.embeds) <= 0:
            return

        if (
            message.embeds[0].footer.text
            and "Recipient" not in message.embeds[0].footer.text
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
            "https://counter.modmail-plugins.ionadev.ml/api/instances/translator",
            json={"id": self.bot.user.id},
        ):
            print("Posted to Plugin API")


def setup(bot):
    bot.add_cog(TranslatePlugin(bot))
