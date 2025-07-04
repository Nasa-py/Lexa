import discord
from discord.ext import commands
import aiohttp
import asyncio
from yt_dlp import YoutubeDL
from discord import FFmpegPCMAudio
from keep_alive import keep_alive
import os
from dotenv import load_dotenv
from discord import Embed
from openai import OpenAI
from functools import partial

load_dotenv()  

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True


bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)


music_queue = []
is_playing = False
current_song = None
loop_enabled = False

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -bufsize 64k'
}

ytdl_format_options = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',

}


ytdl = YoutubeDL(ytdl_format_options)

volume_level = 0.5  # Default volume (50%)


banned_words = [
    "bsdk", "bc", "mc", "tmck", "fuck", "f****", "f**k", "***k", "bitch",
    "chutiya", "chutiyeee", "c h u t i y a", "c hhutiya","tits"
    "mother chudmother", "chud",   "darpok", "aternos", "https://discord.gg", "sybau","bhenchod","nigga","teri ma di phuddi ch lund" ,"teri ma di bund ch kalla lun" , "salla bund deni deya" , "madarchod" , "teri bhen di phuddi"
]

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print("-------------------------------------")

@bot.event
async def on_member_join(member):
    channel = bot.get_channel(1107255396801986570)
    await channel.send(f'{member.mention} Welcome to our server!')

    url = "https://jokeapi-v2.p.rapidapi.com/joke/Any?format=json"
    headers = {
        "x-rapidapi-key": os.getenv("RAPIDAPI_KEY"),
        "x-rapidapi-host": "jokeapi-v2.p.rapidapi.com"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                joke_data = await response.json()
                if joke_data.get("type") == "single":
                    joke = joke_data["joke"]
                elif joke_data.get("type") == "twopart":
                    joke = f"{joke_data['setup']}\n{joke_data['delivery']}"
                else:
                    joke = "Couldn't fetch a joke this time!"
                await channel.send(f"Here's a welcome joke:\n{joke}")
            else:
                await channel.send("Couldn't fetch a joke right now.")

@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(1107255396801986570)
    await channel.send(f'{member.mention} has left the server.')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    content = message.content.lower().replace(" ", "")
    if any(word.replace(" ", "") in content for word in banned_words):
        await message.delete()
        await message.channel.send(f"{message.author.mention} ❌ No profanity or banned words allowed!")
        return

    await bot.process_commands(message)

async def ensure_voice(ctx):
    try:
        if ctx.voice_client is None or not ctx.voice_client.is_connected():
            await ctx.author.voice.channel.connect(reconnect=True)
        elif ctx.voice_client.channel != ctx.author.voice.channel:
            await ctx.voice_client.move_to(ctx.author.voice.channel)
    except discord.ClientException:
        await ctx.send("⚠️ Voice connection is starting. Try again.")
    except discord.errors.ConnectionClosed as e:
        if e.code == 4006:
            await ctx.send("🔄 Reconnecting to voice due to session error...")
            await ctx.voice_client.disconnect(force=True)
            await ctx.author.voice.channel.connect()


@bot.command(aliases=["talk", "lexa"])
async def chat(ctx, *, message: str):
    async with ctx.typing():
        try:
            def get_response():
                return client.chat.completions.create(
                    model="deepseek/deepseek-r1-0528:free",
                    messages=[
                        {"role": "system", "content": "You are Lexa, a sweet, funny and emotional daughter created by Nasa who talks like a real person."},
                        {"role": "user", "content": message}
                    ],
                    extra_headers={
                        "HTTP-Referer": "https://yourdiscordbot.site/",
                        "X-Title": "Lexa Discord Bot"
                    }
                )

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, get_response)

            if response and response.choices:
                reply = response.choices[0].message.content.strip()
                await asyncio.sleep(min(len(reply) * 0.015, 3))  
                await ctx.send(reply)
            else:
                await ctx.send("❌ Lexa didn't get a reply from the model.")

        except Exception as e:
            await ctx.send(f"❌ Lexa's having trouble chatting right now:\n`{str(e)}`")



@bot.command(aliases=["jk"])
async def joke(ctx):
    url = "https://jokeapi-v2.p.rapidapi.com/joke/Any?format=json"
    headers = {
        "x-rapidapi-key": os.getenv("RAPIDAPI_KEY"),
        "x-rapidapi-host": "jokeapi-v2.p.rapidapi.com"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                joke_data = await response.json()
                if joke_data.get("type") == "single":
                    joke = joke_data["joke"]
                elif joke_data.get("type") == "twopart":
                    joke = f"{joke_data['setup']}\n{joke_data['delivery']}"
                else:
                    joke = "😅 Couldn't fetch a joke right now!"
            else:
                joke = "😢 Failed to get a joke. Try again later."

    await ctx.send(f"😂 **Here's a joke for you:**\n{joke}")


@bot.command(aliases=["h", "commands"])
async def help(ctx):
    embed = discord.Embed(
        title="🧠 Bot Command Guide",
        description="Hey love 😘 here’s everything I can do for you:",
        color=discord.Color.purple()
    )

    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else None)

    embed.add_field(name="🎵 Music Commands", value="""
`!play <name>` — Search & play music  
`!pause` — Pause music  
`!resume` — Resume music  
`!skip` — Skip current song  
`!stop` — Stop and clear queue  
`!queue` — Show current queue  
`!loop` — Toggle loop  
`!join` — Join your voice channel  
`!leave` — Leave the voice channel
""", inline=False)

    embed.add_field(name="🛡️ Auto Moderation", value="""
🛑 Deletes messages with bad words  
👋 Welcomes new users  
😢 Says goodbye to leavers
""", inline=False)

    embed.add_field(name="🎉 Fun Commands", value="""
`!hello` — Say hello  
`!goodbye` — Say goodbye  
`!joke` — Sends a random joke  
`!lexa <msg>` — Chat with Lexa 💖
""", inline=False)

    embed.add_field(name="🔧 Bot Stuff", value="`!link` — Bot invite link", inline=False)

    # 🔗 Add clickable Insta in a small field
    embed.add_field(name="⠀", value="🧠 Created by Nasa • Instagram: [_nasa_40](https://www.instagram.com/_nasa_40)", inline=False)

    # Footer with icon only (no text since we moved it)
    embed.set_footer(
        text="",
        icon_url=ctx.guild.icon.url if ctx.guild.icon else bot.user.avatar.url
    )

    await ctx.send(embed=embed)


