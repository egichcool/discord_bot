import discord
from API_KEYS import BOT_TOKEN, TEST_CHANEL_ID, CHAT_CHANEL_ID, API_KEY
import openai
import asyncio

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
openai.api_key = API_KEY


async def setup_weather():
    print(0)
    bg_task = client.loop.create_task(update_weather())

async def update_weather():
    await client.wait_until_ready()    
    counter = 0
    while not client.is_closed():
        counter += 1
        client.activity.type = 'watching'
        client.activity.name = counter

        #await client.get_channel(TEST_CHANEL_ID).send('hello')
        await asyncio.sleep(5) 

@client.event
async def on_ready():
    print(f'Приветствую тебя, {client.user}')
    await setup_weather()

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    if message.channel.id == TEST_CHANEL_ID or message.channel.id == CHAT_CHANEL_ID:
        if message.content.startswith('id'):    
            await message.channel.send(message.channel.id)
    
        else:
            #print(message.content, type(message.content))
            
            response = openai.Completion.create(
            model="text-davinci-003",
            prompt=message.content,
            temperature=0.8,
            max_tokens=1000,
            top_p=1.0,
            frequency_penalty=0.5,
            presence_penalty=0.0,
            )            
            await message.channel.send(response['choices'][0]['text'])
        

client.run(BOT_TOKEN)