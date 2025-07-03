import discord
from discord.ext import commands
import requests
import asyncio

discord.opus.load_opus('libopus.so')

intents = discord.Intents.all()

API_KEY =  "Put your api key here."
voice_id = "Put your ElevenLabs voice id here." 

last_speaker = None #stores last speaker to avoid "user says:" repetition.
send_msg = None

client = commands.Bot(command_prefix='`', intents=intents)

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    client.loop.create_task((queue_handler()))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('`hey'):
        await message.channel.send('Hello!')
    # safeguard for commands
    await client.process_commands(message)
#joining vc
@client.command()
async def join(ctx):
  if ctx.author.voice:
      channel = ctx.author.voice.channel
      await channel.connect()
  else:
      await ctx.send("okay, but you're not in a vc.")

#leaving vc
@client.command()
async def leave(ctx):
  if ctx.author.voice:
    if ctx.voice_client:
        global last_speaker
        await ctx.guild.voice_client.disconnect()
        await ctx.send("left")
        last_speaker = None
    else:
        await ctx.send("i'm not in a vc.")

  else:
    await ctx.send("you're not in a vc.")

#tts functionalities.
tts_queue = asyncio.Queue() #stores the tts requests.

async def queue_handler(): #gets the tts requests from the queue.
    while True:
        ctx, text = await tts_queue.get()
        await playBack(ctx, text) #feches data for api request.
        tts_queue.task_done()

@client.command()
async def say(ctx, *, text: str):
    
    if ctx.author.voice:
        await tts_queue.put((ctx, text))
        
    else:
        await ctx.send("how about you join a vc first?")


async def playBack(ctx, text):
    
    if ctx.author.voice:
        global last_speaker
        global send_msg
        get_name = ctx.author.display_name

        #checks who was the last speaker
        if get_name == last_speaker:
            send_msg = f"{text}"
            print(last_speaker)
            print(send_msg)
        else:
            send_msg = f"{get_name} said: {text}"
            last_speaker = get_name

        # Set up the request by chatgpt
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": API_KEY
        }

        data = {
            "text": send_msg,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.8
            }
        }

        # Make the request
        response = requests.post(url, headers=headers, json=data)

        # Save the audio
        with open("message.mp3", "wb") as f:
            f.write(response.content)

        print("🎧 Saved message.mp3")

        if ctx.author.voice and ctx.author.voice.channel:
            channel = ctx.author.voice.channel

            # Check if bot is already connected to a voice channel
            if ctx.voice_client:
                # If connected to a different channel, move to the author's channel
                if ctx.voice_client.channel != channel:
                    await ctx.voice_client.move_to(channel)
                vc = ctx.voice_client
            else:
                # Connect to the voice channel
                vc = await channel.connect()

            vc.play(discord.FFmpegPCMAudio('message.mp3'))
            
            while vc.is_playing():
                await asyncio.sleep(0.5)
    else:
        await ctx.send("join a vc, buddy.")

client.run("Put your bot token here.")
