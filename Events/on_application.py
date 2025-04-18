import discord
from discord.ext import commands
import json
from dotenv import load_dotenv

load_dotenv()


class Applications(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_socket_raw_receive(self, raw_msg):
        msg = json.loads(raw_msg)
        Client = self.client
        t = msg.get("t")
        if t == "GUILD_JOIN_REQUEST_UPDATE":
            D = msg.get("d")
            REQUEST = D.get("request")
            RESPONSES = REQUEST.get("form_responses")
            status = D.get("status")
            if not status:
                return
            guild = Client.get_guild(int(REQUEST.get("guild_id")))
            if not guild:
                return

            Config = await self.client.db["Configuration"].find_one(
                {"_id": int(guild.id)}
            )
            if not Config:
                return
            if not Config.get("Applications"):
                return

            if not Config.get("Applications", {}).get("Enabled", True):
                return

            DeniedChannel = Config.get("Applications").get("Channels", {}).get("Denied")
            ApprovedChannel = (
                Config.get("Applications").get("Channels", {}).get("Approved")
            )
            SubmittedChannel = (
                Config.get("Applications").get("Channels", {}).get("Submitted")
            )
            AllinOneChannel = Config.get("Applications").get("Channels", {}).get("All")
            Mentions = Config.get("Applications").get("Mentions", {}).get("Roles")
            UserMentions = Config.get("Applications").get("Mentions", {}).get("Users")
            Edit = False
            ChannelID = (
                AllinOneChannel
                or (ApprovedChannel if status == "APPROVED" else None)
                or (DeniedChannel if status == "REJECTED" else None)
                or (SubmittedChannel if status == "SUBMITTED" else None)
            )
            if AllinOneChannel:
                ChannelID = AllinOneChannel
            channel = Client.get_channel(int(ChannelID)) if ChannelID else None
            Edit = Config.get("Applications").get("Edit", False)
            Mention = ""
            if Mentions or UserMentions:

                if Mentions:
                    for role in Mentions:
                        Mention += f"<@&{role}>"
                if UserMentions:
                    for user in UserMentions:
                        Mention += f"<@{user}>"

            if not channel:
                return

            try:
                member = await self.client.fetch_user(int(REQUEST.get("user_id")))
            except (discord.NotFound, discord.HTTPException):
                member = None

            if not member:
                return

            AT = REQUEST.get("actioned_by_user")
            actioner = None
            if AT:
                try:
                    actioner = (
                        await guild.fetch_member(int(AT.get("id"))) if guild else None
                    )
                except (discord.Forbidden, discord.HTTPException, discord.NotFound):
                    actioner = None

            embed = discord.Embed(
                description=f"> **Member:** {member.mention} (`{member.id}`)\n> **Account Created:** <t:{int(member.created_at.timestamp())}:R>"
            )

            if status == "APPROVED":
                embed.title = "Application Approved"
                embed.color = discord.Color.green()
                embed.set_author(
                    name=member.display_name, icon_url=member.display_avatar
                )
                embed.set_footer(
                    text=f"Accepted By @{actioner.display_name}",
                    icon_url=actioner.display_avatar,
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                for response in RESPONSES:
                    if response.get("choices"):
                        choice = response.get("choices")[response.get("response")]
                        embed.add_field(
                            name=response.get("label"),
                            value=f"> {choice}",
                            inline=False,
                        )
                    else:
                        embed.add_field(
                            name=response.get("label"),
                            value=f"> {response.get('response')}",
                            inline=False,
                        )

            elif status == "REJECTED":
                embed.color = discord.Color.red()
                embed.title = "Application Denied"
                embed.description += (
                    f"\n> **Denied Reason:** {REQUEST.get('rejection_reason')}"
                )
                embed.set_author(
                    name=member.display_name, icon_url=member.display_avatar.url
                )
                embed.set_footer(
                    text=f"Denied By @{actioner.display_name}",
                    icon_url=actioner.display_avatar.url,
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                for response in RESPONSES:
                    if response.get("choices"):
                        choice = response.get("choices")[response.get("response")]
                        embed.add_field(
                            name=response.get("label"),
                            value=f"> {choice}",
                            inline=False,
                        )
                    else:
                        embed.add_field(
                            name=response.get("label"),
                            value=f"> {response.get('response')}",
                            inline=False,
                        )

            elif status == "SUBMITTED":
                embed.color = discord.Color.dark_embed()
                embed.title = "Application"
                embed.set_author(
                    name=member.display_name, icon_url=member.display_avatar.url
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.set_footer(text="Pending Application", icon_url=guild.icon)
                for response in RESPONSES:
                    if response.get("choices"):
                        choice = response.get("choices")[response.get("response")]
                        embed.add_field(
                            name=response.get("label"),
                            value=f"> {choice}",
                            inline=False,
                        )
                    else:
                        embed.add_field(
                            name=response.get("label"),
                            value=f"> {response.get('response')}",
                            inline=False,
                        )
                try:
                    MSG = await channel.send(embeds=[embed], content=Mention)
                except (discord.HTTPException, discord.NotFound, discord.Forbidden):
                    return
                await self.client.db["Applications"].insert_one(
                    {
                        "guild_id": int(guild.id),
                        "user_id": int(member.id),
                        "request_id": int(REQUEST.get("id")),
                        "status": status,
                        "actioned_by_user": None,
                        "message_id": MSG.id,
                    }
                )

            if status in ["APPROVED", "REJECTED"]:
                RQ = await self.client.db["Applications"].find_one(
                    {"request_id": int(REQUEST.get("id"))}
                )
                if not RQ:
                    return
                if Edit and AllinOneChannel:
                    try:
                        if not RQ.get("message_id"):
                            return
                        message = await channel.fetch_message(int(RQ.get("message_id")))
                        if message:
                            try:
                                await message.edit(embed=embed)
                            except (
                                discord.HTTPException,
                                discord.NotFound,
                                discord.Forbidden,
                            ):
                                return
                    except (discord.HTTPException, discord.NotFound, discord.Forbidden):
                        return
                else:
                    try:
                        await channel.send(embeds=[embed], content=Mention)
                    except (discord.HTTPException, discord.NotFound, discord.Forbidden):
                        return


async def setup(client: commands.Bot) -> None:

    await client.add_cog(Applications(client))
