import discord
import aiohttp
from discord.ext import commands
from datetime import datetime, timezone
from config import TOKEN, DISCORD_ID
from utils import error_embed
from commands import *

intents = discord.Intents.default()
intents.message_content = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
    
    async def setup_hook(self):
        self.session = aiohttp.ClientSession()
        self.tree.add_command(sync)
        self.tree.add_command(link)
        self.tree.add_command(unlink)
        self.tree.add_command(forcelink)
        self.tree.add_command(forceunlink)
        self.tree.add_command(level)
        self.tree.add_command(milkshake)
        self.tree.add_command(aprilfool)
        self.tree.add_command(quickbuyprivacy)
        self.tree.add_command(sledtype)
        self.tree.add_command(rankcolor)
        self.tree.add_command(gamblergeorge)
        self.tree.add_command(housingadvanced)
        self.tree.add_command(paidsouls)
        self.tree.add_command(ultimate)
        self.tree.add_command(mmsuicides)
        self.tree.add_command(collectibles)
        self.tree.add_command(trackedachievements)
        self.tree.add_command(music)
        self.tree.add_command(bingobucks)
        self.tree.add_command(housingrepulsor)
        self.tree.add_command(boxingfish)
        self.tree.add_command(longestcombo)
        self.tree.add_command(warlordmvp)
        self.tree.add_command(cookiesgiven)
        self.tree.add_command(favoritemaps)
        self.tree.add_command(deliveryman)
        self.tree.add_command(chatchannel)
        self.tree.add_command(murdererchance)
        self.tree.add_command(classicgames)
        self.tree.add_command(poop)
        self.tree.add_command(language)
        self.tree.add_command(pitallegiance)
        self.tree.add_command(smashheroesboosters)
        self.tree.add_command(bwminion)
        self.tree.add_command(smashheroeslimit)
        self.tree.add_command(lockedchallenges)
        self.tree.add_command(sheepwarskit)
        self.tree.add_command(randomstat)

    async def on_ready(self):
        print(f"Bot logged in as {self.user}.")

    async def on_close(self):
        await self.session.close()

bot = MyBot()

# =====================================================================
# Admin commands
# =====================================================================

@app_commands.command(name="sync", description="Synchronise new made or edited commands with Discord")
@app_commands.default_permissions(administrator=True)
async def sync(interaction: discord.Interaction):
    if interaction.user.id != DISCORD_ID:
        embed = discord.Embed(
            title = "Access Denied",
            description = "You do not have permission to use that command.",
            color = discord.Color.red(),
            timestamp = datetime.now(tz=timezone.utc)
        )
        return await interaction.response.send_message(embed=embed)
    try:
        print("Loading...")
        await bot.tree.sync()
        print("Commands successfully synced with Discord.")
        embed = discord.Embed(
            title = "Synchronisation",
            description = "Commands successfully synced with Discord.",
            color = discord.Color(0x010101),
            timestamp = datetime.now(tz=timezone.utc)
        )
        await interaction.response.send_message(embed=embed)

    #Error
    except Exception as e:
        print(e)
        await interaction.response.send_message(embed=error_embed("Something went wrong."))

# =====================================================================

@app_commands.command(name="forcelink", description="Link someone's Discord user to a Minecraft account")
@app_commands.default_permissions(administrator=True)
@app_commands.describe(discorduser = "Discord name of the user", username= "In game name of the player")
@app_commands.rename(discorduser = "discord-name", username="minecraft-name")
async def forcelink(interaction: discord.Interaction, discorduser: discord.Member, username: str):
    if interaction.user.id != DISCORD_ID:
            embed = discord.Embed(
                title = "Access Denied",
                description = "You do not have permission to use that command.",
                color = discord.Color.red(),
                timestamp = datetime.now(tz=timezone.utc)
            )
            return await interaction.response.send_message(embed=embed)
    
    session = interaction.client.session
    try:

        #API
        uuid, name = await get_mojang_api(session, username)
        await get_hypixel_api(session, name, uuid)

        with open("data.json", "r", encoding="utf-8") as f:
            links = json.load(f)
        
        links[str(discorduser.id)] = {"discord_name": discorduser.name, "minecraft_username": name.replace("\\", ""), "minecraft_uuid": uuid}

        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(links, f, indent=4)

        embed = discord.Embed(
            title = "Linked account",
            description = f"Forced link Discord user `@{discorduser.name}` with Minecraft account **{name}**.",
            color = discord.Color.blurple(),
            timestamp = datetime.now(tz=timezone.utc)
        )
        embed.set_footer(text="Made by @Quent120", icon_url=ICON)

        await interaction.response.send_message(embed=embed)

    #Error
    except Exception as e:
        await handle_error(interaction, e)

#=====================================================================

@app_commands.command(name="forceunlink", description="Unlink someone's Minecraft account from this Discord bot")
@app_commands.default_permissions(administrator=True)
@app_commands.describe(discorduser = "Discord name of the user")
@app_commands.rename(discorduser = "discord-name")
async def forceunlink(interaction: discord.Interaction, discorduser: discord.Member):
    try:

        with open("data.json", "r", encoding="utf-8") as f:
            links = json.load(f)
        
        if str(discorduser.id) in links:
            del links[str(discorduser.id)]

            with open("data.json", "w", encoding="utf-8") as f:
                json.dump(links, f, indent=4)

            embed = discord.Embed(
                title = "Unlinked account",
                description = f"Forced unlink Discord user `@{discorduser.name}` from **{interaction.client.user.name}**.",
                color = discord.Color.blurple(),
                timestamp = datetime.now(tz=timezone.utc)
            )
            embed.set_footer(text="Made by @Quent120", icon_url=ICON)
        else:
            embed=error_embed(
                f"No Minecraft account found associated to Discord user `@{discorduser.name}`. Use **/link** to use commands without having to specify a username first."
            )

        await interaction.response.send_message(embed=embed)

    #Error
    except Exception as e:
        await handle_error(interaction, e)


# Funni
@bot.command()
async def ping(ctx):
    await ctx.send("pong")

bot.run(TOKEN)