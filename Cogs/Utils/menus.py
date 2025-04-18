import discord


class Config(discord.ui.View):
    def __init__(self, author: discord.User):
        super().__init__(timeout=None)
        self.author = author

    @discord.ui.button(label="Disabled", style=discord.ButtonStyle.red)
    async def disabled(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        if self.author.id != interaction.user.id:
            return await interaction.response.send_message(
                "` ❌ `  You cannot use this button", ephemeral=True
            )
        C = await interaction.client.db["Configuration"].find_one(
            {"_id": interaction.guild.id}
        )

        CS = C.get("Applications", {}).get("Enabled", False)
        NS = not CS
        C.setdefault("Applications", {})["Enabled"] = NS

        await interaction.client.db["Configuration"].update_one(
            {"_id": interaction.guild.id},
            {"$set": {"Applications.Enabled": NS}},
            upsert=True,
        )

        button.label = "Enabled" if NS else "Disabled"
        button.style = discord.ButtonStyle.green if NS else discord.ButtonStyle.red
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Mentions", style=discord.ButtonStyle.blurple)
    async def mentions(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:

        if self.author.id != interaction.user.id:
            return await interaction.response.send_message(
                "` ❌ ` You cannot use this button", ephemeral=True
            )

        embed = (
            discord.Embed(
                color=discord.Color.blurple(),
            )
            .set_author(name="Mentions Configuration", icon_url=interaction.guild.icon)
            .set_footer(text=f"ID: {interaction.guild.id}")
            .add_field(
                name="` 📢 ` Mentions",
                value=(
                    "> Select the users and roles to mention when an application is **approved** or **denied**.\n"
                    "> You can select up to 25 users and roles."
                ),
            )
        )
        await interaction.response.edit_message(
            embed=embed, view=MentionView(self.author), content=None
        )

    @discord.ui.button(label="Channels", style=discord.ButtonStyle.blurple)
    async def channels(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:

        if self.author.id != interaction.user.id:
            return await interaction.response.send_message(
                "` ❌ ` You cannot use this button", ephemeral=True
            )

        embed = (
            discord.Embed(
                color=discord.Color.blurple(),
            )
            .set_author(name="Channel Configuration", icon_url=interaction.guild.icon)
            .add_field(
                name="` 📦 ` Channels",
                value=(
                    "> Set where application events are sent in your server.\n\n"
                    "> **🟢 Approved** — Sent when an application is accepted.\n"
                    "> **🔴 Denied** — Sent when an application is rejected.\n"
                    "> **🕓 Submitted** — Sent when someone submits a new application.\n"
                    "> **📦 All-in-One** — Sends all application updates to one channel (overrides others).\n\n"
                    "> Use these to keep your team updated on incoming and reviewed applications."
                ),
            )
            .set_footer(text=f"ID: {interaction.guild.id}")
        )

        await interaction.response.edit_message(
            embed=embed, view=ChannelType(self.author), content=None
        )


class Finish(discord.ui.Button):
    def __init__(self, author: discord.User, Updated: dict = {}):
        super().__init__(label="Finish", style=discord.ButtonStyle.green)
        self.author = author
        self.Updated = Updated

    async def callback(self, interaction: discord.Interaction) -> None:
        if self.author.id != interaction.user.id:
            return await interaction.response.send_message(
                "` ❌ ` You cannot use this button", ephemeral=True
            )


class Finish(discord.ui.Button):
    def __init__(self, author: discord.User, updated: dict = {}):
        super().__init__(label="Finish", style=discord.ButtonStyle.green)
        self.author = author
        self.Updated = updated

    async def callback(self, interaction: discord.Interaction) -> None:
        if self.author.id != interaction.user.id:
            return await interaction.response.send_message(
                "` ❌ ` You cannot use this button", ephemeral=True
            )

        Current = (
            await interaction.client.db["Configuration"].find_one(
                {"_id": interaction.guild.id}
            )
            or {}
        )
        Current.setdefault("Applications", {}).update(
            self.Updated.get("Applications", {})
        )

        await interaction.client.db["Configuration"].update_one(
            {"_id": interaction.guild.id}, {"$set": Current}, upsert=True
        )

        await interaction.response.edit_message(
            content=f"` ✅ ` **{interaction.user.name}**, configuration saved.",
            embed=None,
            view=Return(self.author),
        )


class Approved(discord.ui.ChannelSelect):
    def __init__(self, author: discord.User, updated: dict = {}):
        CI = updated.get("Applications", {}).get("Channels", {}).get("Approved", None)
        super().__init__(
            placeholder="Select Approved Channel",
            min_values=0,
            max_values=1,
            default_values=[discord.Object(id=CI)] if CI else [],
        )
        self.author = author
        self.Updated = updated

    async def callback(self, interaction: discord.Interaction):
        if self.author.id != interaction.user.id:
            return await interaction.response.send_message(
                "` ❌ ` You cannot use this menu", ephemeral=True
            )

        channel = self.values[0] if self.values else None
        self.Updated.setdefault("Applications", {}).setdefault("Channels", {})
        self.Updated["Applications"]["Channels"]["Approved"] = (
            channel.id if channel else None
        )
        self.Updated["Applications"]["Channels"]["All"] = None

        await interaction.response.edit_message(
            view=ApprovedChannelsView(self.author, self.Updated)
        )


class Denied(discord.ui.ChannelSelect):
    def __init__(self, author: discord.User, updated: dict = {}):
        CI = updated.get("Applications", {}).get("Channels", {}).get("Denied", None)
        super().__init__(
            placeholder="Select Denied Channel",
            min_values=0,
            max_values=1,
            default_values=[discord.Object(id=CI)] if CI else [],
        )
        self.author = author
        self.Updated = updated

    async def callback(self, interaction: discord.Interaction):
        if self.author.id != interaction.user.id:
            return await interaction.response.send_message(
                "You cannot use this menu", ephemeral=True
            )

        channel = self.values[0] if self.values else None
        self.Updated.setdefault("Applications", {}).setdefault("Channels", {})
        self.Updated["Applications"]["Channels"]["Denied"] = (
            channel.id if channel else None
        )
        self.Updated["Applications"]["Channels"]["All"] = None

        await interaction.response.edit_message(
            view=DeniedChannelsView(self.author, self.Updated)
        )


class Submitted(discord.ui.ChannelSelect):

    def __init__(self, author: discord.User, updated: dict = {}):
        CI = updated.get("Applications", {}).get("Channels", {}).get("Submitted", None)
        super().__init__(
            placeholder="Select Submitted Channel",
            min_values=0,
            max_values=1,
            default_values=[discord.Object(id=CI)] if CI else [],
        )
        self.author = author
        self.Updated = updated

    async def callback(self, interaction: discord.Interaction):
        if self.author.id != interaction.user.id:
            return await interaction.response.send_message(
                "You cannot use this menu", ephemeral=True
            )

        channel = self.values[0] if self.values else None
        self.Updated.setdefault("Applications", {}).setdefault("Channels", {})
        self.Updated["Applications"]["Channels"]["Submitted"] = (
            channel.id if channel else None
        )
        self.Updated["Applications"]["Channels"]["All"] = None

        await interaction.response.edit_message(
            view=SubmittedChannelsView(self.author, self.Updated)
        )


class All(discord.ui.ChannelSelect):
    def __init__(self, author: discord.User, updated: dict = {}):
        CI = updated.get("Applications", {}).get("Channels", {}).get("All", None)
        super().__init__(
            placeholder="Select All-in-One Channel",
            min_values=0,
            max_values=1,
            default_values=[discord.Object(id=CI)] if CI else [],
        )
        self.author = author
        self.Updated = updated

    async def callback(self, interaction: discord.Interaction):
        if self.author.id != interaction.user.id:
            return await interaction.response.send_message(
                "You cannot use this menu", ephemeral=True
            )

        channel = self.values[0] if self.values else None
        self.Updated.setdefault("Applications", {}).setdefault("Channels", {})
        self.Updated["Applications"]["Channels"]["All"] = (
            channel.id if channel else None
        )
        self.Updated["Applications"]["Channels"]["Approved"] = None
        self.Updated["Applications"]["Channels"]["Denied"] = None
        self.Updated["Applications"]["Channels"]["Submitted"] = None

        await interaction.response.edit_message(
            view=AllChannelsView(self.author, self.Updated)
        )


class UserMention(discord.ui.UserSelect):
    def __init__(self, author: discord.User, updated: dict = {}):
        values = updated.get("Applications", {}).get("Mentions", {}).get("Users", [])
        super().__init__(
            placeholder="Select Users to Mention",
            min_values=0,
            max_values=25,
            default_values=[discord.Object(id=user) for user in values],
        )
        self.author = author
        self.Updated = updated

    async def callback(self, interaction: discord.Interaction):
        if self.author.id != interaction.user.id:
            return await interaction.response.send_message(
                "You cannot use this menu", ephemeral=True
            )

        self.Updated.setdefault("Applications", {}).setdefault("Mentions", {})
        self.Updated["Applications"]["Mentions"]["Users"] = [
            user.id for user in self.values
        ]

        await interaction.response.edit_message(
            view=MentionView(self.author, self.Updated)
        )


class RoleMention(discord.ui.RoleSelect):
    def __init__(self, author: discord.User, updated: dict = {}):
        values = updated.get("Applications", {}).get("Mentions", {}).get("Roles", [])
        super().__init__(
            placeholder="Select Roles to Mention",
            min_values=0,
            max_values=25,
            default_values=[discord.Object(id=role) for role in values],
        )
        self.author = author
        self.Updated = updated

    async def callback(self, interaction: discord.Interaction):
        if self.author.id != interaction.user.id:
            return await interaction.response.send_message(
                "You cannot use this menu", ephemeral=True
            )

        self.Updated.setdefault("Applications", {}).setdefault("Mentions", {})
        self.Updated["Applications"]["Mentions"]["Roles"] = [
            role.id for role in self.values
        ]

        await interaction.response.edit_message(
            view=MentionView(self.author, self.Updated)
        )


class MentionView(discord.ui.View):
    def __init__(self, author: discord.User, updated: dict = {}):
        super().__init__(timeout=None)
        self.author = author
        self.add_item(UserMention(author, updated))
        self.add_item(RoleMention(author, updated))
        self.add_item(Finish(author, updated))


class ChannelType(discord.ui.View):
    def __init__(self, author: discord.User):
        super().__init__(timeout=None)
        self.author = author

    @discord.ui.button(label="Approved", style=discord.ButtonStyle.blurple)
    async def approved(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        if self.author.id != interaction.user.id:
            return await interaction.response.send_message(
                "` ❌ ` You cannot use this button", ephemeral=True
            )
        C = await interaction.client.db["Configuration"].find_one(
            {"_id": interaction.guild.id}
        )

        await interaction.response.edit_message(
            embed=discord.Embed(
                color=discord.Color.blurple(),
            )
            .add_field(
                name="` 🟢 ` Approved",
                value="This channel will receive messages when an application is **approved**.",
                inline=False,
            )
            .set_author(name="Channel Configuration", icon_url=interaction.guild.icon)
            .set_footer(text=f"ID: {interaction.guild.id}"),
            view=ApprovedChannelsView(self.author, C or {}),
        )

    @discord.ui.button(label="Denied", style=discord.ButtonStyle.blurple)
    async def denied(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        if self.author.id != interaction.user.id:
            return await interaction.response.send_message(
                "` ❌ ` You cannot use this button", ephemeral=True
            )
        C = await interaction.client.db["Configuration"].find_one(
            {"_id": interaction.guild.id}
        )

        await interaction.response.edit_message(
            embed=discord.Embed(
                color=discord.Color.blurple(),
            )
            .add_field(
                name="` 🔴 ` Denied",
                value="This channel will receive messages when an application is **denied**.",
                inline=False,
            )
            .set_author(name="Channel Configuration", icon_url=interaction.guild.icon)
            .set_footer(text=f"ID: {interaction.guild.id}"),
            view=DeniedChannelsView(self.author, C or {}),
        )

    @discord.ui.button(label="Submitted", style=discord.ButtonStyle.blurple)
    async def submitted(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        if self.author.id != interaction.user.id:
            return await interaction.response.send_message(
                "` ❌ ` You cannot use this button", ephemeral=True
            )
        C = await interaction.client.db["Configuration"].find_one(
            {"_id": interaction.guild.id}
        )

        await interaction.response.edit_message(
            embed=discord.Embed(
                color=discord.Color.blurple(),
            )
            .add_field(
                name="` 🕓 ` Submitted",
                value="This channel will receive messages when someone **submits** a new application.",
                inline=False,
            )
            .set_author(name="Channel Configuration", icon_url=interaction.guild.icon)
            .set_footer(text=f"ID: {interaction.guild.id}"),
            view=SubmittedChannelsView(self.author, C or {}),
        )

    @discord.ui.button(label="All", style=discord.ButtonStyle.blurple)
    async def all(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        if self.author.id != interaction.user.id:
            return await interaction.response.send_message(
                "` ❌ ` You cannot use this button", ephemeral=True
            )
        C = await interaction.client.db["Configuration"].find_one(
            {"_id": interaction.guild.id}
        )

        await interaction.response.edit_message(
            embed=discord.Embed(
                color=discord.Color.blurple(),
            )
            .add_field(
                name="` 🖊️ ` Edit",
                value="This will edit the submission message instead of sending a new one.",
                inline=False,
            )
            .add_field(
                name="` 📦 ` All-in-One",
                value="Sends **all application updates** (approved, denied, and submitted) to this one channel. This overrides the individual ones above.",
                inline=False,
            )
            .set_author(name="Channel Configuration", icon_url=interaction.guild.icon)
            .set_footer(text=f"ID: {interaction.guild.id}"),
            view=AllChannelsView(self.author, C or {}),
        )


class AllChannelsView(discord.ui.View):
    def __init__(self, author: discord.User, updated: dict):
        super().__init__()
        self.add_item(EditBool(author))
        self.add_item(All(author, updated))
        self.add_item(Finish(author, updated))


class ApprovedChannelsView(discord.ui.View):
    def __init__(self, author: discord.User, updated: dict):
        super().__init__()
        self.add_item(Approved(author, updated))
        self.add_item(Finish(author, updated))


class DeniedChannelsView(discord.ui.View):
    def __init__(self, author: discord.User, updated: dict):
        super().__init__()
        self.add_item(Denied(author, updated))
        self.add_item(Finish(author, updated))


class SubmittedChannelsView(discord.ui.View):
    def __init__(self, author: discord.User, updated: dict):
        super().__init__()
        self.add_item(Submitted(author, updated))
        self.add_item(Finish(author, updated))


class Return(discord.ui.View):
    def __init__(self, author: discord.User):
        super().__init__(timeout=None)
        self.author = author

    @discord.ui.button(label="Return", style=discord.ButtonStyle.gray)
    async def return_(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        from Cogs.Configuration.main import ConfigEmbed

        if self.author.id != interaction.user.id:
            return await interaction.response.send_message(
                "` ❌ ` You cannot use this button", ephemeral=True
            )
        C = await interaction.client.db["Configuration"].find_one(
            {"_id": interaction.guild.id}
        )
        embed = await ConfigEmbed(interaction.guild)
        view = Config(interaction.user)
        button = view.children[0]
        button.label = (
            "Enabled" if C.get("Applications", {}).get("Enabled", False) else "Disabled"
        )
        button.style = (
            discord.ButtonStyle.green
            if C.get("Applications", {}).get("Enabled", False)
            else discord.ButtonStyle.red
        )
        await interaction.response.edit_message(embed=embed, view=view, content=None)


class EditBool(discord.ui.Select):
    def __init__(self, author: discord.User, updated: dict = {}):
        value = updated.get("Applications", {}).get("Edit", None)
        super().__init__(
            placeholder="Editing",
            options=[
                discord.SelectOption(
                    label="True", value="True", default=value is True or value == "True"
                ),
                discord.SelectOption(
                    label="False",
                    value="False",
                    default=value is False or value == "False",
                ),
            ],
        )
        self.author = author
        self.Updated = updated

    async def callback(self, interaction: discord.Interaction):
        if self.author.id != interaction.user.id:
            return await interaction.response.send_message(
                "You cannot use this menu", ephemeral=True
            )

        self.Updated.setdefault("Applications", {})
        self.Updated["Applications"]["Edit"] = self.values[0]

        await interaction.response.edit_message(
            view=AllChannelsView(self.author, self.Updated)
        )
