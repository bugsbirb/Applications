from discord.ext import commands
import discord
from dotenv import load_dotenv

load_dotenv()


class Utils(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.hybrid_command(description="Get the bot's latency")
    async def ping(self, ctx: commands.Context) -> None:
        await ctx.send(
            content=f"` ` **{ctx.author.display_name},** the bot's latency is `{self.client.latency * 1000:.2f}ms`.",
            ephemeral=True,
        )

    @commands.hybrid_command(description="About the bot")
    async def about(self, ctx: commands.Context) -> None:
        embed = discord.Embed(
            description="**Server Applications** is a bot that logs [server access applications](https://support.discord.com/hc/en-us/articles/29729107418519-Server-Member-Applications).",
            color=discord.Color.blurple(),
        )
        embed.set_author(
            name=f"{self.client.user.name}",
            icon_url=self.client.user.display_avatar.url,
        )
        embed.set_thumbnail(url=self.client.user.display_avatar.url)
        await ctx.send(
            embeds=[embed],
        )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Utils(client))
