import discord
from discord.ext import commands


class CodeBlock:
    missing_error = "Missing code block. Please use the following markdown\n\\`\\`\\`language\ncode here\n\\`\\`\\`"

    def __init__(self, argument):
        try:
            block, code = argument.split("\n", 1)
        except ValueError:
            raise commands.BadArgument(self.missing_error)

        if not block.startswith("```") and not code.endswith("```"):
            raise commands.BadArgument(self.missing_error)

        language = block[3:]
        self.command = self.get_command_from_language(language.lower())
        self.source = code.rstrip("`").replace("```", "")

    def get_command_from_language(self, language):
        cmds = {
            "cpp": "g++ -std=c++1z -O2 -Wall -Wextra -pedantic -pthread main.cpp -lstdc++fs && ./a.out",
            "c": "mv main.cpp main.c && gcc -std=c11 -O2 -Wall -Wextra -pedantic main.c && ./a.out",
            "py": "python3 main.cpp",
            "python": "python3 main.cpp",
            "haskell": "runhaskell main.cpp",
        }

        cpp = cmds["cpp"]
        for alias in ("cc", "h", "c++", "h++", "hpp"):
            cmds[alias] = cpp
        try:
            return cmds[language]
        except KeyError as e:
            if language:
                fmt = f"Unknown language to compile for: {language}"
            else:
                fmt = "Could not find a language to compile with."
            raise commands.BadArgument(fmt) from e
