import discord
import aiohttp
import asyncio
import json
import re
from datetime import datetime, timezone
from config import HYPIXEL_API_KEY

ICON = "https://minotar.net/helm/d61cd4e9fcf146d2bd1dd9b494405b07/15"

#Converts in game rank colors to Discord embed colors
PLUSCOLORS = {
    "None": discord.Color.light_grey(),
    "Red": discord.Color.red(),
    "Gold": discord.Color(0xF2A224),
    "Green": discord.Color(0x72EB50),
    "Yellow": discord.Color.yellow(),
    "Light Purple": discord.Color(0xC936E0),
    "White": discord.Color(0xFFFFFF),
    "Blue": discord.Color(0x3244AD),
    "Dark Green": discord.Color(0x006114),
    "Dark Red": discord.Color(0x780000),
    "Dark Aqua": discord.Color(0x0B6F8A),
    "Dark Purple": discord.Color(0x68077A),
    "Dark Gray": discord.Color(0x3D3D3D),
    "Black": discord.Color(0x010101),
    "Dark Blue": discord.Color(0x0E0673),
}

BEDWARSSTARS = {
    "star_black_open": "✫",
    "star_white_circled": "✪",
    "star_white_outlined": "⚝",
    "star_four_clubs": "✥",
    "star_black_outlined": "✭",
    "star_four_pointed": "✦",
    "star_pinwheel": "✵",
    "star_hollow": "✰",
    "star_nautical": "✯"
}

BEDWARSBRACKETS = {
    "prestige_bracket_none": ("[", "]"),
    "prestige_bracket_curly": ("{", "}"),
    "prestige_bracket_angled": ("<", ">"),
    "prestige_bracket_parenthesis": ("(", ")"),
    "prestige_bracket_double_angle_quotation_mark": ("«", "»")
}

MURDERMYSTERYPREFIXICON = {
    "prefixicon_default": "✪",
    "prefixicon_alpha": "α",
    "prefixicon_divine": "Φ",
    "prefixicon_zero": "∅",
    "prefixicon_sigma": "Σ",
    "prefixicon_rich": "$",
    "prefixicon_omega": "Ω",
    "prefixicon_equivalence": "≡",
    "prefixicon_podium": "π",
    "prefixicon_florin": "ƒ"
}

BEDWARSCHALLENGES = {
    "bw_challenge_no_team_upgrades": "Renegade",
    "bw_challenge_no_utilities": "Warmonger",
    "bw_challenge_selfish": "Selfish",
    "bw_challenge_slow_generator": "Minimum Wage",
    "bw_challenge_assassin": "Assassin",
    "bw_challenge_reset_armor": "Regular Shopper",
    "bw_challenge_invisible_shop": "Invisible Shop",
    "bw_challenge_collector": "Collector",
    "bw_challenge_woodworker": "Woodworker",
    "bw_challenge_sponge": "Bridging for Dummies",
    "bw_challenge_toxic_rain": "Toxic Rain",
    "bw_challenge_defuser": "Defuser",
    "bw_challenge_mining_fatigue": "Lazy Miner",
    "bw_challenge_no_healing": "Ultimate UHC",
    "bw_challenge_hotbar": "Sleight of Hand",
    "bw_challenge_weighted_items": "Weighted Items",
    "bw_challenge_knockback_stick_only": "Social Distancing",
    "bw_challenge_no_swords": "Swordless",
    "bw_challenge_archer_only": "Marksman",
    "bw_challenge_patriot": "Patriot",
    "bw_challenge_stamina": "Stamina",
    "bw_challenge_no_sprint": "Old Man",
    "bw_challenge_capped_resources": "Capped Resources",
    "bw_challenge_stop_light": "Red Light, Green Light",
    "bw_challenge_delayed_hitting": "Slow Reflexes",
    "bw_challenge_no_hitting": "Pacifist",
    "bw_challenge_master_assassin": "Master Assassin",
    "bw_challenge_no_shift": "Standing Tall",
    "bw_challenge_protect_the_president": "Protect the President",
    "bw_challenge_cant_touch_this": "Can't Touch This",
    "bw_challenge_wool_warrior": "Wool Warrior",
    "bw_challenge_anchor": "Anchor",
    "bw_challenge_no_dreaming": "No Dreaming",
    "bw_challenge_quick_maths": "Quick Maths",
    "bw_challenge_block_repellent_beds": "Blockrepellent Beds",
    "bw_challenge_midnight": "Midnight",
    "bw_challenge_beds_and_bloodlust": "Beds & Bloodlust",
    "bw_challenge_beg_and_barter": "Beg & Barter",
    "bw_challenge_halved_and_doubled": "Halved & Doubled"
}

