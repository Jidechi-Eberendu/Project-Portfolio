import asyncio
import sqlite3
import random
import time
import datetime
import requests
import tempfile
import re
from telethon import TelegramClient, events
from collections import defaultdict
from config import (
    API_ID,
    API_HASH,
    SESSION_NAME,
    OPENAI_API_KEY,
    OPENAI_API_URL,
    OPENAI_MODEL,
    IMAGE_CHANNEL_ID,
    ADMIN_ID,
    ELEVENLABS_API_KEY,
    VOICE_ID
)

# Read the AI persona prompt from the txt file
try:
    with open("prompt.txt", "r", encoding="utf-8") as file:
        system_prompt = file.read()
except FileNotFoundError:
    print("Error: prompt.txt not found. Please create the file with the AI's persona.")
    system_prompt = "You are a helpful assistant." # Fallback prompt

# ✅ Create Telegram client
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

# ✅ Connect to SQLite Database
conn = sqlite3.connect("chat_memory.db")
cursor = conn.cursor()

# ✅ Create conversation history table
cursor.execute("""
CREATE TABLE IF NOT EXISTS conversations (
    user_id INTEGER,
    role TEXT,
    message TEXT
)
""")
conn.commit()

# ✅ Track user message counts
cursor.execute("""
CREATE TABLE IF NOT EXISTS user_message_count (
    user_id INTEGER PRIMARY KEY,
    count INTEGER DEFAULT 0
)
""")
conn.commit()

# ✅ Create user interaction logging table
cursor.execute("""
CREATE TABLE IF NOT EXISTS user_interactions (
    user_id INTEGER,
    timestamp REAL
)
""")
conn.commit()

# ✅ Store user messages for batching replies (per user)
user_message_buffer = defaultdict(list)

# ✅ Function to get the admin entity at startup
async def get_admin_entity():
    try:
        await client.get_entity(ADMIN_ID)
        print(f"Admin entity for {ADMIN_ID} successfully fetched and cached.")
    except Exception as e:
        print(f"Warning: Failed to fetch admin entity for {ADMIN_ID}. Error: {e}")

# ✅ Schedule a reply for a user after 1 minute
def schedule_reply(user_id):
    async def reply():
        await asyncio.sleep(60)
        if user_id in user_message_buffer:
            messages = user_message_buffer.pop(user_id)
            summarized_text = "\n".join(messages[-5:])
            ai_reply = await chat_with_openai(user_id, summarized_text)
            try:
                await client.get_dialogs(limit=100)
                entity = await client.get_entity(user_id)
                await client.send_message(entity, ai_reply)
            except Exception as e:
                print(f"Error sending message to user {user_id}: {e}")
    asyncio.create_task(reply())

# ✅ Function to fetch a random image from the channel
async def send_random_image(user_id):
    await asyncio.sleep(random.randint(15, 45))
    image_list = []
    async for message in client.iter_messages(IMAGE_CHANNEL_ID, limit=100):
        if message.photo:
            image_list.append(message)
    if not image_list:
        await client.send_message(user_id, "Sorry, no images available right now 😔")
        return
    random_image = random.choice(image_list)
    await client.send_file(user_id, random_image, caption=random.choice([
        "Miss me? 😘",
        "Thought you'd like this one 😉",
        "Just for you, baby 😏",
        "Had to send you this one 😘",
        "You like what you see? 👀",
        "Only for you, don’t tell anyone 😉",
        "Bet you can't handle this 😏",
        "Couldn’t resist sharing this with you 😘",
        "A little something to keep you thinking about me 😏",
        "Too hot to keep to myself 🔥",
        "You’re lucky I like you 😘",
        "This one’s special… just like you 😉",
        "One look and you'll be addicted 😏",
        "Feeling generous today 😘",
        "Hope this makes your day better 😉"
    ]))

## URL Removal Function
def remove_urls(text):
    url_pattern = re.compile(r'https?://\S+|www\.\S+')
    return url_pattern.sub(r'', text)

