import discord
from discord import app_commands
from datetime import datetime, timezone
import time
import random
import re
import json
from PIL import Image, ImageDraw, ImageFont
import io
import roman
from utils import *

# =====================================================================
# /link
# =====================================================================

@app_commands.command(name="link", description="Link your Discord user to Minecraft account to fill commands with your name if left blank")
@app_commands.describe(username="Your in game name")
@app_commands.rename(username="name")
async def link(interaction: discord.Interaction, username: str):
    await interaction.response.defer()
    session = interaction.client.session
    try:

        #API
        uuid, name = await get_mojang_api(session, username)
        data = await get_hypixel_api(session, username, uuid)

        linkeddiscord = data["player"].get("socialMedia", {}).get("links", {}).get("DISCORD", "")

        if linkeddiscord == interaction.user.name:
            with open("data.json", "r", encoding="utf-8") as f:
                links = json.load(f)
            
            links[str(interaction.user.id)] = {"discord_name": interaction.user.name, "minecraft_username": name.replace("\\", ""), "minecraft_uuid": uuid}

            with open("data.json", "w", encoding="utf-8") as f:
                json.dump(links, f, indent=4)

            embed = set_embed(
                "Linked account",
                f"Linked Discord user `@{interaction.user.name}` to Minecraft account **{name}**.",
                discord.Color.blurple(),
                uuid
            )
        else:
            embed = discord.Embed(
                title = "Discord user not linked to Hypixel",
                description = "To link your Discord account to your Hypixel account: log in to Hypixel and go to **Profile -> Social Media -> Discord** and type your Discord username in chat.",
                color = discord.Color.red(),
                timestamp = datetime.now(tz=timezone.utc)
            )
        embed.set_footer(text="Made by @Quent120", icon_url=ICON)

        await interaction.followup.send(embed=embed)

    #Error
    except Exception as e:
        await handle_error(interaction, e)

# =====================================================================
# /unlink
# =====================================================================

@app_commands.command(name="unlink", description="Unlink your Minecraft account from this Discord bot")
async def unlink(interaction: discord.Interaction):
    await interaction.response.defer()
    try:

        with open("data.json", "r", encoding="utf-8") as f:
            links = json.load(f)
        
        if str(interaction.user.id) in links:
            del links[str(interaction.user.id)]

            with open("data.json", "w", encoding="utf-8") as f:
                json.dump(links, f, indent=4)

            embed = discord.Embed(
                title = "Unlinked account",
                description = f"Unlinked Discord user `@{interaction.user.name}` from **{interaction.client.user.name}**.",
                color = discord.Color.blurple(),
                timestamp = datetime.now(tz=timezone.utc)
            )
            embed.set_footer(text="Made by @Quent120", icon_url=ICON)
        else:
            embed=error_embed(
                f"No Minecraft account found associated to Discord user `@{interaction.user.name}`. Use **/link** to run commands without having to specify a username first."
            )

        await interaction.followup.send(embed=embed)

    #Error
    except Exception as e:
        await handle_error(interaction, e)

# =====================================================================
# /level
# =====================================================================

@app_commands.command(name="level", description="Show how many times the player has reached max level rewards")
@app_commands.describe(username="In game name of the player")
@app_commands.rename(username="player")
async def level(interaction: discord.Interaction, username: str = None):
    await interaction.response.defer()
    session = interaction.client.session
    try:
        #Link
        username = await is_linked(username, interaction.user.id)
        if isinstance(username, discord.Embed):
            await interaction.followup.send(embed=username)
        else:
            #API
            uuid, name = await get_mojang_api(session, username)
            data = await get_hypixel_api(session, username, uuid)
            rank = get_rank(data)

            xp = int(data["player"].get("networkExp", 0))
            level = round(((2 * xp + 30625) ** 0.5) / 50 - 2.5, 2) #no idea how this is right
            maxlevel = round(xp / 79680000, 2)

            if maxlevel < 1:
                description = f"**{name}** is network level `{level:,}`, that's `{maxlevel}` of level 250!"
            else:
                description = f"**{name}** is network level `{level:,}`, that's `{maxlevel}` time(s) level 250!"

            await interaction.followup.send(embed=set_embed(
                f"{rank} {name}'s Network Level",
                description,
                discord.Color(0x14859C),
                uuid
            ))

    #Error
    except Exception as e:
        await handle_error(interaction, e)

# =====================================================================
# /milkshake
# =====================================================================

@app_commands.command(name="milkshake", description="Unsuful information about the milkshake bar from the Slumber Hotel")
async def milkshake(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Slumber Hotel Milkshakes",
        description = "• `Strawberry Milkshake` **2** tickets: jump boost II 60s\n• `Blueberry Milkshake` **1** ticket: slowness II 60s\n• `Apple milkshake` **4** tickets: jump boost II 30s\n• `Banana milkshake` **2** tickets: invisibility II 15s\n• `Mysterious milkshake` **3** tickets: nausea II 5s\n• `Water` **1** ticket: *You now feel very refreshed!*\n• `Rasperry Milkshake` **5** tickets: wither II 15s\n▸ **Cooldown**: `60s`",
        color = discord.Color(0xFF69B4),
        timestamp = datetime.now(tz=timezone.utc)
    )
    embed.set_footer(text="Made by @Quent120", icon_url=ICON)
    await interaction.response.send_message(embed=embed)

# =====================================================================
# /aprilfool
# =====================================================================