def get_mm_prefixstat(data):
    prefixstat = data["player"].get("stats", {}).get("MurderMystery", {})
    MURDERMYSTERYPREFIXSTAT = {
        "prefixstat_none": "",
        "prefixstat_classic_kills": ("[", prefixstat.get("wins_MURDER_CLASSIC", 0), "]"),
        "prefixstat_classic_wins": ("[", prefixstat.get("kills_MURDER_CLASSIC", 0), "]"),
        "prefixstat_infection_kills": ("{", prefixstat.get("kills_MURDER_INFECTION", 0), "}"),
        "prefixstat_infection_wins": ("{", prefixstat.get("wins_MURDER_INFECTION", 0), "}"),
        "prefixstat_assassins_kills": ("(", prefixstat.get("kills_MURDER_ASSASSINS", 0), ")"),
        "prefixstat_assassins_wins": ("(", prefixstat.get("wins_MURDER_ASSASSINS", 0), ")")
    }
    return MURDERMYSTERYPREFIXSTAT

def error_embed(description):
    return discord.Embed(
        title = "Error",
        description = description,
        color = discord.Color.red(),
        timestamp = datetime.now(tz=timezone.utc)
    )

def set_embed(title, description, color, uuid):
    embed = discord.Embed(
        title = title,
        description = description,
        color = color,
        timestamp = datetime.now(tz=timezone.utc)
    ) 
    embed.set_thumbnail(url=f"https://minotar.net/helm/{uuid}/48")
    embed.set_footer(text="Made by @Quent120", icon_url=ICON)
    return embed

async def get_mojang_api(session, username):
    async with session.get(f"https://api.mojang.com/users/profiles/minecraft/{username}") as response:
        mojang_data = await response.json()
    if response.status == 404 or response.status == 400:
        raise ValueError(f"Couldn't find player by the name of `{username}`.")
    if response.status != 200:
        error = mojang_data["errorMessage"]
        raise ValueError(f"Error {response.status}. Mojang's API returned with error: `{error}`.")
    uuid = mojang_data["id"]
    name = mojang_data["name"].replace("_", r"\_")
    return  uuid, name

async def get_hypixel_api(session, username, uuid):
    async with session.get("https://api.hypixel.net/player", params={"key": HYPIXEL_API_KEY, "uuid": uuid}) as response:
        data = await response.json()
    if response.status != 200:
        raise ValueError(f"Error {response.status}. Something went wrong with Hypixel's API.")
    if data["player"] is None:
        raise ValueError(f"`{username}` never logged into Hypixel.")
    return data

async def is_linked(username, discordid):
    discordid = str(discordid)
    if username is None:
        with open("data.json", "r", encoding="utf-8") as f:
            links = json.load(f)
        if discordid in links:
            username = links.get(discordid).get("minecraft_username")
            return username
        else:
            embed = discord.Embed(
                title = "No linked account found",
                description = "No Minecraft account associated with your Discord user. Use **/link** to use commands without specifying a username.",
                color = discord.Color.red(),
                timestamp = datetime.now(tz=timezone.utc)
            )
            return embed
    return username

