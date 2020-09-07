from discord.ext import commands
from discord import  Embed
from utils.yoba_currency_exchanger import CurrencyExchanger


class Test(commands.Cog):
    """class for Test fiches"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def cur(self, ctx: commands.Context, *args):
        string = ''.join(args)
        res = await CurrencyExchanger.exchange(string)
        embed = Embed(
            description=res
        )
        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Test(bot))
