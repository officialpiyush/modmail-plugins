import discord
import aiohttp
import json
from discord.ext import commands
from .utils import CodeBlock

Cog = getattr(commands, 'Cog', object)

class CodeCog(Cog):
    """Compile & Run cpp,c,py,haskell code using coliru

    Please Dont Abuse
    """

    def __init__(self,bot):
        self.bot = bot

    @commands.command(aliases=["code"])
    async def coliru(self,ctx,code: CodeBlock):
        """Compiles Code Through coliru API

        You have to pass in a code block with the language syntax
        either set to one of these:
        - cpp
        - c
        - python
        - py
        - haskell

        Anything else isn't supported. The C++ compiler uses g++ -std=c++14.
        The python support is now 3.5.2.

        Please don't spam this for Stacked's sake.
        """

         payload = {
            'cmd': code.command,
            'src': code.source
        }

        data = json.dumps(payload)

        async with ctx.session.post('http://coliru.stacked-crooked.com/compile', data=data) as resp:
                if resp.status != 200:
                    await ctx.send('Coliru did not respond in time.')
                    return

                output = await resp.text(encoding='utf-8')

                if len(output) < 1992:
                    await ctx.send(f'```\n{output}\n```')
                    return

                # output is too big so post it in gist
                async with ctx.session.post('http://coliru.stacked-crooked.com/share', data=data) as r:
                    if r.status != 200:
                        await ctx.send('Could not create coliru shared link')
                    else:
                        shared_id = await r.text()
                        await ctx.send(f'Output too big. Coliru link: http://coliru.stacked-crooked.com/a/{shared_id}')


def setup(bot):
    bot.add_cog(CodeCog(bot))

			
