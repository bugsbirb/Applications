import discord
from discord.ext import commands
import os

import json
from dotenv import load_dotenv

load_dotenv()


async def ConfigEmbed(guild: discord.Guild) -> discord.Embed:
    embed = discord.Embed(
        color=discord.Color.blurple(),
        timestamp=discord.utils.utcnow(),
    )
    embed.set_author(name="Configuration", icon_url=guild.icon)
    embed.set_footer(text=f"ID: {guild.id}")
    embed.description = (
        "`🔽` Select **an option** to manage your server's configuration."
    )

    embed.add_field(
        name="` ❤️ ` Support",
        value="> If you need help, please join open a support issue on our github.",
        inline=False,
    )
    embed.add_field(
        name="` 📙 ` Purpose",
        value=(
            "> Simplify your server's application process with this bot. "
            "Automate submissions, approvals, and denials to stay organized. "
            "[Learn more](https://support.discord.com/hc/en-us/articles/29729107418519-Server-Member-Applications)."
        ),
        inline=False,
    )

    return embed


class Configuration(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.hybrid_command(
        name="setup", description="Configure the bot for your server"
    )
    @commands.has_permissions(manage_guild=True)
    async def setup(self, ctx: commands.Context) -> None:
        from Cogs.Utils.menus import Config

        C = await self.client.db["Configuration"].find_one({"_id": ctx.guild.id})
        if not C:
            C = {}
        E = await ConfigEmbed(ctx.guild)
        view = Config(ctx.author)
        button = view.children[0]
        button.label = (
            "Enabled" if C.get("Applications", {}).get("Enabled", False) else "Disabled"
        )
        button.style = (
            discord.ButtonStyle.green
            if C.get("Applications", {}).get("Enabled", False)
            else discord.ButtonStyle.red
        )
        await ctx.send(embed=E, view=view)

    @setup.error
    async def setup_error(self, ctx: commands.Context, error: Exception) -> None:
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(
                content=f"` ❌ ` **{ctx.author.display_name},** you do not have permission to use this command.",
                ephemeral=True,
            )
        else:
            await ctx.send(
                content=f"` ❌ ` **{ctx.author.display_name},** an unexpected error occurred.",
                ephemeral=True,
            )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Configuration(client))