def clean_text(text: str) -> str:
    text = re.sub(r'(?<=[A-Z])(?=[A-Z][a-z])', ' ', text)
    text = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', text)
    text = re.sub(r'(?<=[a-zA-Z])(?=[0-9])|(?<=[0-9])(?=[a-zA-Z])', ' ', text)
    text = re.sub(r'[_\-;.]+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text.title()

async def handle_error(interaction, error):
    if isinstance(error, ValueError):
        description = str(error)
    elif isinstance(error, aiohttp.ContentTypeError):
        description = "The API returned an invalid response format, expected JSON. Try again later."
    elif isinstance(error, aiohttp.ClientError):
        description = "An error occured while trying to connect to the API. Try again later."
        print("API link: https://developer.hypixel.net/dashboard/")
    elif isinstance(error, asyncio.TimeoutError):
        description = "The API took too long to respond. Try again later."
    elif isinstance(error, KeyError):
        print("Missing field:", error)
        description = f"Unexpected API response: missing field `{error}`."
    elif isinstance(error, UnboundLocalError):
        print("Error:", error)
        description = "An unexpected value was received. Please try again."
    else:
        print("Error:", error)
        description = "Something went wrong."
    await interaction.response.send_message(embed = error_embed(description))

def get_rank(data):
    prefix = data["player"].get("prefix", "")
    rank = data["player"].get("rank", "")
    newPackageRank = data["player"].get("newPackageRank", "")
    monthlyPackageRank = data["player"].get("monthlyPackageRank", "")

    #Special Ranks
    if prefix == "§6[MOJANG]":
        displayRank = "[MOJANG]"
    elif prefix == "§6[EVENTS]":
        displayRank = "[EVENTS]"
    elif prefix == "§d[PIG§b+++§d]":
        displayRank = "[PIG+++]"
    elif prefix == "§d[INNIT]":
        displayRank = "[INNIT]"
    elif rank == "YOUTUBER":
        displayRank = "[YOUTUBE]"
    elif rank == "STAFF":
        displayRank = "[ዞ]"

    #Purchasable Ranks
    elif monthlyPackageRank == "SUPERSTAR":
        displayRank = "[MVP++]"
    elif newPackageRank == "MVP_PLUS":
        displayRank = "[MVP+]"
    elif newPackageRank == "MVP":
        displayRank = "[MVP]"
    elif newPackageRank == "VIP_PLUS":
        displayRank = "[VIP+]"
    elif newPackageRank == "VIP":
        displayRank = "[VIP]"
    else:
        displayRank = ""
    
    return displayRank

def calculate_bedwars_xp(exp: int) -> tuple[int, float]: #Made by @Foui_
    PRESTIGE_XP = 487000
    EASY_XP = [500, 1000, 2000, 3500]
    EASY_TOTAL = 7000
    XP_PER = 5000

    prestige = exp // PRESTIGE_XP
    level = prestige * 100
    rem = exp % PRESTIGE_XP

    if rem < EASY_TOTAL:
        cumulative = 0
        for i, xp in enumerate(EASY_XP):
            if rem < cumulative + xp:
                progress = (rem - cumulative) / xp
                return (level, progress)
            cumulative += xp
            level += 1
    else:
        level += 4
        rem   -= EASY_TOTAL
        level += rem // XP_PER
        progress = (rem % XP_PER) / XP_PER
        return (level, progress)

    return (level, 0.0)

def format_number(n):
    if n != "" and n >= 1000:
        return f"{round(n / 1000, 1)}k"
    return str(n)

def get_bedwars_level(data):
    level = str(int(calculate_bedwars_xp(data["player"].get("stats", {}).get("Bedwars", {}).get("Experience", 0))[0]))
    star = BEDWARSSTARS.get(data["player"].get("stats", {}).get("Bedwars", {}).get("active_star", "star_black_open"), "✫")
    brackets = BEDWARSBRACKETS.get(data["player"].get("stats", {}).get("Bedwars", {}).get("active_prestige_bracket", "prestige_bracket_none"), ("[", "]"))

    formating = data["player"].get("stats", {}).get("Bedwars", {}).get("dreamfeast", {}).get("toggles", {})
    bold = "**" if formating.get("toggle_bold_numbers", False) else ""
    strike = "~~" if formating.get("toggle_strikethrough_brackets", False) else ""
    underline = "__" if formating.get("toggle_underlined_prestige", False) else ""

    return f"{underline}{strike}{brackets[0]}{strike}{bold}{level}{bold}{star}{strike}{brackets[1]}{strike}{underline}"

def get_murdermystery_level(data):
    prefixstat = data["player"].get("stats", {}).get("MurderMystery", {}).get("active_prefixstat", "prefixicon_none")
    prefixstat = get_mm_prefixstat(data).get(prefixstat)

    prefixicon = data["player"].get("stats", {}).get("MurderMystery", {}).get("active_prefixicon", "prefixicon_default")
    prefixicon = MURDERMYSTERYPREFIXICON.get(prefixicon)

    return f"{prefixstat[0] if prefixstat else ""}{format_number(prefixstat[1] if prefixstat else "")}{prefixicon}{prefixstat[2] if prefixstat else ""}"