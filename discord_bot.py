import discord
from discord.ext import commands
import asyncio
from API_KEYS import BOT_TOKEN, TEST_CHANEL_ID, CHAT_CHANEL_ID, API_KEY, EGICHCOOL_ID
import openai
from openmeteo_py import Options,OWmanager
import json
#import requests


#class MyClient(discord.Client):
class MyClient(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        openai.api_key = API_KEY        
        with open('data/weather_code.json', 'r') as json_file:
            self.weather_codes = json.load(json_file)
          

    async def setup_hook(self) -> None:
        # Создать таск на фоне
        self.bg_task = self.loop.create_task(self.my_background_task())

    async def on_ready(self):
        print(f'Вечер в хату {self.user} (ID: {self.user.id})')

    async def get_weather(self, coords=(55.738543, 37.541263)):
        self.coords = coords
        options = Options(*self.coords, current_weather=True)
        mgr = OWmanager(options)
        meteo = mgr.get_data()
        return meteo['current_weather']

    async def get_embed_weather(self, coords=(55.738543, 37.541263)):
        weather_data = await self.get_weather(coords)    

        embed = discord.Embed(title='Прогноз погоды', 
                        description=f"""За бортом {weather_data['temperature']}° 
                        {self.weather_codes[str(weather_data['weathercode'])]['name']}""",
                        color=int(self.weather_codes[str(weather_data['weathercode'])]['color'], 16))
        
        if weather_data['time'][11:13] in ('07', '08', '09', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19'):
            embed.set_thumbnail(url=f"{self.weather_codes[str(weather_data['weathercode'])]['image_day']}")
        else:
            embed.set_thumbnail(url=f"{self.weather_codes[str(weather_data['weathercode'])]['image_night']}")
        
        return embed
    
    '''
    @tree.command(name='Погода по адресу')
    async def weather_to_specific_coords(self, address):
        url = f'https://nominatim.openstreetmap.org/search/{address}?format=json'
        response = requests.get(url).json()
        if response == []:
            #await 
            return False
        
        embed = self.get_embed_weather(response[0]["lat"], response[0]["lon"])
    '''


    async def my_background_task(self):
        await self.wait_until_ready()
        counter = 0
        channel = self.get_channel(TEST_CHANEL_ID)  # ID канала для отправки погоды   

        embed = await self.get_embed_weather()    # Тут получать данные месаги
        
        weather_message = await channel.send(embed=embed)

        while not self.is_closed():
            await asyncio.sleep(60)  # Каждые N секунд перезапускать таск
            counter += 1
            #await channel.send(counter)
            embed = await self.get_embed_weather()
            await weather_message.edit(embed=embed)
    


intents=discord.Intents.default()
intents.message_content = True
bot = MyClient(intents=intents, command_prefix=commands.when_mentioned_or("!"))
#tree = app_commands.CommandTree(bot)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return        
            
    if message.channel.id == TEST_CHANEL_ID or message.channel.id == CHAT_CHANEL_ID:

        if message.content.startswith('id'):    
            await message.channel.send(message.channel.id)
    
        else:                
            '''
            response = openai.Completion.create(
            model="text-davinci-003",
            prompt=message.content,
            temperature=0.7,
            max_tokens=1000,
            top_p=1.0,
            frequency_penalty=0.5,
            presence_penalty=0.0,
            )     
            await message.channel.send(response['choices'][0]['text'])
            '''
            print(message.content)

@bot.command(name = "commandname", description = "My first application Command", guild=discord.Object(id=958615114595045376))
async def first_command(interaction):
    await interaction.response.send_message("Hello!")




bot.run(BOT_TOKEN)