#Button
class yearview(discord.ui.View):
    def __init__(self, uuid, name, rank, year, grass, plants, kelp, logs, carrot, golden_carrot):
        super().__init__(timeout=60)
        self.year = year
        self.switchyear.label = f"Switch to {self.year}"
        self.uuid = uuid
        self.name = name
        self.rank = rank
        self.grass = grass; self.plants = plants; self.logs = logs; self.kelp = kelp
        self.carrot  =  carrot; self.golden_carrot = golden_carrot
    
    @discord.ui.button(style=discord.ButtonStyle.primary)
    async def switchyear(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.year == "become sheep":
            newembed=set_embed(
                f"{self.rank} {self.name}'s become sheep stats",
                f"• Grass eaten: `{self.grass:,}`\n• Plants eaten: `{self.plants:,}`\n• Logs eaten `{self.logs:,}`\n• Kelp eaten: `{self.kelp:,}`",
                discord.Color.dark_green(),
                self.uuid
            )
            self.year = "become rabbit"

        else:
            newembed=set_embed(
                f"{self.rank} {self.name}'s become rabbit stats",
                f"• Carrots eaten: `{self.carrot:,}`\n• Golden carrots eaten: `{self.golden_carrot:,}`",
                discord.Color.dark_green(),
                self.uuid
            )
            self.year = "become sheep"

        button.label = f"Switch to {self.year}"
        await interaction.response.edit_message(embed=newembed, view=self)

#Command
@app_commands.command(name="aprilfool", description="Show stats from both 2026 become rabbit and 2024 become sheep april fools")
@app_commands.describe(username="In game name of the player")
@app_commands.choices(year=[
    app_commands.Choice(name="Become Sheep", value="become sheep"),
    app_commands.Choice(name="Become Rabbit", value="become rabbit"),
])
@app_commands.rename(username="player")
async def aprilfool(interaction: discord.Interaction, year: app_commands.Choice[str], username: str = None):
    await interaction.response.defer()
    session = interaction.client.session
    try:
        #Link
        username = await is_linked(username, interaction.user.id)
        if isinstance(username, discord.Embed):
            await interaction.followup.send(embed=username)
        else:
            #API
            uuid, name = await get_mojang_api(session, username)
            data = await get_hypixel_api(session, username, uuid)
            rank = get_rank(data)

            sheep = data["player"].get("stats", {}).get("MainLobby", {}).get("becomeSheep", {}).get("eaten", {})
            grass = sheep.get("grass", 0)
            plants = sheep.get("plants", 0)
            logs =  sheep.get("logs", 0)
            kelp = sheep.get("kelp", 0)
            
            rabbit = data["player"].get("stats", {}).get("MainLobby", {}).get("becomeRabbit", {}).get("eaten", {})
            carrot = rabbit.get("carrot", 0)
            golden_carrot = rabbit.get("golden_carrot", 0)

            if year.value == "become sheep":
                embed=set_embed(
                    f"{rank} {name}'s become sheep stats",
                    f"• Grass eaten: `{grass:,}`\n• Plants eaten: `{plants:,}`\n• Logs eaten `{logs:,}`\n• Kelp eaten: `{kelp:,}`",
                    discord.Color.dark_green(),
                    uuid
                )
                year.value = "become rabbit"

            elif year.value == "become rabbit":
                embed=set_embed(
                    f"{rank} {name}'s become rabbit stats",
                    f"• Carrots eaten: `{carrot:,}`\n• Golden carrots eaten: `{golden_carrot:,}`",
                    discord.Color.dark_green(),
                    uuid
                )
                year.value = "become sheep"
            
            await interaction.followup.send(embed=embed, view=yearview(uuid, name, rank, year.value, grass, plants, logs, kelp, carrot, golden_carrot))
            
    #Error
    except Exception as e:
        await handle_error(interaction, e)

# =====================================================================
# /quickbuyprivacy
# =====================================================================

@app_commands.command(name="quickbuyprivacy", description="Show player's Bed Wars quickbuy layout privacy")
@app_commands.describe(username="In game name of the player")
@app_commands.rename(username="player")
async def quickbuyprivacy(interaction: discord.Interaction, username: str = None):
    await interaction.response.defer()
    session = interaction.client.session
    try:
        #Link
        username = await is_linked(username, interaction.user.id)
        if isinstance(username, discord.Embed):
            await interaction.followup.send(embed=username)
        else:
            #API
            uuid, name = await get_mojang_api(session, username)
            data = await get_hypixel_api(session, username, uuid)
            rank = get_rank(data)
            
            bw_level = get_bedwars_level(data)
            quickbuy_privacy = data["player"].get("stats", {}).get("Bedwars", {}).get("quickbuy_privacy", "NONE")
            if quickbuy_privacy == "NONE":
                description = f"Anyone can share their Quick Buy with {bw_level} {name}."
                color = discord.Color.light_gray()
            elif quickbuy_privacy == "MEDIUM":
                description = f"Only friends, guild members, and party members can share their Quick Buy with {bw_level} {name}."
                color = discord.Color.green()
            elif quickbuy_privacy == "HIGH":
                description = f"Only friends can share their Quick Buy with {bw_level} {name}."
                color = discord.Color.orange()
            elif quickbuy_privacy == "MAX":
                description = f"Nobody can share their Quick Buy with {bw_level} {name}."
                color = discord.Color.red()

            await interaction.followup.send(embed=set_embed(
                f"{rank} {name}'s quickbuy layout privacy",
                f"`{quickbuy_privacy}`: {description}",
                color,
                uuid
            ))

    #Error
    except Exception as e:
        await handle_error(interaction, e)

# =====================================================================
# /sledtype
# =====================================================================

@app_commands.command(name="sledtype", description="Show player's selected sled skin gadget")
@app_commands.describe(username="In game name of the player")
@app_commands.rename(username="player")
async def sledtype(interaction: discord.Interaction, username: str = None):
    await interaction.response.defer()
    session = interaction.client.session
    try:
        #Link
        username = await is_linked(username, interaction.user.id)
        if isinstance(username, discord.Embed):
            await interaction.followup.send(embed=username)
        else:
            #API
            uuid, name = await get_mojang_api(session, username)
            data = await get_hypixel_api(session, username, uuid)
            rank = get_rank(data)

            sled = data["player"].get("vanityMeta", {}).get( "packages", [])
            if "gadget_sled" in sled:
                sledtype = data["player"].get("vanityMeta", {}).get("gadgetSledType", "STONE_SLED").replace("_", " ").title()
                description = f"**{name}** selected the `{sledtype}` skin."
            else:
                description = f"**{name}** hasn't unlocked the sled gadget."
            
            await interaction.followup.send(embed=set_embed(
                f"{rank} {name}'s selected sled gadget",
                description,
                discord.Color.dark_orange(),
                uuid
            ))

    #Error
    except Exception as e:
        await handle_error(interaction, e)

# =====================================================================
# /rankcolor
# =====================================================================

@app_commands.command(name="rankcolor", description="Show player's selected rank color, useful for special ranks such as YOUTUBE or STAFF")
@app_commands.describe(username="In game name of the player")
@app_commands.rename(username="player")
async def rankcolor(interaction: discord.Interaction, username: str = None):
    await interaction.response.defer()
    session = interaction.client.session
    try:
        #Link
        username = await is_linked(username, interaction.user.id)
        if isinstance(username, discord.Embed):
            await interaction.followup.send(embed=username)
        else:
            #API
            uuid, name = await get_mojang_api(session, username)
            data = await get_hypixel_api(session, username, uuid)
            rank = get_rank(data)

            plusColor = data["player"].get("rankPlusColor", "RED").replace("_", " ").title()
            rankColor = data["player"].get("monthlyRankColor", "GOLD").title()
            plusplusmonths = data["player"].get("cachedData", {}).get("superstarMonths", {}).get("value", 0)

            if plusColor == "Red" and rank in ["", "[VIP]", "[VIP+]", "[MVP]", "[MOJANG]"]:
                plusColor = "Gray"
                description = f"**{name}** hasn't unlocked plus colors."
            else:
                description = f"**{name}** selected the `{plusColor}` plus color with `{rankColor}` name."

            if plusplusmonths != 0:
                description += f"\n‣ Total **MVP++** subscription months: `{plusplusmonths:,}`"

            await interaction.followup.send(embed=set_embed(
                f"{rank} {name}'s selected rank color",
                description,
                MINECRAFTCOLORS.get(plusColor, discord.Color.red()),
                uuid
            ))

    #Error
    except Exception as e:
        await handle_error(interaction, e)

# =====================================================================
# /gamblergeorge
# =====================================================================

# OUTDATED DUE TO LATEST UPDATED, WILL UPDATE SOON
'''
@app_commands.command(name="gamblergeorge", description="Show player's Gambler George quest status")
@app_commands.describe(username="In game name of the player")
@app_commands.rename(username="player")
async def gamblergeorge(interaction: discord.Interaction, username: str = None):
    await interaction.response.defer()
    session = interaction.client.session
    try:
        #Link
        username = await is_linked(username, interaction.user.id)
        if isinstance(username, discord.Embed):
            await interaction.followup.send(embed=username)
        else:
            #API
            uuid, name = await get_mojang_api(session, username)
            data = await get_hypixel_api(session, username, uuid)
            rank = get_rank(data)

            bw_level = get_bedwars_level(data)
            unlocked = data["player"].get("stats", {}).get("Bedwars", {}).get("slumber", {}).get("quest", {}).get("started", {}).get("npc_gambler_george", False)

            if not unlocked:
                description = f"{bw_level} {name} hasn't unlocked Gambler George yet."
                color = discord.Color.red()
            else:
                gamblergeorge = data["player"].get("stats", {}).get("Bedwars", {}).get("slumber", {}).get("quest", {}).get("gambler_george", {})
                lostbettime = gamblergeorge.get("lost_bet_time", 0)//1000
                lastlose = int(time.time()) - lostbettime
                if  lastlose < 86400:
                    lastlose = 86400 - lastlose
                    h = lastlose // 3600
                    m = (lastlose % 3600) // 60
                    s = lastlose % 60
                    description = f"{bw_level} {name} **lost** their bet, available again in `{h:,}`h `{m}`m `{s}`s."
                    color = discord.Color.red()
                else:
                    notinprogress = gamblergeorge.get("lost_bet", "false") == "true"
                    betamount = gamblergeorge.get("bet_amout", 0)
                    if not notinprogress and not betamount:
                        description = f"{bw_level} {name}'s Gambler George quest is currently **available**."
                    else:
                        wins = gamblergeorge.get("gamble_games_won", 0)
                        if wins < 2:
                            description = f"Quest **in progress**, {bw_level} {name} won `{wins:,}`/`2` game(s) so far."
                        else:
                            description = f"Quest **in progress**, {bw_level} {name} won `{wins:,}`/`2` games so far.\n*▸ Note that wins past 2 do not reset on loss.*"
                    color = discord.Color.green()

            await interaction.followup.send(embed=set_embed(
                f"{rank} {name}'s Gambler George quest status",
                description,
                color,
                uuid
            ))
    
    #Error
    except Exception as e:
        await handle_error(interaction, e)
'''

# =====================================================================
# /housingadvanced
# =====================================================================

@app_commands.command(name="housingadvanced", description="Show whether the player toggled Housing stats advanced operations or not")
@app_commands.describe(username="In game name of the player")
@app_commands.rename(username="player")
async def housingadvanced(interaction: discord.Interaction, username: str = None):
    await interaction.response.defer()
    session = interaction.client.session
    try:
        #Link
        username = await is_linked(username, interaction.user.id)
        if isinstance(username, discord.Embed):
            await interaction.followup.send(embed=username)
        else:
            #API
            uuid, name = await get_mojang_api(session, username)
            data = await get_hypixel_api(session, username, uuid)
            rank = get_rank(data)

            housingplus = get_housing_plus(data)

            advancedvariableoperations = data["player"].get("housingMeta", {}).get("playerSettings", {}).get("ADVANCED_VARIABLE_OPERATIONS", "BooleanState-false")
            if advancedvariableoperations == "BooleanState-true":
                description = f"{name} **enabled** Housing advanced bitwise stats operations"
                color = discord.Color.green()
            else:
                description = f"{name} **disabled** Housing advanced bitwise stats operations"
                color = discord.Color.red()

            await interaction.followup.send(embed=set_embed(
                f"{housingplus}{rank} {name}'s Housing advanced",
                description,
                color,
                uuid
            ))

    #Error
    except Exception as e:
        await handle_error(interaction, e)

# =====================================================================
# /paidsouls
# =====================================================================

@app_commands.command(name="paidsouls", description="Show how many SkyWars souls the player has paid, legacy feature")
@app_commands.describe(username="In game name of the player")
@app_commands.rename(username="player")
async def paidsouls(interaction: discord.Interaction, username: str = None):
    await interaction.response.defer()
    session = interaction.client.session
    try:
        #Link
        username = await is_linked(username, interaction.user.id)
        if isinstance(username, discord.Embed):
            await interaction.followup.send(embed=username)
        else:
            #API
            uuid, name = await get_mojang_api(session, username)
            data = await get_hypixel_api(session, username, uuid)
            rank = get_rank(data)

            paid_souls = data["player"].get("stats", {}).get("SkyWars", {}).get("paid_souls", 0)
            sw_level = re.sub("§.", "",data["player"].get("stats", {}).get("SkyWars", {}).get("levelFormattedWithBrackets", "§7[§71§7✯§7]§r"))

            if paid_souls >= 200:
                description = f"**{sw_level} {name}** has paid `{paid_souls:,}` SkyWars souls, shame on them for wasting precious coins!"
            else:
                description = f"**{sw_level} {name}** has paid `{paid_souls:,}` SkyWars souls with coins."
            
            await interaction.followup.send(embed=set_embed(
                f"{rank} {name}'s paid SkyWars souls",
                description,
                discord.Color.dark_purple(),
                uuid
            ))

    #Error
    except Exception as e:
        await handle_error(interaction, e)

# =====================================================================
# /bwultimate
# =====================================================================

@app_commands.command(name="ultimate", description="Show player's selected Bed Wars Dreams Ultimate")
@app_commands.describe(username="In game name of the player")
@app_commands.rename(username="player")
async def ultimate(interaction: discord.Interaction, username: str = None):
    await interaction.response.defer()
    session = interaction.client.session
    try:
        #Link
        username = await is_linked(username, interaction.user.id)
        if isinstance(username, discord.Embed):
            await interaction.followup.send(embed=username)
        else:
            #API
            uuid, name = await get_mojang_api(session, username)
            data = await get_hypixel_api(session, username, uuid)
            rank = get_rank(data)

            bw_level = get_bedwars_level(data)
            ultimate = data["player"].get("stats", {}).get("Bedwars", {}).get("selected_ultimate", "NONE").title()

            if ultimate == "None":
                description = f"{bw_level} {name} hasn't selected any ultimate, they will get `Kangaroo` by default on their first game."
                color = discord.Color.light_gray()
            else:
                description = f"{bw_level} {name} selected the `{ultimate}` ultimate."
                color = discord.Color.gold()
        
            await interaction.followup.send(embed=set_embed(
                f"{rank} {name}'s selected Bed Wars Ultimate",
                description,
                color,
                uuid
            ))

    #Error
    except Exception as e:
        await handle_error(interaction, e)

# =====================================================================
# /mmsuicides
# =====================================================================

@app_commands.command(name="mmsuicides", description="Show player's Murdery Mystery deaths from themself")
@app_commands.describe(username="In game name of the player")
@app_commands.rename(username="player")
async def mmsuicides(interaction: discord.Interaction, username: str = None):
    await interaction.response.defer()
    session = interaction.client.session
    try:
        #Link
        username = await is_linked(username, interaction.user.id)
        if isinstance(username, discord.Embed):
            await interaction.followup.send(embed=username)
        else:
            #API
            uuid, name = await get_mojang_api(session, username)
            data = await get_hypixel_api(session, username, uuid)
            rank = get_rank(data)

            mm_level = get_murdermystery_level(data)
            suicides = data["player"].get("stats", {}).get("MurderMystery", {}).get("suicides", 0)

            await interaction.followup.send(embed=set_embed(
            f"{rank} {name}'s Murder Mystery suicides",
            f"{mm_level} {name} shot himself `{suicides:,}` times with a bow and an arrow!",
            discord.Color.dark_red(),
            uuid
            ))

    #Error
    except Exception as e:
        await handle_error(interaction, e)

# =====================================================================
# /collectibles
# =====================================================================

@app_commands.command(name="collectibles", description="Show how many lobby collectibles the player has unlocked")
@app_commands.describe(username="In game name of the player")
@app_commands.rename(username="player")
async def collectibles(interaction: discord.Interaction, username: str = None):
    await interaction.response.defer()
    session = interaction.client.session
    try:
        #Link
        username = await is_linked(username, interaction.user.id)
        if isinstance(username, discord.Embed):
            await interaction.followup.send(embed=username)
        else:
            #API
            uuid, name = await get_mojang_api(session, username)
            data = await get_hypixel_api(session, username, uuid)
            rank = get_rank(data)

            collectibles = len(data["player"].get("vanityMeta", {}).get("packages", []))

            await interaction.followup.send(embed=set_embed(
            f"{rank} {name}'s collectibles unlocked",
            f"**{name}** has unlocked `{collectibles:,}` lobby collectibles.",
            discord.Color(0x2BFCFC),
            uuid
            ))

    #Error
    except Exception as e:
        await handle_error(interaction, e)

# =====================================================================
# /trackedachievements
# =====================================================================

#Button
class achievementsview(discord.ui.View):
    def __init__(self, uuid, name, rank, tracking):
        super().__init__(timeout=60)
        self.uuid = uuid
        self.name = name
        self.rank = rank
        self.tracking = tracking
        if len(self.tracking) == 0:
            self.remove_item(self.showachievements)         

    @discord.ui.button(label="Show all", style=discord.ButtonStyle.primary)
    async def showachievements(self, interaction: discord.Interaction, button: discord.ui.Button):
        button.disabled = True
        await interaction.response.edit_message(embed=set_embed(
            f"{self.rank} {self.name}'s tracked achievements",
            f"### **{self.name}** is curently tracking `{len(self.tracking):,}` tiered achievements.\n• {"\n• ".join(self.tracking).replace("_", " ").title()}",
            discord.Color(0x27BEF5),
            self.uuid
        ), view=self)


#Command
@app_commands.command(name="trackedachievements", description="Show how many tiered achievements the player is curently tracking")
@app_commands.describe(username="In game name of the player")
@app_commands.rename(username="player")
async def trackedachievements(interaction: discord.Interaction, username: str = None):
    await interaction.response.defer()
    session = interaction.client.session
    try:
        #Link
        username = await is_linked(username, interaction.user.id)
        if isinstance(username, discord.Embed):
            await interaction.followup.send(embed=username)
        else:
            #API
            uuid, name = await get_mojang_api(session, username)
            data = await get_hypixel_api(session, username, uuid)
            rank = get_rank(data)

            tracking = data["player"].get("achievementTracking", [])

            await interaction.followup.send(embed=set_embed(
            f"{rank} {name}'s tracked achievements",
            f"**{name}** is curently tracking `{len(tracking):,}` tiered achievements.",
            discord.Color(0x27BEF5),
            uuid
            ), view=achievementsview(uuid, name, rank, tracking))

    #Error
    except Exception as e:
        await handle_error(interaction, e)

# =====================================================================
# /music
# =====================================================================

@app_commands.command(name="music", description="Show player's toggled musics")
@app_commands.describe(username="In game name of the player")
@app_commands.rename(username="player")
async def music(interaction: discord.Interaction, username: str = None):
    await interaction.response.defer()
    session = interaction.client.session
    try:
        #Link
        username = await is_linked(username, interaction.user.id)
        if isinstance(username, discord.Embed):
            await interaction.followup.send(embed=username)
        else:
            #API
            uuid, name = await get_mojang_api(session, username)
            data = await get_hypixel_api(session, username, uuid)
            rank = get_rank(data)

            bedwars = data["player"].get("stats", {}).get("Bedwars", {}).get("pianistEnabled", False)
            buildbattle = data["player"].get("stats", {}).get("BuildBattle", {}).get("music", False)
            housing = data["player"].get("housingMeta", {}).get("playerSettings", {}).get("JUKEBOX_MUSIC", "BooleanState-false") == "BooleanState-true"
            pixelparty = round(data["player"].get("stats", {}).get("Arcade", {}).get("pixel_party_music_volume", 0.5), 2) * 100
            if pixelparty == 0:
                description = f"• Bed Wars : `{bedwars}`\n• Build Battle: `{buildbattle}`\n• Housing: `{housing}`\n• Pixel Party: `False`"
            else:
                description = f"• Bed Wars : `{bedwars}`\n• Build Battle: `{buildbattle}`\n• Housing: `{housing}`\n• Pixel Party: `True` Volume: `{int(pixelparty)}%`"

            await interaction.followup.send(embed=set_embed(
            f"{rank} {name}'s toggled musics",
            description,
            discord.Color.pink(),
            uuid
            ))

    #Error
    except Exception as e:
        await handle_error(interaction, e)


# =====================================================================
# /bingobucks
# =====================================================================

@app_commands.command(name="bingobucks", description="Show how many bingo bucks the player has")
@app_commands.describe(username="In game name of the player")
@app_commands.rename(username="player")
async def bingobucks(interaction: discord.Interaction, username: str = None):
    await interaction.response.defer()
    session = interaction.client.session
    try:
        #Link
        username = await is_linked(username, interaction.user.id)
        if isinstance(username, discord.Embed):
            await interaction.followup.send(embed=username)
        else:
            #API
            uuid, name = await get_mojang_api(session, username)
            data = await get_hypixel_api(session, username, uuid)
            rank = get_rank(data)

            bingobucks = data["player"].get("seasonal", {}).get("bingo", {}).get("bucks", 0)

            await interaction.followup.send(embed=set_embed(
            f"{rank} {name}'s bingo bucks",
            f"**{name}** has `{bingobucks:,}` bingo bucks.",
            discord.Color.green(),
            uuid
            ))

    #Error
    except Exception as e:
        await handle_error(interaction, e)

# =====================================================================
# /housingrepulsor
# =====================================================================

@app_commands.command(name="housingrepulsor", description="Show wheter or not the player has enabled the YouTube repulsor gadget")
@app_commands.describe(username="In game name of the player")
@app_commands.rename(username="player")
async def housingrepulsor(interaction: discord.Interaction, username: str = None):
    await interaction.response.defer()
    session = interaction.client.session
    try:
        #Link
        username = await is_linked(username, interaction.user.id)
        if isinstance(username, discord.Embed):
            await interaction.followup.send(embed=username)
        else:
            #API
            uuid, name = await get_mojang_api(session, username)
            data = await get_hypixel_api(session, username, uuid)
            rank = get_rank(data)

            housingplus = get_housing_plus(data)
        
            ytrepulsor = data["player"].get("housingMeta", {}).get("playerSettings", {}).get("YT_REPULSOR", "IntegerState-0") == "IntegerState-1"

            if ytrepulsor:
                description = f"**{name}** has `enabled` the YouTube repulsor gadget."
                color = discord.Color.green()
            else:
                if rank in ["", "[VIP]", "[VIP+]", "[MVP]", "[MVP+]", "[MVP++]", "[MOJANG]"]:
                    description = f"**{name}** hasn't unlocked the YouTube repulsor gadget."
                else:
                    description = f"**{name}** has `disabled` the YouTube repulsor gadget."
                color = discord.Color.red()

            await interaction.followup.send(embed=set_embed(
            f"{housingplus}{rank} {name}'s YouTube repulsor",
            description,
            color,
            uuid
            ))

    #Error
    except Exception as e:
        await handle_error(interaction, e)

# =====================================================================
# /boxingfish
# =====================================================================

@app_commands.command(name="boxingfish", description="Show player's selected boxing duel fish")
@app_commands.describe(username="In game name of the player")
@app_commands.rename(username="player")
async def boxingfish(interaction: discord.Interaction, username: str = None):
    await interaction.response.defer()
    session = interaction.client.session
    try:
        #Link
        username = await is_linked(username, interaction.user.id)
        if isinstance(username, discord.Embed):
            await interaction.followup.send(embed=username)
        else:
            #API
            uuid, name = await get_mojang_api(session, username)
            data = await get_hypixel_api(session, username, uuid)
            rank = get_rank(data)

            boxingfish = data["player"].get("stats", {}).get("Duels", {}).get("active_boxing_fish", "boxing_fish_raw_fish").replace("boxing_fish_", "").replace("_", " ").title()

            await interaction.followup.send(embed=set_embed(
            f"{rank} {name}'s selected boxing duel fish",
            f"**{name}** selected the `{boxingfish}` boxing fish skin.",
            discord.Color.dark_teal(),
            uuid
            ))

    #Error
    except Exception as e:
        await handle_error(interaction, e)

# =====================================================================
# /longestcombo
# =====================================================================

@app_commands.command(name="longestcombo", description="Show player's longest combo held across all duels")
@app_commands.describe(username="In game name of the player")
@app_commands.rename(username="player")
async def longestcombo(interaction: discord.Interaction, username: str = None):
    await interaction.response.defer()
    session = interaction.client.session
    try:
        #Link
        username = await is_linked(username, interaction.user.id)
        if isinstance(username, discord.Embed):
            await interaction.followup.send(embed=username)
        else:
            #API
            uuid, name = await get_mojang_api(session, username)
            data = await get_hypixel_api(session, username, uuid)
            rank = get_rank(data)

            longestcombo = data["player"].get("stats", {}).get("Duels", {}).get("longest_combo", 0)

            await interaction.followup.send(embed=set_embed(
            f"{rank} {name}'s longest Duels combo",
            f"**{name}** got a combo of `{longestcombo:,}` hits in Duels!",
            discord.Color.orange(),
            uuid
            ))

    #Error
    except Exception as e:
        await handle_error(interaction, e)

# =====================================================================
# /warlordmvp
# =====================================================================

@app_commands.command(name="warlordmvp", description="Show how many times the player was the MVP of a Warlord game")
@app_commands.describe(username="In game name of the player")
@app_commands.rename(username="player")
async def warlordmvp(interaction: discord.Interaction, username: str = None):
    await interaction.response.defer()
    session = interaction.client.session
    try:
        #Link
        username = await is_linked(username, interaction.user.id)
        if isinstance(username, discord.Embed):
            await interaction.followup.send(embed=username)
        else:
            #API
            uuid, name = await get_mojang_api(session, username)
            data = await get_hypixel_api(session, username, uuid)
            rank = get_rank(data)

            mvp = data["player"].get("stats", {}).get("Battleground", {}).get("mvp_count", 0)

            await interaction.followup.send(embed=set_embed(
            f"{rank} {name}'s MVP Warlord games",
            f"**{name}** was the MVP of the game `{mvp:,}` time(s) in Warlord.",
            discord.Color.dark_green(),
            uuid
            ))

    #Error
    except Exception as e:
        await handle_error(interaction, e)

# =====================================================================
# /cookiesgiven
# =====================================================================

@app_commands.command(name="cookiesgiven", description="Show how many packs of cookies the player has sent in Housing")
@app_commands.describe(username="In game name of the player")
@app_commands.rename(username="player")
async def cookiesgiven(interaction: discord.Interaction, username: str = None):
    await interaction.response.defer()
    session = interaction.client.session
    try:
        #Link
        username = await is_linked(username, interaction.user.id)
        if isinstance(username, discord.Embed):
            await interaction.followup.send(embed=username)
        else:
            #API
            uuid, name = await get_mojang_api(session, username)
            data = await get_hypixel_api(session, username, uuid)
            rank = get_rank(data)

            housingplus = get_housing_plus(data)

            cookiesgiven = []
            for i in data["player"].get("housingMeta", {}):
                if i.startswith("given_cookies_"):
                    cookiesgiven.append(i)


            await interaction.followup.send(embed=set_embed(
            f"{housingplus}{rank} {name}'s Housing cookies given",
            f"**{name}** has given `{len(cookiesgiven):,}` packs of cookies in Housing",
            discord.Color(0xD68A3C),
            uuid
            ))

    #Error
    except Exception as e:
        await handle_error(interaction, e)

# =====================================================================
# /favoritemap
# =====================================================================

#Button
class favoritemapsview(discord.ui.View):
    def __init__(self, uuid, name, rank, favoritemaps, color, mode):
        super().__init__(timeout=60)
        self.uuid = uuid
        self.name = name
        self.rank = rank
        self.favoritemaps = favoritemaps
        self.color = color
        self.mode = mode
        if len(self.favoritemaps) == 0:
            self.remove_item(self.showfavoritemaps)
       
    @discord.ui.button(label="Show all", style=discord.ButtonStyle.primary)
    async def showfavoritemaps(self, interaction: discord.Interaction, button: discord.ui.Button):
        button.disabled = True
        await interaction.response.edit_message(embed=set_embed(
            f"{self.rank} {self.name}'s favorite maps",
            f"### **{self.name}** has `{len(self.favoritemaps):,}` maps added to favorite in {self.mode.name}.\n• {"\n• ".join(self.favoritemaps).replace("favoritemap_", "").title()}",
            self.color,
            self.uuid
        ), view=self)

#Command
@app_commands.command(name="favoritemaps", description="Show how many maps a player has added to favorite")
@app_commands.describe(username="In game name of the player")
@app_commands.rename(username="player")
@app_commands.choices(mode=[
    app_commands.Choice(name="Bed Wars", value="bedwars"),
    app_commands.Choice(name="SkyWars", value="skywars"),
    app_commands.Choice(name="Murder Mystery", value="murdermystery"),
])
async def favoritemaps(interaction: discord.Interaction, mode: app_commands.Choice[str], username: str = None):
    await interaction.response.defer()
    session = interaction.client.session
    try:
        #Link
        username = await is_linked(username, interaction.user.id)
        if isinstance(username, discord.Embed):
            await interaction.followup.send(embed=username)
        else:
            #API
            uuid, name = await get_mojang_api(session, username)
            data = await get_hypixel_api(session, username, uuid)
            rank = get_rank(data)

            if mode.value == "bedwars":
                packages = data["player"].get("stats", {}).get("Bedwars", {}).get("packages", [])
                color = discord.Color.red()
            elif mode.value == "skywars":
                packages = data["player"].get("stats", {}).get("SkyWars", {}).get("packages", [])
                color = discord.Color.teal()
            elif mode.value == "murdermystery":
                packages = data["player"].get("stats", {}).get("MurderMystery", {}).get("packages", [])
                color = discord.Color.dark_gold()

            favoritemaps = []
            for i in packages:
                if i.startswith("favoritemap_"):
                    favoritemaps.append(i)

            await interaction.followup.send(embed=set_embed(
            f"{rank} {name}'s favorite maps",
            f"**{name}** has `{len(favoritemaps):,}` maps added to favorite in {mode.name}.",
            color,
            uuid
            ),view=favoritemapsview(uuid, name, rank, favoritemaps, color, mode))

    #Error
    except Exception as e:
        await handle_error(interaction, e)

# =====================================================================
# /deliveryman
# =====================================================================

@app_commands.command(name="deliveryman", description="Show player's stats about the lobby delivery man")
@app_commands.describe(username="In game name of the player")
@app_commands.rename(username="player")
async def deliveryman(interaction: discord.Interaction, username: str = None):
    await interaction.response.defer()
    session = interaction.client.session
    try:
        #Link
        username = await is_linked(username, interaction.user.id)
        if isinstance(username, discord.Embed):
            await interaction.followup.send(embed=username)
        else:
            #API
            uuid, name = await get_mojang_api(session, username)
            data = await get_hypixel_api(session, username, uuid)
            rank = get_rank(data)

            #Daily reward
            streak = data["player"].get("rewardScore", 0)
            higheststreak = data["player"].get("rewardHighScore", 0)
            totalclaim = data["player"].get("totalRewards", 0)
            notoken = data["player"].get("totalDailyRewards", 0)
            tokens = data["player"].get("adsense_tokens", 0)
            usedtokens = totalclaim - notoken
            lastclaimed = data["player"].get("lastAdsenseGenerateTime", 0)//1000

            if lastclaimed == 0:
                lastclaimed = "`Never`"
            else:
                lastclaimed = int(time.time()) - lastclaimed
                if lastclaimed < 86400:
                    lastclaimed = "`today`"
                else:
                    d = lastclaimed // 86400
                    h = (lastclaimed % 86400) // 3600
                    m = (lastclaimed % 3600) // 60
                    lastclaimed = f"`{d:,}d` `{h}h` `{m}m` ago"

            #Cosmetics
            collectibles = data["player"].get("vanityMeta", {}).get( "packages", [])

            count = 0
            for i in collectibles:
                if "treasure" in i or "moustache" in i:
                    count += 1
            
            #Delivery Man
            explastclaimed = data["player"].get("eugene", {}).get("dailyTwoKExp", 0)//1000

            if explastclaimed == 0:
                explastclaimed = "`Never`"
            else:
                explastclaimed = int(time.time()) - explastclaimed
                if explastclaimed < 86400:
                    explastclaimed = "`today`"
                else:
                    d = explastclaimed // 86400
                    h = (explastclaimed % 86400) // 3600
                    m = (explastclaimed % 3600) // 60
                    explastclaimed = f"`{d:,}d` `{h}h` `{m}m` ago"

            embed=set_embed(
            f"{rank} {name}'s delivery man stats",
            "",
            discord.Color.gold(),
            uuid
            )

            embed.add_field(name="Daily reward stats", value=f"• Curent streak: `{streak:,}`\n• Best streak: `{higheststreak:,}`\n• Total claim: `{totalclaim:,}`\n• Last claimed: {lastclaimed}", inline=True)
            embed.add_field(name="\u200b", value=f"• Tokens: `{tokens:,}`\n• Used tokens: `{usedtokens:,}`", inline = True)
            embed.add_field(name=f"**{name}** has unlocked `{count:,}/6` daily reward collectibles", value=f"• Moustache Emote: `{"emote_moustache" in collectibles}`\n• Dig For Treasure Gesture: `{"taunt_treasure" in collectibles}`\n• Treasure Hunter Suit Helmet: `{"suit_treasure_helmet" in collectibles}`\n• Treasure Hunter Suit chestplate: `{"suit_treasure_chestplate" in collectibles}`\n• Treasure Hunter Suit Leggings: `{"suit_treasure_leggings" in collectibles}`\n• Treasure Hunter Suit Boots: `{"suit_treasure_boots" in collectibles}`", inline = False)
            embed.add_field(name="Daily free 2,000xp", value=f"• Last claimed: {explastclaimed}", inline = False)

            await interaction.followup.send(embed=embed)

    #Error
    except Exception as e:
        await handle_error(interaction, e)

# =====================================================================
# /chatchannel
# =====================================================================

@app_commands.command(name="chatchannel", description="Show player's curently used chat channel")
@app_commands.describe(username="In game name of the player")
@app_commands.rename(username="player")
async def chatchannel(interaction: discord.Interaction, username: str = None):
    await interaction.response.defer()
    session = interaction.client.session
    try:
        #Link
        username = await is_linked(username, interaction.user.id)
        if isinstance(username, discord.Embed):
            await interaction.followup.send(embed=username)
        else:
            #API
            uuid, name = await get_mojang_api(session, username)
            data = await get_hypixel_api(session, username, uuid)
            rank = get_rank(data)

            channel = data["player"].get("channel", "ALL").replace("_", "-")

            if channel == "ALL":
                color = discord.Color(0x72EB50)
            elif channel == "PARTY":
                color = discord.Color.blurple()
            elif channel == "GUILD":
                color = discord.Color(0x006114)
            elif channel == "OFFICER":
                color = discord.Color(0x0B6F8A)
            elif channel == "PM":
                color = discord.Color(0xE367EB) 
            elif channel == "SKYBLOCK-COOP": 
                color = discord.Color(0x23DDEB)


            await interaction.followup.send(embed=set_embed(
            f"{rank} {name}'s selected chat channel",
            f"**{name}** is curently using the `{channel}` channel.", 
            color,
            uuid
            ))

    #Error
    except Exception as e:
        await handle_error(interaction, e)

# =====================================================================
# /murdererchance
# =====================================================================

@app_commands.command(name="murdererchance", description="Show wheter or not the player has enabled YouTube rank's increased Murder Mystery chances")
@app_commands.describe(username="In game name of the player")
@app_commands.rename(username="player")
async def murdererchance(interaction: discord.Interaction, username: str = None):
    await interaction.response.defer()
    session = interaction.client.session
    try:
        #Link
        username = await is_linked(username, interaction.user.id)
        if isinstance(username, discord.Embed):
            await interaction.followup.send(embed=username)
        else:
            #API
            uuid, name = await get_mojang_api(session, username)
            data = await get_hypixel_api(session, username, uuid)
            rank = get_rank(data)

            increaseyt = data["player"].get("stats", {}).get("MurderMystery", {}).get("packages", [])

            if "increase_yt_murderer" in increaseyt:
                description = f"**{name}** enabled YouTube rank's increased murderer/detective chances."
                color = discord.Color.green()
            else:
                if rank in ["", "[VIP]", "[VIP+]", "[MVP]", "[MVP+]", "[MVP++]", "[MOJANG]"] and "disable_increase_yt" not in increaseyt:
                    description = f"**{name}** hasn't unlocked YouTube rank's increased murderer/detective chances."
                else:
                    description = f"**{name}** disabled YouTube rank's increased murderer/detective chances."
                color = discord.Color.red()

            await interaction.followup.send(embed=set_embed(
            f"{rank} {name}'s increased Murder Mystery chances",
            description, 
            color,
            uuid
            ))
    
    #Error
    except Exception as e:
        await handle_error(interaction, e)

# =====================================================================
# /classicgames
# =====================================================================

@app_commands.command(name="classicgames", description="Show various player's stats in the Classic Games lobby")
@app_commands.describe(username="In game name of the player")
@app_commands.rename(username="player")
async def classicgames(interaction: discord.Interaction, username: str = None):
    await interaction.response.defer()
    session = interaction.client.session
    try:
        #Link
        username = await is_linked(username, interaction.user.id)
        if isinstance(username, discord.Embed):
            await interaction.followup.send(embed=username)
        else:
            #API
            uuid, name = await get_mojang_api(session, username)
            data = await get_hypixel_api(session, username, uuid)
            rank = get_rank(data)

            legacy = data["player"].get("stats", {}).get("Legacy", {})

            tokens = legacy.get("tokens", 0)
            totaltokens = legacy.get("total_tokens", 0)
            usedtokens = totaltokens - tokens
            nexttoken = legacy.get("next_tokens_seconds", 120)
            if nexttoken >= 60:
                nexttoken = f"`{nexttoken // 60}min {nexttoken % 60}s`"
            else:
                nexttoken = f"`{nexttoken}s`"
                
            arenabrawl = legacy.get("arena_tokens", 0)
            vampirez = legacy.get("vampirez_tokens", 0)
            tkr = legacy.get("gingerbread_tokens", 0)
            quake = legacy.get("quakecraft_tokens", 0)
            walls = legacy.get("walls_tokens", 0)
            paintball  = legacy.get("paintball_tokens", 0)

            rollspeed = legacy.get("speed", "TEN_SECONDS").replace("TEN_", "10").replace("FIVE_", "5").replace("SECONDS", "s")
            channel = legacy.get("preferredChannel", "ALL")

            embed=set_embed(
            f"{rank} {name}'s Classic Games lobby",
            f"", 
            discord.Color.dark_green(),
            uuid
            )

            embed.add_field(name = "Classic Tokens", value = f"• Available tokens: `{tokens:,}`\n• Used tokens: `{usedtokens:,}`\n• Tokens earned: `{totaltokens:,}`\n• Next token in: {nexttoken}/`2min`", inline = True)
            embed.add_field(name = "Settings", value = f"• Tokens roll speed: `{rollspeed}`\n• Preferred channel: `{channel}`", inline = True)
            if totaltokens != 0:
                embed.add_field(name = "Earned tokens details", value = f"• Arena Brawl: `{arenabrawl:,}` *≈ {round((arenabrawl * 2)/60, 1):,}h*\n• VampireZ: `{vampirez:,}` *≈ {round((vampirez * 2)/60, 1):,}h*\n• Turbo Kart Racers: `{tkr:,}` *≈ {round((tkr * 2)/60, 1):,}h*\n• Quakecraft: `{quake:,}` *≈ {round((quake * 2)/60, 1):,}h*\n• The Walls: `{walls:,}` *≈ {round((walls * 2)/60, 1):,}h*\n• Paintball Warfare: `{paintball:,}` *≈ {round((paintball * 2)/60, 1):,}h*", inline = False)

            await interaction.followup.send(embed=embed)

    #Error
    except Exception as e:
        await handle_error(interaction, e)

# =====================================================================
# /poop
# =====================================================================

@app_commands.command(name="poop", description="Show player's collected... poops?")
@app_commands.describe(username="In game name of the player")
@app_commands.rename(username="player")
async def poop(interaction: discord.Interaction, username: str = None):
    await interaction.response.defer()
    session = interaction.client.session
    try:
        #Link
        username = await is_linked(username, interaction.user.id)
        if isinstance(username, discord.Embed):
            await interaction.followup.send(embed=username)
        else:
            #API
            uuid, name = await get_mojang_api(session, username)
            data = await get_hypixel_api(session, username, uuid)
            rank = get_rank(data)
    
            poop = data["player"].get("stats", {}).get("Arcade", {}).get("poop_collected_farm_hunt", 0)
            potato = data["player"].get("stats", {}).get("MainLobby", {}).get("fishing", {}).get("stats", {}).get("permanent", {}).get("individual", {}).get("plant", {}).get("potato", 0)

            description = f"**{name}** has collected `{poop:,}` poops!"

            if poop and potato:
                description += f"\n▸ *Collected poops per potato caught:* `{round(poop/potato, 2)}`"

            await interaction.followup.send(embed=set_embed(
            f"{rank} {name}'s Farm Hunt collected poops",
            description, 
            discord.Color(0x693E13),
            uuid
            ))

    #Error
    except Exception as e:
        await handle_error(interaction, e)

# =====================================================================
# /language
# =====================================================================

@app_commands.command(name="language", description="Show player's selected language")
@app_commands.describe(username="In game name of the player")
@app_commands.rename(username="player")
async def language(interaction: discord.Interaction, username: str = None):
    await interaction.response.defer()
    session = interaction.client.session
    try:
        #Link
        username = await is_linked(username, interaction.user.id)
        if isinstance(username, discord.Embed):
            await interaction.followup.send(embed=username)
        else:
            #API
            uuid, name = await get_mojang_api(session, username)
            data = await get_hypixel_api(session, username, uuid)
            rank = get_rank(data)
    
            language = data["player"].get("userLanguage", "ENGLISH").replace("PIRATE", "PIRATE_SPEAK").replace("PORTUGUESE_BR","BRAZILIAN_PORTUGUESE").replace("PORTUGUESE_PT", "PORTUGUESE").replace("_", " ").capitalize()
            autodetect = data["player"].get("autoDetectLanguage", "false").title()

            await interaction.followup.send(embed=set_embed(
            f"{rank} {name}'s Hypixel language",
            f"**{name}** selected `{language}` as their Hypixel language.\n‣ Auto detect language: `{autodetect}`", 
            discord.Color.og_blurple(),
            uuid
            ))

    #Error
    except Exception as e:
        await handle_error(interaction, e)

# =====================================================================
# /pitallegiance
# =====================================================================

@app_commands.command(name="pitallegiance", description="Show player's last stats in the map Genesis in The Pit")
@app_commands.describe(username="In game name of the player")
@app_commands.rename(username="player")
async def pitallegiance(interaction: discord.Interaction, username: str = None):
    await interaction.response.defer()
    session = interaction.client.session
    try:
        #Link
        username = await is_linked(username, interaction.user.id)
        if isinstance(username, discord.Embed):
            await interaction.followup.send(embed=username)
        else:
            #API
            uuid, name = await get_mojang_api(session, username)
            data = await get_hypixel_api(session, username, uuid)
            rank = get_rank(data)

            allegiance = data["player"].get("stats", {}).get("Pit", {}).get("profile", {}).get("genesis_allegiance", "None")
            points = data["player"].get("stats", {}).get("Pit", {}).get("profile", {}).get("genesis_points", 0)
            lastplayed = data["player"].get("stats", {}).get("Pit", {}).get("profile", {}).get("genesis_allegiance_time", 0) // 1000
            spawn = data["player"].get("stats", {}).get("Pit", {}).get("profile", {}).get("genesis_spawn_in_base", "false")

            if allegiance == "DEMON":
                color = discord.Color.dark_red()
            elif allegiance == "ANGEL":
                color = discord.Color(0xFFFFFF)
            else:
                color = discord.Color.light_grey()

            lastplayed = int(time.time()) - lastplayed
            days = lastplayed // 86400
            hours = (lastplayed % 86400) // 3600

            description = f"• Chosen allegiance: `{allegiance}`\n• Points during last played Genesis rotation: `{points:,}`"
            if lastplayed != 0:
                description += f"\n• Last played: `{days:,}d {hours}h ago`"
            description += f"\n• Faction spawn: `{spawn}`"

            await interaction.followup.send(embed=set_embed(
            f"{rank} {name}'s Genesis alliegance stats",
            description, 
            color,
            uuid
            ))
     
    #Error
    except Exception as e:
        await handle_error(interaction, e)

# =====================================================================
# /smashheroesboosters
# =====================================================================

@app_commands.command(name="smashheroesboosters", description="Show player's Smash Heroes EXP boosters")
@app_commands.describe(username="In game name of the player")
@app_commands.rename(username="player")
async def smashheroesboosters(interaction: discord.Interaction, username: str = None):
    await interaction.response.defer()
    session = interaction.client.session
    try:
        #Link
        username = await is_linked(username, interaction.user.id)
        if isinstance(username, discord.Embed):
            await interaction.followup.send(embed=username)
        else:
            #API
            uuid, name = await get_mojang_api(session, username)
            data = await get_hypixel_api(session, username, uuid)
            rank = get_rank(data)

            smashheroes = data["player"].get("stats", {}).get("SuperSmash", {})

            booster10 = smashheroes.get("expBooster_purchases_10_plays", 0)
            booster30 = smashheroes.get("expBooster_purchases_30_plays", 0)
            booster50 = smashheroes.get("expBooster_purchases_50_plays", 0)
            booster100 = smashheroes.get("expBooster_purchases_100_plays", 0)

            activebooster = smashheroes.get("hero_level_booster_active", "None")
            if activebooster == "None":
                color = discord.Color.light_grey()
            else:
                type = activebooster.get("value", 0)
                remaining = type - activebooster.get("plays", 0)
                if type == 10:
                    color = discord.Color.green()
                elif type == 30:
                    color = discord.Color.yellow()
                elif type == 50:
                    color = discord.Color.dark_gold()
                else:
                    color = discord.Color.red()

            embed=set_embed(
                f"{rank} {name}'s Smash Heroes EXP boosters",
                "", 
                color,
                uuid
            )
            embed.add_field(name = "Purchased EXP Boosters", value = f"• 10 Games booster: `{booster10:,}`\n• 30 Games booster: `{booster30:,}`\n• 50 Games booster: `{booster50:,}`\n• 100 Games booster: `{booster100:,}`", inline = False)
            if activebooster != "None":
                embed.add_field(name = "Active EXP Booster", value = f"→ {type:,} games booster: `{remaining:,}/{type:,}` games remaining", inline = False)
            else:
                embed.add_field(name = "Active EXP Booster", value = f"**{name}** curently doesn't have an active EXP booster.", inline = False)

            await interaction.followup.send(embed=embed)
     
    #Error
    except Exception as e:
        await handle_error(interaction, e)

# =====================================================================
# /bwminion
# =====================================================================

@app_commands.command(name="bwminion", description="Show player's Ender Dust Bed Wars minion from the Slumber Hotel") 
@app_commands.describe(username="In game name of the player")
@app_commands.rename(username="player")
async def bwminion(interaction: discord.Interaction, username: str = None):
    await interaction.response.defer()
    session = interaction.client.session
    try:
        #Link
        username = await is_linked(username, interaction.user.id)
        if isinstance(username, discord.Embed):
            await interaction.followup.send(embed=username)
        else:
            #API
            uuid, name = await get_mojang_api(session, username)
            data = await get_hypixel_api(session, username, uuid)
            rank = get_rank(data)

            bw_level = get_bedwars_level(data)
            minion = data["player"].get("stats", {}).get("Bedwars", {}).get("slumber", {}).get("minion", {})

            if minion:

                font = ImageFont.truetype("Minecraft.ttf", 36)

                # Minion stats
                enderdustcollected = minion.get("ender_dust_collected", 0)
                ticketscollected = minion.get("tickets_collected", 0)
                
                img = Image.open("images/bwminion.png")
                draw = ImageDraw.Draw(img)

                # Text shadow
                draw.text((351, 374), f"{enderdustcollected:,}", font=font, fill=(21, 63, 63))
                draw.text((288, 404), f"{ticketscollected:,}", font=font, fill=(21, 63, 63))
                # Text
                draw.text((348, 371), f"{enderdustcollected:,}", font=font, fill=(85, 255, 255))
                draw.text((285, 401), f"{ticketscollected:,}", font=font, fill=(85, 255, 255))
                
                buffer = io.BytesIO()
                img.save(buffer, format="PNG")
                buffer.seek(0)
                file1 = discord.File(fp=buffer, filename="Ender Dust Minion X.png")


                # Minion Inventory
                enderdust = minion.get("ender_dust", 0)
                tickets = minion.get("tickets", 0)
                if tickets <= 1:
                    tickets = ""

                img = Image.open("images/bwminioninventory.png")
                draw = ImageDraw.Draw(img)

                img_enderdust = Image.open("images/enderdust.png")
                img_ticket = Image.open("images/ticket.png")

                if 0 < enderdust <= 64:
                    img.paste(img_enderdust, (183, 159))
                    if minion.get("tickets", 0) > 0:
                        img.paste(img_ticket, (237, 159))

                    # Text shadow
                    draw.text((237, 183), f"{enderdust}", font=font, fill=(63, 63, 63), anchor="ra")
                    draw.text((291, 183), f"{tickets}", font=font, fill=(63, 63, 63), anchor="ra") # un slot = 54px
                    # Text
                    draw.text((234, 180), f"{enderdust}", font=font, fill=(255, 255, 255), anchor="ra")
                    draw.text((288, 180), f"{tickets}", font=font, fill=(255, 255, 255), anchor="ra")

                elif enderdust > 64:
                    if enderdust > 128:
                        enderdust = 64
                    else:
                        enderdust -= 64

                    img.paste(img_enderdust, (183, 159))
                    img.paste(img_enderdust, (237, 159))
                    img.paste(img_ticket, (291, 159))

                    # Text shadow
                    draw.text((237, 183), "64", font=font, fill=(63, 63, 63), anchor="ra")
                    draw.text((291, 183), f"{enderdust}", font=font, fill=(63, 63, 63), anchor="ra")
                    draw.text((345, 183), f"{tickets}", font=font, fill=(63, 63, 63), anchor="ra")
                    # Text
                    draw.text((234, 180), "64", font=font, fill=(255, 255, 255), anchor="ra")
                    draw.text((288, 180), f"{enderdust}", font=font, fill=(255, 255, 255), anchor="ra")
                    draw.text((342, 180), f"{tickets}", font=font, fill=(255, 255, 255), anchor="ra")
                        
                buffer = io.BytesIO()
                img.save(buffer, format="PNG")
                buffer.seek(0)
                file2 = discord.File(fp=buffer, filename="Ender Dust Minion X Inventory.png")

                await interaction.followup.send(
                    content=f"{bw_level} {rank} {name}'s Ender Dust Minion stats",
                    files=[file1, file2]
                )

            else:
                await interaction.followup.send(embed=set_embed(
                    f"{rank} {name}'s Ender Dust Minion stats",
                    f"{bw_level} {name} hasn't unlocked the Bed Wars minion from the Slumber Hotel.",
                    discord.Color.red(),
                    uuid
                ))

    #Error
    except Exception as e:
        await handle_error(interaction, e)

# =====================================================================
# /smashheroeslimit
# =====================================================================

@app_commands.command(name="smashheroeslimit", description="Show how many Smash Heroes games of 1v1 the player has played")
@app_commands.describe(username="In game name of the player")
@app_commands.rename(username="player")
async def smashheroeslimit(interaction: discord.Interaction, username: str = None):
    await interaction.response.defer()
    session = interaction.client.session
    try:
        #Link
        username = await is_linked(username, interaction.user.id)
        if isinstance(username, discord.Embed):
            await interaction.followup.send(embed=username)
        else:
            #API
            uuid, name = await get_mojang_api(session, username)
            data = await get_hypixel_api(session, username, uuid)
            rank = get_rank(data)

            level = data["player"].get("stats", {}).get("SuperSmash", {}).get("smashLevel", 0)

            games = data["player"].get("stats", {}).get("SuperSmash", {}).get("ONE_V_JUAN_gamesDay", 0)
            firstgame = data["player"].get("stats", {}).get("SuperSmash", {}).get("ONE_V_JUAN_firstGame", 0)//1000

            if int(time.time()) - firstgame > 86400:
                games = 0

            if games < 50:
                color = discord.Color.green()
            else:
                color = discord.Color.red()

            await interaction.followup.send(embed=set_embed(
                f"{rank} {name}'s Smash Heroes games limit",
                f"[{level:,} ✶] {name} has played `{games:,}/50` games of 1v1 today.",
                color,
                uuid
            ))

    #Error
    except Exception as e:
        await handle_error(interaction, e)

# =====================================================================
# /lockedchallenges
# =====================================================================

@app_commands.command(name="lockedchallenges", description="Show player's locked completed Bed Wars challenges")
@app_commands.describe(username="In game name of the player")
@app_commands.rename(username="player")
async def lockedchallenges(interaction: discord.Interaction, username: str = None):
    await interaction.response.defer()
    session = interaction.client.session
    try:
        #Link
        username = await is_linked(username, interaction.user.id)
        if isinstance(username, discord.Embed):
            await interaction.followup.send(embed=username)
        else:
            #API
            uuid, name = await get_mojang_api(session, username)
            data = await get_hypixel_api(session, username, uuid)
            rank = get_rank(data)

            bedwars = data["player"].get("stats", {}).get("Bedwars", {})
            packages = bedwars.get("packages", [])

            lockedchallenges = []
            for elt in bedwars:
                if elt.startswith("bw_challenge_") and elt+"_collected" not in packages:
                    lockedchallenges.append(elt)

            if lockedchallenges == []:
                bw_level = get_bedwars_level(data)
                embed = set_embed(
                    f"{rank} {name}'s locked Bed Wars challenges completions",
                    f"{bw_level} {name} doesn't have any locked challenge completion.",
                    discord.Color.red(),
                    uuid
                )
            else:
                embed=set_embed(
                    f"{rank} {name}'s locked challenges completions",
                    "",
                    discord.Color.purple(),
                    uuid
                )

                for elt in lockedchallenges:
                    title = BEDWARSCHALLENGES[elt]
                    wins = bedwars[elt]

                    besttime = bedwars.get("challenges", {}).get(elt+"_best_time")//1000
                    h = besttime // 3600
                    m = (besttime % 3600) // 60
                    s = besttime % 60

                    embed.add_field(name=f"{title}", value=f"Wins with Challenge: `{wins:,}`\nFastest Completion: `{h:02}:{m:02}:{s:02}`", inline = True)

            await interaction.followup.send(embed=embed)

    #Error
    except Exception as e:
        await handle_error(interaction, e)

# =====================================================================
# /sheepwarskit
# =====================================================================

@app_commands.command(name="sheepwarskit", description="Show player's selected default Sheep Wars kit")
@app_commands.describe(username="In game name of the player")
@app_commands.rename(username="player")
async def sheepwarskit(interaction: discord.Interaction, username: str = None):
    await interaction.response.defer()
    session = interaction.client.session
    try:
        #Link
        username = await is_linked(username, interaction.user.id)
        if isinstance(username, discord.Embed):
            await interaction.followup.send(embed=username)
        else:
            #API
            uuid, name = await get_mojang_api(session, username)
            data = await get_hypixel_api(session, username, uuid)
            rank = get_rank(data)

            kit = data["player"].get("stats", {}).get("WoolGames", {}).get("sheep_wars", {}).get("default_kit", "BUILDER")

            KITCOLORS = {
                "BUILDER": discord.Color.green(),
                "RAIDER": discord.Color.dark_gold(),
                "BOWMAN": discord.Color.blue(),
                "MUNITIONS": discord.Color.purple(),
                "TANK": discord.Color.yellow(),
                "HEAVY": discord.Color.dark_purple()
            }

            await interaction.followup.send(embed=set_embed(
                f"{rank} {name}'s selected Sheep Wars kit",
                f"**{name}** has selected the `{kit}` kit as their default kit.",
                KITCOLORS["kit"],
                uuid
            ))

    #Error
    except Exception as e:
        await handle_error(interaction, e)

# =====================================================================
# /random
# =====================================================================

@app_commands.command(name="random", description="Return a random stat from the API")
@app_commands.describe(username="In game name of the player")
@app_commands.rename(username="player")
async def randomstat(interaction: discord.Interaction, username: str = None):
    await interaction.response.defer()
    session = interaction.client.session
    try:
        #Link
        username = await is_linked(username, interaction.user.id)
        if isinstance(username, discord.Embed):
            await interaction.followup.send(embed=username)
        else:
            #API
            uuid, name = await get_mojang_api(session, username)
            data = await get_hypixel_api(session, username, uuid)
            rank = get_rank(data)

            value = data["player"]
            while isinstance(value , dict):
                rdm = random.randint(0, len(value)-1)
                key, value = list(value.items())[rdm]
                if isinstance(value, list):
                    value = value[random.randint(0, len(value)-1)]
            if isinstance(value, str):
                value = clean_text(value)
            else:
                value = f"{value:,}"
            key = clean_text(key)

            await interaction.followup.send(embed=set_embed(
                f"{rank} {name}'s {key}",
                f"**{key}**: `{value}`\n \n*Note: text formating may be messy due to the API being inconsistent.*",
                discord.Color.random(),
                uuid
            ))
        
    #Error
    except Exception as e:
        await handle_error(interaction, e)


# =====================================================================
# /parkours
# =====================================================================

#Button
class perfectview(discord.ui.View):
    def __init__(self, uuid, name, rank, color, parkour, parkourCompletions, checkpointBests, AVAILABLE_PARKOURS):
        super().__init__(timeout=60)
        self.uuid = uuid
        self.name = name
        self.rank = rank
        self.color = color
        self.parkour = parkour
        self.parkourCompletions = parkourCompletions
        self.checkpointBests = checkpointBests
        self.AVAILABLE_PARKOURS = AVAILABLE_PARKOURS

    @discord.ui.button(label = "Show perfect checkpoints",style=discord.ButtonStyle.primary)
    async def perfectcheckpoints(self, interaction: discord.Interaction, button: discord.ui.Button):
        button.disabled = True

        parkour = {}
        for lobby in self.AVAILABLE_PARKOURS:
                parkour.update({
                    self.AVAILABLE_PARKOURS[lobby]: {
                        "Best Time": self.parkourCompletions.get(lobby, [{}])[0].get("timeTook", "`N/A`"),
                        "Checkpoints": self.checkpointBests.get(lobby, {})
                    }
                })

        description = f"### **{self.name}**'s perfect checkpoints time\n\n"
        perfect = []
        for lobby in parkour:
            found = False
            for cp in parkour[lobby]["Checkpoints"]:
                if parkour[lobby]["Checkpoints"][cp] <= 3005:
                    perfect.append(f"**{lobby} #{int(cp)+1}**: {formatted_time(parkour[lobby]["Checkpoints"][cp])}")
                    found = True
            if found:
                perfect.append("")

        if perfect:
            description += "\n".join(perfect)
            description += "\n**Warning**: Getting a time of exactly 0ms resets the checkpoint's time on the next attempt."
        else:
            description = f"**{self.name}** never got a checkpoint time of 3s or below."
            self.color = discord.Color.red()

        newembed=set_embed(
            f"{self.rank} {self.name}'s lobby parkour time",
            description,
            self.color,
            self.uuid
        )

        await interaction.response.edit_message(embed=newembed, view=self)

#Command
@app_commands.command(name="parkours", description="Show player's combined parkour time across all lobbies and checkpoints")
@app_commands.describe(username="In game name of the player")
@app_commands.rename(username="player")
async def parkours(interaction: discord.Interaction, username: str = None):
    await interaction.response.defer()
    session = interaction.client.session
    try:
        #Link
        username = await is_linked(username, interaction.user.id)
        if isinstance(username, discord.Embed):
            await interaction.followup.send(embed=username)
        else:
            #API
            uuid, name = await get_mojang_api(session, username)
            data = await get_hypixel_api(session, username, uuid)
            rank = get_rank(data)

            AVAILABLE_PARKOURS = {
                "Housing": "Housing",
                "ArcadeGames2": "Arcade",
                "CopsnCrims2024": "Cops and Crims",
                "SkywarsStandard2022": "SkyWars",
                "BedwarsSpring2023": "Bed Wars",
                "SuperSmash": "Smash Heroes",
                "tntLobby2024": "TNT Games",
                "WoolGames": "Wool Games",
                "mainLobby2022": "Main Lobby",
                "MegaWalls": "Mega Walls",
                "Duels": "Duels",
                "BuildBattle": "Build Battle",
                "uhc": "UHC",
                "MurderMystery": "Murder Mystery",
                "Prototype2025": "Prototype",
                "Warlords": "Warlords",
                "Legacy": "Classic Games",
                "BlitzLobby": "Blitz SG"
            }

            parkourCompletions = data["player"].get("parkourCompletions", {})
            checkpointBests = data["player"].get("parkourCheckpointBests", {})

            parkour = {}
            for lobby in AVAILABLE_PARKOURS:
                    parkour.update({
                        AVAILABLE_PARKOURS[lobby]: {
                            "Best Time": parkourCompletions.get(lobby, [{}])[0].get("timeTook", "`N/A`"),
                            "Checkpoints": checkpointBests.get(lobby, {})
                        }
                    })

            total = 0
            missing = []
            for lobby in parkour:
                if parkour[lobby]["Best Time"] == "`N/A`":
                    missing.append(lobby)
                else:
                    total += parkour[lobby]["Best Time"]


            if len(missing) == len(parkour):
                description = f"**{name}** hasn't completed any parkour."
                color = discord.Color.red()
            elif missing:
                description = f"### **{name}** completed `{len(parkour)-len(missing)}/{len(parkour)}` parkour(s) in {formatted_time(total)}."
                color = discord.Color.yellow()
            else:
                description = f"### **{name}** completed all the lobby parkours in {formatted_time(total)}."
                color = discord.Color.orange()

            embed=set_embed(
                f"{rank} {name}'s lobby parkour time",
                description,
                color,
                uuid
            )

            for lobby in parkour:
                checkpoints = ""
                sumofbest = 0
                if parkour[lobby]["Checkpoints"]:
                    for cp in parkour[lobby]["Checkpoints"]:
                            checkpoints += f"**#{int(cp)+1}** `{formatted_time(parkour[lobby]["Checkpoints"][cp]).replace("`", "")}`\n\u200b"
                            sumofbest += parkour[lobby]["Checkpoints"][cp]
                else:
                    checkpoints = "\u200b `N/A`"
                if parkour[lobby]["Best Time"] == "`N/A`":
                    embed.add_field(name=lobby, value=f"▸ {formatted_time(parkour[lobby]["Best Time"])}\n__Best Checkpoints__\n{checkpoints}", inline = True)
                else:
                    embed.add_field(name=lobby, value=f"▸ {formatted_time(parkour[lobby]["Best Time"])}\n__Sum of Best__\n▸ {formatted_time(sumofbest)}\n__Best Checkpoints__\n{checkpoints}", inline = True)
            
            if missing and len(missing) != len(parkour):
                missing = "`, `".join(missing)
                embed.add_field(name="\u200b", value=f"**Warning**: Missing completion for `{missing}`", inline=False)

            await interaction.followup.send(embed=embed, view=perfectview(uuid, name, rank, color, parkour, parkourCompletions, checkpointBests, AVAILABLE_PARKOURS))
        
    #Error
    except Exception as e:
        await handle_error(interaction, e)

# =====================================================================
# /activecollectibles
# =====================================================================

@app_commands.command(name="activecollectibles", description="Show player's selected and favorites collectibles from the lobby")
@app_commands.describe(username="In game name of the player")
@app_commands.rename(username="player")
async def activecollectibles(interaction: discord.Interaction, username: str = None):
    await interaction.response.defer()
    session = interaction.client.session
    try:
        #Link
        username = await is_linked(username, interaction.user.id)
        if isinstance(username, discord.Embed):
            await interaction.followup.send(embed=username)
        else:
            #API
            uuid, name = await get_mojang_api(session, username)
            data = await get_hypixel_api(session, username, uuid)
            rank = get_rank(data)

            favoritecollectibles = data["player"].get("vanityFavorites", "None")
            gadget = data["player"].get("currentGadget", "None")
            clickeffect = data["player"].get("currentClickEffect", "None")
            cloak = data["player"].get("currentCloak", "None")
            particlepack = data["player"].get("particlePack", "None")
            hat = data["player"].get("currentHat", "None")
            pet = data["player"].get("currentPet", "None")
            suit = data["player"].get("outfit", {})

            await interaction.followup.send(embed=set_embed(
            f"{rank} {name}'s selected collectibles",
            f"**Favorite Collectibles**:\n▸ `{favoritecollectibles.replace("TAUNT", "GESTURE").replace("OUTFIT", "SUIT").replace("_HELMET", "").replace("_", " ").replace(";", "`, `").title()}`\n**Gadget**: `{gadget.replace("_", " ").title()}`\n\n**Click Effect**: `{clickeffect.replace("_", " ").title()}`\n**Cloak**: `{cloak.replace("_", " ").title()}`\n**Particle Pack**: `{particlepack.replace("_", " ").title()}`\n**Hat**: `{hat.replace("_", " ").title()}`\n**Pet**: `{pet.replace("_", " ").title()}`\n**Suit**:\n ▸ Helmet: `{suit.get("HELMET", "None").replace("_Helmet", "").replace("_", " ").title()}`\n ▸ Chestplate: `{suit.get("CHESTPLATE", "None").replace("_Helmet", "").replace("_", " ").title()}`\n ▸ Leggings: `{suit.get("LEGGINGS", "None").replace("_Helmet", "").replace("_", " ").title()}`\n ▸ Boots: `{suit.get("BOOTS", "None").replace("_Helmet", "").replace("_", " ").title()}`",
            discord.Color.magenta(),
            uuid
        ))
        
    #Error
    except Exception as e:
        await handle_error(interaction, e)

# =====================================================================
# /fishingratio
# =====================================================================

@app_commands.command(name="fishingratio", description="Show player's fishing stats ratios")
@app_commands.describe(username="In game name of the player")
@app_commands.choices(environment=[
    app_commands.Choice(name="Overall", value="overall"),
    app_commands.Choice(name="Water", value="water"),
    app_commands.Choice(name="Lava", value="lava"),
    app_commands.Choice(name="Ice", value="ice"),
    ],
    catch=[
    app_commands.Choice(name="Fish", value="fish"),
    app_commands.Choice(name="Treasure", value="treasure"),
    app_commands.Choice(name="Junk", value="junk"),
    app_commands.Choice(name="Mythical Fish", value="mythical fish"),
    app_commands.Choice(name="Plant", value="plant"),
    app_commands.Choice(name="Creature", value="creature"),
])
@app_commands.rename(username="player")
@app_commands.rename(catch="type")
async def fishingratio(interaction: discord.Interaction, environment: app_commands.Choice[str], catch: app_commands.Choice[str], username: str = None):
    await interaction.response.defer()
    session = interaction.client.session
    try:
        #Link
        username = await is_linked(username, interaction.user.id)
        if isinstance(username, discord.Embed):
            await interaction.followup.send(embed=username)
        else:
            #API
            uuid, name = await get_mojang_api(session, username)
            data = await get_hypixel_api(session, username, uuid)
            rank = get_rank(data)

            fishing = data["player"].get("stats", {}).get("MainLobby", {}).get("fishing", {}).get("stats", {}).get("permanent", {})
            mythical = data["player"].get("stats", {}).get("MainLobby", {}).get("fishing", {}).get("orbs", {})
            enchants = data["player"].get("stats", {}).get("MainLobby", {}).get("fishing", {}).get("enchants", {})

            if environment.value == "overall":
                water = fishing.get("water", {})
                lava = fishing.get("lava", {})
                ice = fishing.get("ice", {})

                total = sum(water.values()) + sum(lava.values()) + sum(ice.values())
                if catch.value == "mythical fish":
                    compare = sum(v for v in mythical.values() if isinstance(v, int))
                else:
                    compare = water.get(catch.value, 0) + lava.get(catch.value, 0) + ice.get(catch.value, 0)
            else:
                if catch.value == "mythical fish":
                    await interaction.followup.send(embed=error_embed("Cannot track mythical fish's environment."))
                    return
                total = sum(fishing.get(environment.value, {}).values())
                compare = fishing.get(environment.value, {}).get(catch.value, 0)

            if total == 0 or compare == 0:
                result = 0
                odds = 0
            else:
                result = round(total/compare, 2)
                odds = round((compare/total)*100, 2)
            catchname = catch.name.lower()
            if environment.name == "Overall":
                environmentname = ""
            else:
                environmentname = environment.name.lower() + " "

            embed=set_embed(
                f"{rank} {name}'s {catchname} per {environmentname}catch ratio",
                f"**{name}** gets a **{catchname}** in average every `{result:,}` {environmentname} catches. `{odds}%`",
                discord.Color.blue(),
                uuid
            )

            # Enchants
            enchantments = ""
            for name, settings in enchants.items():
                if settings.get("toggle", False):
                    if settings.get("level"):
                        level = roman.toRoman(settings.get("level"))
                    else:
                        level = "I"
                    enchantments += f"\n\u200b • **{name.replace("_", " ").replace("luck", "luck of the sea").title()}** {level}"
            if enchantments:
                embed.add_field(name = "Selected Enchantments", value = enchantments, inline = False)
                    
            await interaction.followup.send(embed=embed)
                
    #Error
    except Exception as e:
        await handle_error(interaction, e)

# =====================================================================
# /cvcshootingrange
# =====================================================================

@app_commands.command(name="cvcshootingrange", description="Show player's shooting range kills from the Cops and Crims lobby")
@app_commands.describe(username="In game name of the player")
@app_commands.rename(username="player")
async def cvcshootingrange(interaction: discord.Interaction, username: str = None):
    await interaction.response.defer()
    session = interaction.client.session
    try:
        #Link
        username = await is_linked(username, interaction.user.id)
        if isinstance(username, discord.Embed):
            await interaction.followup.send(embed=username)
        else:
            #API
            uuid, name = await get_mojang_api(session, username)
            data = await get_hypixel_api(session, username, uuid)
            rank = get_rank(data)

            kills = data["player"].get("achievements", {}).get("copsandcrims_practice_makes_perfect", 0)

            await interaction.followup.send(embed=set_embed(
                f"{rank} {name}'s shooting range kills",
                f"**{name}** killed `{kills:,}` mobs in the Shooting Range from the Cops and Crims lobby.",
                discord.Color.dark_grey(),
                uuid
            ))
                
    #Error
    except Exception as e:
        await handle_error(interaction, e)

# =====================================================================
# /bedwars
# =====================================================================

#List
class modeview(discord.ui.View):
    def __init__(self, uuid, name, rank, bw_level, stats):
        super().__init__(timeout=120)
        self.uuid = uuid
        self.name = name
        self.rank = rank
        self.bw_level = bw_level
        self.stats = stats

        self.select = discord.ui.Select(
            options = [
                discord.SelectOption(label=mode, default=(mode == "Overall"))
                for mode in (MODES | DREAMS).values()
            ]
        )
        self.select.callback = self.switchmode
        self.add_item(self.select)
    
    async def switchmode(self, interaction: discord.Interaction):
        mode = self.select.values[0]

        for opt in self.select.options:
            opt.default = (opt.label == mode)

        newembed = set_embed(
            f"{self.bw_level} {self.rank} {self.name}'s {mode} Bed Wars stats",
            "",
            discord.Color.red(),
            self.uuid
        )

        i = 0
        for type in TYPES:
            i += 1
            total = self.stats.get(mode, {}).get(type, {}).get("total", 0)
            causes = self.stats.get(mode, {}).get(type, {}).get("causes", {})
            causesshown = ""
            for k, v in causes.items():
                percent = round((v / total)*100, 2)
                causesshown += f"▸ {k.replace("_", " ").title()}: `{v:,}` *{percent}%*\n"
            newembed.add_field(name=f"{type.replace("_", " ").title()}", value=f"__Total__: {total:,}\n{causesshown}", inline=True)
            if i % 2 == 0:
                newembed.add_field(name="", value="", inline=True)
        
        await interaction.response.edit_message(embed=newembed, view=self)

# Command
@app_commands.command(name="bedwars", description="Show player's Bed Wars stats and detailed causes")
@app_commands.describe(username="In game name of the player")
@app_commands.rename(username="player")
async def bedwars(interaction: discord.Interaction, username: str = None):
    await interaction.response.defer()
    session = interaction.client.session
    try:
        #Link
        username = await is_linked(username, interaction.user.id)
        if isinstance(username, discord.Embed):
            await interaction.followup.send(embed=username)
        else:
            #API
            uuid, name = await get_mojang_api(session, username)
            data = await get_hypixel_api(session, username, uuid)
            rank = get_rank(data)



            KEYTYPES = ["final_kills", "final_deaths", "kills", "deaths"]

            bedwars = data["player"].get("stats", {}).get("Bedwars", {})

            def get_type(key: str):
                for t in KEYTYPES:
                    if key == t or key.endswith("_" + t):
                        return t
                return None

            def get_mode(key: str):
                for t in MODES.keys():
                    if t == key or key.startswith(t + "_"):
                        return t
                return None

            if bedwars.get("games_played_bedwars_1", 0):
                bw_level = get_bedwars_level(data)

                stats = {}
                for key, value in bedwars.items():
                    result = key.removesuffix("_bedwars").replace("tourney_bedwars4s_", "tourney_bedwars_four_four_")
                    stattype = get_type(result)
                    if stattype:
                        result = result.removesuffix(stattype).removesuffix("_")
                        mode = get_mode(result)
                        cause = result.removeprefix(mode).removeprefix("_") if mode else result
                        dreammode = cause.split("_")[0]

                        if mode == "tourney_bedwars":
                            submode = cause.removeprefix(get_mode(cause) + "_")
                            cause =  submode[2:]
                            tournament = stats.setdefault("Tourneys", {}).setdefault(stattype, {"total": 0, "causes": {}})
                            if cause:
                                tournament["causes"][cause] = tournament["causes"].get(cause, 0) + value
                            else:
                                tournament["total"] += value
                        
                        elif dreammode in DREAMS:
                            cause = cause.removeprefix(dreammode).removeprefix("_")
                            dream = stats.setdefault(DREAMS[dreammode], {}).setdefault(stattype, {"total": 0, "causes": {}})
                            if cause:
                                dream["causes"][cause] = dream["causes"].get(cause, 0) + value
                            else:
                                dream["total"] += value

                        elif mode:
                            gamemode = stats.setdefault(MODES[mode], {}).setdefault(stattype, {"total": 0, "causes": {}})
                            if cause:
                                gamemode["causes"][cause] = value
                            else:
                                gamemode["total"] = value

                        else:
                            overall = stats.setdefault("Overall", {}).setdefault(stattype, {"total": 0, "causes": {}})
                            if cause:
                                overall["causes"][cause] = value
                            else:
                                overall["total"] = value

                embed=set_embed(
                    f"{bw_level} {rank} {name}'s Overall Bed Wars stats",
                    "",
                    discord.Color.red(),
                    uuid
                )

                i = 0
                for type in TYPES:
                    i += 1
                    total = stats.get("Overall", {}).get(type, {}).get("total", 0)
                    causes = stats.get("Overall", {}).get(type, {}).get("causes", {})
                    causesshown = ""
                    for k, v in causes.items():
                        percent = round((v / total)*100, 2)
                        causesshown += f"▸ {k.replace("_", " ").title()}: `{v:,}` *{percent}%*\n"
                    embed.add_field(name=f"{type.replace("_", " ").title()}", value=f"__Total__: {total:,}\n{causesshown}", inline= True)
                    if i % 2 == 0:
                        embed.add_field(name="", value="", inline=True)

                await interaction.followup.send(embed=embed, view=modeview(uuid, name, rank, bw_level, stats))

            else:
                await interaction.followup.send(embed=set_embed(
                    f"{rank} {name}'s Bed Wars stats",
                    f"**{name}** never played Bed Wars.",
                    discord.Color.red(),
                    uuid
                ))

            
                            
    #Error
    except Exception as e:
        await handle_error(interaction, e)