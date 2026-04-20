from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import Message
from config import *
from SHUKLAMUSIC import app
from SHUKLAMUSIC.core.call import SHUKLA
from SHUKLAMUSIC.utils import bot_sys_stats
from SHUKLAMUSIC.utils.decorators.language import language
from SHUKLAMUSIC.utils.inline import supp_markup
from SHUKLAMUSIC.utils.clonedb import get_clone_info
from config import BANNED_USERS

# Aapke database.py ke mutabiq mongodb ko import kar rahe hain
from SHUKLAMUSIC.core.mongo import mongodb as db

# Database collection
ping_db = db.ping_config 

# ==========================================
# HELPER FUNCTION: OWNER CHECK
# ==========================================
async def is_owner(client, message):
    bot = await client.get_me()
    clone_info = await get_clone_info(bot.id)
    return clone_info and clone_info.get("user_id") == message.from_user.id

# ==========================================
# SET PING COMMAND (FOR CLONE OWNER)
# ==========================================
@Client.on_message(filters.command("setping"))
async def set_ping_msg(client, message: Message):
    if not await is_owner(client, message):
        return await message.reply_text("> ❌ **Access Denied:** This command is strictly for the bot owner.")

    if len(message.command) < 2:
        return await message.reply_text(
            "❌ **Usage:** `/setping [Message]`\n\n"
            "**Aap ye placeholders use kar sakte hain:**\n"
            "• `{ping}` - Bot ki speed\n"
            "• `{pytgping}` - Call server speed\n"
            "• `{uptime}` - Bot kabse online hai\n"
            "• `{ram}` - RAM usage\n"
            "• `{cpu}` - CPU usage\n"
            "• `{disk}` - Disk space\n"
            "• `{mention}` - Bot ka naam"
        )
    try:
        # Formatting (bold/italic) ko preserve karne ke liye
        new_msg = message.text.html.split(None, 1)[1]
    except IndexError:
        return await message.reply_text("❌ Kuch text likhein command ke baad.")

    bot = await client.get_me()
    
    # Har clone bot ka data uske bot_id se alag save hoga
    await ping_db.update_one(
        {"bot_id": bot.id}, 
        {"$set": {"message": new_msg}}, 
        upsert=True
    )
    await message.reply_text("✅ **Ping message placeholders ke saath set ho gaya hai!**")

# ==========================================
# PING COMMAND
# ==========================================
@Client.on_message(filters.command("ping", prefixes=["/"]) & ~BANNED_USERS)
@language
async def ping_com(client, message: Message, _):
    bot = await client.get_me()
    start = datetime.now()
    
    response = await message.reply_photo(
        photo="https://files.catbox.moe/1ovfu4.jpg",
        caption=_["ping_1"].format(bot.mention),
    )
    
    # Stats calculate karna
    pytgping = await SHUKLA.ping()
    UP, CPU, RAM, DISK = await bot_sys_stats()
    resp = (datetime.now() - start).microseconds / 1000
    
    # Database se is specific clone bot ka custom message uthana
    data = await ping_db.find_one({"bot_id": bot.id})
    
    if data and "message" in data:
        custom_text = data["message"]
        # Saare placeholders ko asli data se replace karna
        final_caption = custom_text.replace("{ping}", str(resp)) \
                                   .replace("{pytgping}", str(pytgping)) \
                                   .replace("{uptime}", str(UP)) \
                                   .replace("{ram}", str(RAM)) \
                                   .replace("{cpu}", str(CPU)) \
                                   .replace("{disk}", str(DISK)) \
                                   .replace("{mention}", bot.mention)
    else:
        # Agar koi message set nahi hai toh default chalega
        final_caption = _["ping_2"].format(resp, bot.mention, UP, RAM, CPU, DISK, pytgping)

    await response.edit_text(final_caption, reply_markup=supp_markup(_))
  