@bot.command(aliases=["inv"])
async def link(ctx):
    await ctx.send("Here's My Invite Link: https://discord.com/api/oauth2/authorize?client_id=1383397568679248003&permissions=8&scope=bot")
    await ctx.send("Created by Nasa ")
    await ctx.send("Instagram:_Nasa_40")


@bot.command(aliases=["j"])
async def join(ctx):
    if ctx.author.voice:
        await ensure_voice(ctx)
    else:
        await ctx.send("❌ You are not connected to a voice channel.")

@bot.command(aliases=["p"])
async def play(ctx, *, search: str):
    global music_queue, is_playing

    if ctx.author.voice is None:
        await ctx.send("❌ You must be in a voice channel.")
        return

    await ensure_voice(ctx)

    msg = await ctx.send("🔍 Searching...")

    if not search.lower().startswith("ytsearch:") and not search.startswith("http"):
        search = f"ytsearch:{search}"

    try:
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(search, download=False))

        if 'entries' in data:
            data = data['entries'][0]

        formats = data.get("formats", [])
        audio_url = None
        for f in formats:
            if f.get("vcodec") == "none" and f.get("acodec") != "none":
                audio_url = f.get("url")
                break

        if not audio_url:
            audio_url = data.get("url")

        if not audio_url:
            await msg.edit(content="❌ Could not get audio stream.")
            return

        song = {
            'title': data['title'],
            'url': audio_url,
            'webpage_url': data['webpage_url']
        }

        music_queue.append(song)
        await msg.edit(content=f"✅ Queued: **{song['title']}**")

        if not is_playing:
            await play_next(ctx)

    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

async def play_next(ctx):
    global music_queue, is_playing, current_song, loop_enabled, volume_level

    if not music_queue and not loop_enabled:
        is_playing = False
        current_song = None
        await ctx.send("🛑 Queue finished.")
        return

    if not loop_enabled:
        current_song = music_queue.pop(0)

    is_playing = True

    # Create audio source and wrap it with volume control
    source = FFmpegPCMAudio(current_song['url'], **ffmpeg_options)
    source = discord.PCMVolumeTransformer(source, volume=volume_level)

    def after_playing(error):
        global is_playing
        if error:
            print(f"Voice error: {error}")
        fut = play_next(ctx)
        bot.loop.create_task(fut)

    if ctx.voice_client.is_playing():
        return

    ctx.voice_client.play(source, after=after_playing)
    await ctx.send(f"▶️ Now playing: **{current_song['title']}**")


@bot.command(aliases=["q"])
async def queue(ctx):
    if music_queue:
        queue_str = "\n".join([f"{i+1}. {song['title']}" for i, song in enumerate(music_queue)])
        await ctx.send(f"📃 **Queue:**\n{queue_str}")
    else:
        await ctx.send("🎶 The queue is empty.")

@bot.command(aliases=["s"])
async def skip(ctx):
    global loop_enabled
    loop_enabled = False
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭ Skipping...")
    else:
        await ctx.send("❌ Nothing is playing.")

@bot.command(aliases=["st"])
async def stop(ctx):
    global music_queue, is_playing, current_song
    music_queue.clear()
    is_playing = False
    current_song = None
    if ctx.voice_client:
        ctx.voice_client.stop()
    await ctx.send("🛑 Stopped and cleared the queue.")

@bot.command()
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸ Paused.")
    else:
        await ctx.send("❌ Nothing is playing.")

@bot.command()
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ Resumed.")
    else:
        await ctx.send("❌ Nothing is paused.")

@bot.command(aliases=["l"])
async def loop(ctx):
    global loop_enabled
    loop_enabled = not loop_enabled
    await ctx.send(f"🔁 Loop is now {'enabled' if loop_enabled else 'disabled'}.")

@bot.command(aliases=["v"])
async def volume(ctx, level: int):
    global volume_level

    if 0 <= level <= 100:
        volume_level = level / 100
        if ctx.voice_client and ctx.voice_client.source:
            ctx.voice_client.source.volume = volume_level
        await ctx.send(f"🔊 Volume set to **{level}%**")
    else:
        await ctx.send("❌ Please enter a value between 0 and 100.")


@bot.command()
async def hello(ctx):
    await ctx.send("Hello!")

@bot.command()
async def goodbye(ctx):
    await ctx.send("Goodbye!")

@bot.command(aliases=["lv"])
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Left the voice channel.")
    else:
        await ctx.send("❌ I'm not in a voice channel.")


@bot.event
async def on_error(event, *args, **kwargs):
    print(f"❌ Unhandled error in event {event}:")
    import traceback
    traceback.print_exc()

keep_alive()

bot.run(os.getenv("BOT_TOKEN"))