# ✅ Handle incoming messages
@client.on(events.NewMessage)
async def handler(event):
    if event.is_group:
        return
    user_id = event.sender_id
    user_message = event.raw_text.strip()

    timestamp = time.time()
    cursor.execute("INSERT INTO user_interactions (user_id, timestamp) VALUES (?, ?)", (user_id, timestamp))
    conn.commit()

    cursor.execute("SELECT count FROM user_message_count WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    msg_count = result[0] if result else 0
    msg_count += 1
    cursor.execute("INSERT INTO user_message_count (user_id, count) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET count = ?", (user_id, msg_count, msg_count))
    conn.commit()

    if any(word in user_message.lower() for word in ["voice", "vn", "voicenote"]) or (msg_count == 2) or (msg_count > 0 and msg_count % 7 == 0):
        delay_seconds = random.randint(60, 180)
        await asyncio.sleep(delay_seconds)
        clean_message = remove_urls(user_message)
        ai_reply = await chat_with_openai_voice(user_id, clean_message)
        await generate_and_send_voice_note(user_id, ai_reply)
        user_message_buffer[user_id] = []
        return

    if user_message.startswith("/stats") and user_id == ADMIN_ID:
        await send_stats(user_id)
        return

    if user_message.startswith("/broadcast") and user_id == ADMIN_ID:
        if event.message.media:
            broadcast_message = user_message[len("/broadcast"):].strip()
            await broadcast_to_users(broadcast_message, media=event.message.media)
        else:
            broadcast_message = user_message[len("/broadcast"):].strip()
            if broadcast_message:
                await broadcast_to_users(broadcast_message)
            else:
                await client.send_message(user_id, "Usage: /broadcast <your message> [optional media]")
        return

    user_message_buffer[user_id].append(user_message)

    if len(user_message_buffer[user_id]) == 1:
        schedule_reply(user_id)

    if any(keyword in user_message.lower() for keyword in ["send pic", "pic", "show me", "picture", "photo"]):
        await send_random_image(user_id)
        user_message_buffer[user_id] = []
        return

    if msg_count % 20 == 0:
        await send_random_image(user_id)
        user_message_buffer[user_id] = []

# ✅ Function to send messages to OpenAI GPT-4o-mini
async def chat_with_openai(user_id, user_message):
    cursor.execute("SELECT role, message FROM conversations WHERE user_id = ?", (user_id,))
    history = cursor.fetchall()
    messages = [{"role": "system", "content": system_prompt}]
    for role, message in history[-5:]:
        messages.append({"role": role, "content": message})
    messages.append({"role": "user", "content": user_message})

    response = requests.post(
        OPENAI_API_URL,
        headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
        json={"model": OPENAI_MODEL, "messages": messages, "temperature": 0.7, "max_tokens": 200}
    )
    if response.status_code == 200:
        ai_reply = response.json().get("choices", [{}])[0].get("message", {}).get("content", "No response.")
    else:
        print("Error:", response.text)
        ai_reply = "Sorry, something went wrong."

    cursor.execute("INSERT INTO conversations (user_id, role, message) VALUES (?, ?, ?)", (user_id, "user", user_message))
    cursor.execute("INSERT INTO conversations (user_id, role, message) VALUES (?, ?, ?)", (user_id, "assistant", ai_reply))
    conn.commit()
    return ai_reply

# ✅ Voice note version (shorter output)
async def chat_with_openai_voice(user_id, user_message):
    return await chat_with_openai(user_id, user_message)

# ✅ Function to generate and send a voice note
async def generate_and_send_voice_note(user_id, text_to_speak):
    cleaned_text = remove_urls(text_to_speak)
    print(f"Generating voice note for user {user_id} with text: '{cleaned_text}'")
    try:
        response = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream",
            headers={
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": ELEVENLABS_API_KEY
            },
            json={
                "text": cleaned_text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            }
        )
        response.raise_for_status()

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_audio_file:
            temp_audio_file.write(response.content)
            temp_audio_file_path = temp_audio_file.name

        await client.send_file(user_id, temp_audio_file_path, voice_note=True)
        print(f"Successfully sent voice note to user {user_id}.")

    except requests.exceptions.RequestException as e:
        print(f"Error calling ElevenLabs API: {e}")
        try:
            await client.send_message(user_id, "Sorry, I couldn't generate a voice note right now.")
        except Exception as send_e:
            print(f"Error sending fallback message to user {user_id}: {send_e}")
    except Exception as e:
        print(f"Error sending voice note: {e}")
        try:
            await client.send_message(user_id, "Sorry, something went wrong while sending the voice note.")
        except Exception as send_e:
            print(f"Error sending fallback message to user {user_id}: {send_e}")
    finally:
        try:
            import os
            if 'temp_audio_file_path' in locals() and os.path.exists(temp_audio_file_path):
                os.remove(temp_audio_file_path)
                print(f"Cleaned up temporary file: {temp_audio_file_path}")
        except Exception as cleanup_error:
            print(f"Error cleaning up temporary file: {cleanup_error}")

# ✅ Send daily updates to the admin
async def send_daily_update():
    while True:
        now = datetime.datetime.now()
        midnight = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        sleep_time = (midnight - now).total_seconds()
        await asyncio.sleep(sleep_time)

        one_day_ago = time.time() - 86400
        cursor.execute("SELECT COUNT(DISTINCT user_id) FROM user_interactions WHERE timestamp > ?", (one_day_ago,))
        unique_users_count = cursor.fetchone()[0]

        update_message = f"Daily Update:\nNew users interacted with Amara in the last 24 hours: {unique_users_count}"
        try:
            await client.send_message(ADMIN_ID, update_message)
        except Exception as e:
            print(f"Error sending daily update to admin: {e}")

        cursor.execute("DELETE FROM user_interactions WHERE timestamp < ?", (one_day_ago,))
        conn.commit()

# ✅ Send stats on demand
async def send_stats(admin_id):
    one_day_ago = time.time() - 86400
    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM user_interactions WHERE timestamp > ?", (one_day_ago,))
    unique_users_count = cursor.fetchone()[0]
    stats_message = f"On-Demand Stats:\nNew users interacted with Amara in the last 24 hours: {unique_users_count}"
    try:
        await client.send_message(ADMIN_ID, stats_message)
    except Exception as e:
        print(f"Error sending stats to admin: {e}")

# ✅ Broadcast a message (with optional media) to all users
async def broadcast_to_users(message, media=None):
    cursor.execute("SELECT DISTINCT user_id FROM user_interactions")
    user_ids = cursor.fetchall()

    successful_sends = 0
    failed_sends = 0

    for (user_id,) in user_ids:
        try:
            if media:
                await client.send_file(user_id, media, caption=message)
            else:
                await client.send_message(user_id, message)
            successful_sends += 1
        except Exception as e:
            print(f"Failed to send message to user {user_id}: {e}")
            failed_sends += 1

    broadcast_result = (
        f"Broadcast Complete:\n"
        f"Total users: {len(user_ids)}\n"
        f"Successful sends: {successful_sends}\n"
        f"Failed sends: {failed_sends}"
    )
    try:
        await client.send_message(ADMIN_ID, broadcast_result)
    except Exception as e:
        print(f"Error sending broadcast results to admin: {e}")

# ✅ Start the Telegram client
async def main():
    print("Starting bot...")
    await client.start()
    await get_admin_entity()
    asyncio.create_task(send_daily_update())
    print("Bot is running!")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())