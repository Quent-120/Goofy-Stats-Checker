from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
HYPIXEL_API_KEY = os.getenv('HYPIXEL_API_KEY')
DISCORD_ID = int(os.getenv('DISCORD_ID'))
