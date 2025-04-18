import discord
import sys

sys.dont_write_bytecode = True
import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import time
import platform
from motor.motor_asyncio import AsyncIOMotorClient


load_dotenv()
TOKEN = os.getenv("TOKEN")
PREFIX = os.getenv("PREFIX")
MONGO_URI = os.getenv("MONGO_URI")
if TOKEN is None:
    print("Token not found in .env file.")
    exit(1)

C = AsyncIOMotorClient(MONGO_URI)


class client(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True

        super().__init__(
            command_prefix=commands.when_mentioned_or(PREFIX),
            intents=intents,
            help_command=None,
            enable_debug_events=True,
        )
        self.client = client
        self.cogslist = ["Cogs.Configuration.main", "Events.on_application"]
        self.db = C["ServerApps"]

    async def load_jishaku(self):
        await self.wait_until_ready()
        await self.load_extension("jishaku")

    async def on_ready(self):
        prfx = time.strftime("%H:%M:%S GMT", time.gmtime())
        print(prfx + " Logged in as " + self.user.name)
        print(prfx + " Bot ID " + str(self.user.id))
        print(prfx + " Discord Version " + discord.__version__)
        print(prfx + " Python Version " + str(platform.python_version()))
        synced = await self.tree.sync()
        print(prfx + " Slash CMDs Synced " + str(len(synced)) + " Commands")
        print(prfx + " Bot is in " + str(len(self.guilds)) + " servers")
        await self.change_presence(
            activity=discord.Activity(
                name="Applications", type=discord.ActivityType.watching
            )
        )

    async def setup_hook(self):
        self.loop.create_task(self.load_jishaku())

        for ext in self.cogslist:
            await self.load_extension(ext)
            print(f"{ext} loaded")


Client = client()
Client.run(TOKEN)
