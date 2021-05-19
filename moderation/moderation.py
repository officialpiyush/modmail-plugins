import asyncio
import discord
from discord.ext import commands
from core import checks
from core.models import PermissionLevel


class Moderation(commands.Cog):
    """
    Commands to moderate your server.*
    NOTE: You will need the moderator permission
    level in order to run any of these commands.*_ _
    """

    

    def __init__(self, bot):
        self.bot = bot
        self.db = bot.api.get_plugin_partition(self)

    async def cog_command_error(self, ctx, error):
        """Checks errors"""
        error = getattr(error, "original", error)
        if isinstance(error, commands.CheckFailure):
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="You don't have enough permissions to run this command!",
                    color=discord.Color.red(),
                ).set_footer(text="Are you a moderator?")
            )
        raise error

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        """Sets up mute role permissions for the channel."""
        muterole = await self.db.find_one({"_id": "muterole"})
        if muterole == None:
            return

        if not str(channel.guild.id) in muterole:
            return

        role = channel.guild.get_role(muterole[str(channel.guild.id)])
        if role == None:
            return
        await channel.set_permissions(role, send_messages=False)

    @commands.command(usage="<channel>")
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def setlog(self, ctx, channel: discord.TextChannel = None):
        """Sets up a log channel."""
        if channel == None:
            return await ctx.send_help(ctx.command)

        try:
            await channel.send(
                embed=discord.Embed(
                    description=(
                        "This channel has been set up to log actions.\n"
                        "This means that I will send bans/warns/kicks here."
                    ),
                    color=self.bot.main_color,
                )
            )
        except discord.errors.Forbidden:
            await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="I don't have enough permissions to write in that channel.",
                    color=discord.Color.red(),
                ).set_footer(text="Please fix the permissions.")
            )
        else:
            await self.db.find_one_and_update(
                {"_id": "logging"},
                {"$set": {str(ctx.guild.id): channel.id}},
                upsert=True,
            )
            await ctx.send(
                embed=discord.Embed(
                    title="Success",
                    description=f"{channel.mention} has been set up as log channel.",
                    color=self.bot.main_color,
                )
            )

    @commands.command(usage="<role>")
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def muterole(self, ctx, role: discord.Role = None):
        """Sets up the muted role."""
        if role is None:
            if (await self.db.find_one({"_id": "muterole"})) is not None:
                if (
                    ctx.guild.get_role(
                        (await self.db.find_one({"_id": "muterole"}))[str(ctx.guild.id)]
                    )
                    != None
                ):
                    return await ctx.send(
                        embed=discord.Embed(
                            title="Error",
                            description="Muted role is already set up.",
                            color=discord.Color.red(),
                        ).set_footer(
                            text="If you want to change role, just mention it."
                        )
                    )
            role = await ctx.guild.create_role(name="Muted")

        await self.db.find_one_and_update(
            {"_id": "muterole"}, {"$set": {str(ctx.guild.id): role.id}}, upsert=True
        )

        await ctx.send(
            embed=discord.Embed(
                title="Success",
                description=f"The muted role has been set to {role.mention}.",
                color=self.bot.main_color,
            )
        )

    @commands.command(usage="<member> [reason]")
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def warn(self, ctx, member: discord.Member = None, *, reason=None):
        """
        Warns the specified member.
        """
        if member == None:
            return await ctx.send_help(ctx.command)

        if reason != None:
            if not reason.endswith("."):
                reason = reason + "."

        case = await self.get_case()

        msg = f"You have been warned in {ctx.guild.name}" + (
            f" for: {reason}" if reason else "."
        )

        await self.log(
            guild=ctx.guild,
            embed=discord.Embed(
                title="Warn",
                description=f"{member} has been warned by {ctx.author.mention}"
                + (f" for: {reason}" if reason else "."),
                color=self.bot.main_color,
            ).set_footer(text=f"This is the {case} case."),
        )

        try:
            await member.send(msg)
        except discord.errors.Forbidden:
            return await ctx.send(
                embed=discord.Embed(
                    title="Logged",
                    description=f"Warning has been logged for {member}. I couldn't warn them, they disabled DMs.",
                    color=self.bot.main_color,
                ).set_footer(text=f"This is the {case} case.")
            )

        await ctx.send(
            embed=discord.Embed(
                title="Success",
                description=f"{member} has been warned.",
                color=self.bot.main_color,
            ).set_footer(text=f"This is the {case} case.")
        )

    @commands.command(usage="<member> [reason]")
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def kick(self, ctx, member: discord.Member = None, *, reason=None):
        """Kicks the specified member."""
        if member == None:
            return await ctx.send_help(ctx.command)

        if reason != None:
            if not reason.endswith("."):
                reason = reason + "."

        msg = f"You have been kicked from {ctx.guild.name}" + (
            f" for: {reason}" if reason else "."
        )

        try:
            await member.send(msg)
        except discord.errors.Forbidden:
            pass

        try:
            await member.kick(reason=reason)
        except discord.errors.Forbidden:
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="I don't have enough permissions to kick them.",
                    color=discord.Color.red(),
                ).set_footer(text="Please fix the permissions.")
            )

        case = await self.get_case()

        await self.log(
            guild=ctx.guild,
            embed=discord.Embed(
                title="Kick",
                description=f"{member} has been kicked by {ctx.author.mention}"
                + (f" for: {reason}" if reason else "."),
                color=self.bot.main_color,
            ).set_footer(text=f"This is the {case} case."),
        )

        await ctx.send(
            embed=discord.Embed(
                title="Success",
                description=f"{member} has been kicked.",
                color=self.bot.main_color,
            ).set_footer(text=f"This is the {case} case.")
        )

    @commands.command(usage="<member> [reason]")
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def ban(self, ctx, member: discord.Member = None, *, reason=None):
        """Bans the specified member."""
        if member == None:
            return await ctx.send_help(ctx.command)

        if reason != None:
            if not reason.endswith("."):
                reason = reason + "."

        msg = f"You have been banned from {ctx.guild.name}" + (
            f" for: {reason}" if reason else "."
        )

        try:
            await member.send(msg)
        except discord.errors.Forbidden:
            pass

        try:
            await member.ban(reason=reason, delete_message_days=0)
        except discord.errors.Forbidden:
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="I don't have enough permissions to ban them.",
                    color=discord.Color.red(),
                ).set_footer(text="Please fix the permissions.")
            )

        case = await self.get_case()

        await self.log(
            guild=ctx.guild,
            embed=discord.Embed(
                title="Ban",
                description=f"{member} has been banned by {ctx.author.mention}"
                + (f" for: {reason}" if reason else "."),
                color=self.bot.main_color,
            ).set_footer(text=f"This is the {case} case."),
        )

        await ctx.send(
            embed=discord.Embed(
                title="Success",
                description=f"{member} has been banned.",
                color=self.bot.main_color,
            ).set_footer(text=f"This is the {case} case.")
        )

    @commands.command(usage="<member> [reason]")
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def mute(self, ctx, member: discord.Member = None, *, reason=None):
        """Mutes the specified member."""
        if member == None:
            return await ctx.send_help(ctx.command)
        role = await self.db.find_one({"_id": "muterole"})
        no_role = False
        if role == None:
            no_role = True
        elif str(ctx.guild.id) in role:
            role = ctx.guild.get_role(role[str(ctx.guild.id)])
            if role == None:
                no_role = True

        if reason != None:
            if not reason.endswith("."):
                reason = reason + "."

        if no_role:
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description=(
                        "You must set up a muted role first.\n"
                        f"To set one, run `{ctx.prefix}muterole (@role)`."
                    ),
                    color=discord.Color.red(),
                )
            )

        msg = f"You have been muted from {ctx.guild.name}" + (
            f" for: {reason}" if reason else "."
        )

        try:
            await member.send(msg)
        except discord.errors.Forbidden:
            pass

        try:
            await member.add_roles(role, reason=reason)
        except discord.errors.Forbidden:
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="I don't have enough permissions to mute them.",
                    color=discord.Color.red(),
                ).set_footer(text="Please fix the permissions.")
            )

        case = await self.get_case()

        await self.log(
            guild=ctx.guild,
            embed=discord.Embed(
                title="Mute",
                description=f"{member} has been muted by {ctx.author.mention}"
                + (f" for: {reason}" if reason else "."),
                color=self.bot.main_color,
            ).set_footer(text=f"This is the {case} case."),
        )

        await ctx.send(
            embed=discord.Embed(
                title="Success",
                description=f"{member} has been muted.",
                color=self.bot.main_color,
            ).set_footer(text=f"This is the {case} case.")
        )

    @commands.command(usage="<member> [reason]")
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def unmute(self, ctx, member: discord.Member = None, *, reason=None):
        """Unmutes the specified member."""
        if member == None:
            return await ctx.send_help(ctx.command)
        role = await self.db.find_one({"_id": "muterole"})
        no_role = False
        if role == None:
            no_role = True
        elif str(ctx.guild.id) in role:
            role = ctx.guild.get_role(role[str(ctx.guild.id)])
            if role == None:
                no_role = True

        if reason != None:
            if not reason.endswith("."):
                reason = reason + "."

        if no_role:
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description=(
                        "You don't have a muted role set up.\n"
                        f"You will have to unmute them manually."
                    ),
                    color=discord.Color.red(),
                )
            )

        try:
            await member.remove_roles(role, reason=reason)
        except discord.errors.Forbidden:
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="I don't have enough permissions to unmute them.",
                    color=discord.Color.red(),
                ).set_footer(text="Please fix the permissions.")
            )

        case = await self.get_case()

        await self.log(
            guild=ctx.guild,
            embed=discord.Embed(
                title="Mute",
                description=f"{member} has been unmuted by {ctx.author.mention}"
                + (f" for: {reason}" if reason else "."),
                color=self.bot.main_color,
            ).set_footer(text=f"This is the {case} case."),
        )

        await ctx.send(
            embed=discord.Embed(
                title="Success",
                description=f"{member} has been unmuted.",
                color=self.bot.main_color,
            ).set_footer(text=f"This is the {case} case.")
        )

    @commands.command()
    @checks.has_permissions(PermissionLevel.OWNER)
    async def nuke(self, ctx, channel: discord.TextChannel = None):
        """
        Nukes (deletes EVERY message in) a channel.
        You can mention a channel to nuke that one instead.
        """
        if channel == None:
            channel = ctx.channel
        tot = "this" if channel.id == ctx.channel.id else "that"
        message = await ctx.send(
            embed=discord.Embed(
                title="Are you sure?",
                description=(
                    f"This command will delete EVERY SINGLE MESSAGE in {tot} channel!\n"
                    'If you are sure and responsible about what might happen send "Yes, do as I say!". '
                    "Otherwise, send anything else to abort.\n"
                    "**Unexpected bad things might happen if you decide to continue!**"
                ),
                color=discord.Color.red(),
            )
        )

        def surecheck(m):
            return m.author == ctx.message.author

        try:
            sure = await self.bot.wait_for("message", check=surecheck, timeout=30)
        except asyncio.TimeoutError:
            await message.edit(
                embed=discord.Embed(title="Aborted.", color=self.bot.main_color)
            )
            ensured = False
        else:
            if sure.content == "Yes, do as I say!":
                ensured = True
            else:
                await message.edit(
                    embed=discord.Embed(title="Aborted.", color=self.bot.main_color)
                )
                ensured = False
        if ensured:
            case = await self.get_case()

            channel_position = channel.position

            try:
                new_channel = await channel.clone()

                await new_channel.edit(position=channel_position)
                await channel.delete()
            except discord.errors.Forbidden:
                return await ctx.send(
                    embed=discord.Embed(
                        title="Error",
                        description=f"I don't have enough permissions to nuke {tot} channel.",
                        color=discord.Color.red(),
                    ).set_footer(text="Please fix the permissions.")
                )

            await new_channel.send(
                embed=discord.Embed(
                    title="Nuke",
                    description="This channel has been nuked!",
                    color=self.bot.main_color,
                )
                .set_image(
                    url="https://cdn.discordapp.com/attachments/600843048724987925/600843407228928011/tenor.gif"
                )
                .set_footer(text=f"This is the {case} case.")
            )

            await self.log(
                guild=ctx.guild,
                embed=discord.Embed(
                    title="Nuke",
                    description=f"{ctx.author.mention} nuked {new_channel.mention}.",
                    color=self.bot.main_color,
                ).set_footer(text=f"This is the {case} case."),
            )

    @commands.command(usage="<amount>")
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def purge(self, ctx, amount: int = 1):
        """Purge the specified amount of messages."""
        max = 2000
        if amount > max:
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description=f"You can only purge up to 2000 messages.",
                    color=discord.Color.red(),
                ).set_footer(text=f"Use {ctx.prefix}nuke to purge the entire chat.")
            )

        try:
            await ctx.message.delete()
            await ctx.channel.purge(limit=amount)
        except discord.errors.Forbidden:
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="I don't have enough permissions to purge messages.",
                    color=discord.Color.red(),
                ).set_footer(text="Please fix the permissions.")
            )

        case = await self.get_case()
        messages = "messages" if amount > 1 else "message"
        have = "have" if amount > 1 else "has"

        await self.log(
            guild=ctx.guild,
            embed=discord.Embed(
                title="Purge",
                description=f"{amount} {messages} {have} been purged by {ctx.author.mention}.",
                color=self.bot.main_color,
            ).set_footer(text=f"This is the {case} case."),
        )

        await ctx.send(
            embed=discord.Embed(
                title="Success",
                description=f"Purged {amount} {messages}.",
                color=self.bot.main_color,
            ).set_footer(text=f"This is the {case} case.")
        )

    async def get_case(self):
        """Gives the case number."""
        num = await self.db.find_one({"_id": "cases"})
        if num == None:
            num = 0
        elif "amount" in num:
            num = num["amount"]
            num = int(num)
        else:
            num = 0
        num += 1
        await self.db.find_one_and_update(
            {"_id": "cases"}, {"$set": {"amount": num}}, upsert=True
        )
        suffix = ["th", "st", "nd", "rd", "th"][min(num % 10, 4)]
        if 11 <= (num % 100) <= 13:
            suffix = "th"
        return f"{num}{suffix}"

    async def log(self, guild: discord.Guild, embed: discord.Embed):
        """Sends logs to the log channel."""
        channel = await self.db.find_one({"_id": "logging"})
        if channel == None:
            return
        if not str(guild.id) in channel:
            return
        channel = self.bot.get_channel(channel[str(guild.id)])
        if channel == None:
            return
        return await channel.send(embed=embed)


def setup(bot):
    bot.add_cog(Moderation(bot))