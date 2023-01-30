import discord
import asyncio
from API_KEYS import BOT_TOKEN, TEST_CHANEL_ID, CHAT_CHANEL_ID, API_KEY, EGICHCOOL_ID
import openai
from openmeteo_py import Options,OWmanager


class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        openai.api_key = API_KEY             
          

    async def setup_hook(self) -> None:
        # create the background task and run it in the background
        self.bg_task = self.loop.create_task(self.my_background_task())

    async def on_ready(self):
        print(f'Вечер в хату {self.user} (ID: {self.user.id})')

    async def get_weather(self, coords=(55.738543, 37.541263)):
        self.coords = coords
        options = Options(*self.coords, current_weather=True)
        mgr = OWmanager(options)
        meteo = mgr.get_data()
        print(meteo)
        return meteo['current_weather']

    async def my_background_task(self):
        await self.wait_until_ready()
        counter = 0
        channel = self.get_channel(TEST_CHANEL_ID)  # channel ID goes here
        weather_data = await self.get_weather()          
        embed = discord.Embed(title='Прогноз погоды', 
                              description=f"За бортом {weather_data['temperature']}, {self.weather_codes[weather_data['weathercode']]}",
                              color=0xFFFF00)     
        embed.set_thumbnail(url='https://lh5.googleusercontent.com/JuQZdHpH1JyBm3SBVyY7ePWyNwFOEn_JipegmgFALmKat441MI0qCbzFQdpiKvdcQiA=w2400')        
        weather_message = await channel.send('Приветик', embed=embed)
        while not self.is_closed():
            await asyncio.sleep(5)  # task runs every 60 seconds
            counter += 1
            #await channel.send(counter)
            await weather_message.edit(embed=embed, content='')


            '''
            weather = await self.get_weather()   
            await self.change_presence(activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"прогноз погоды",  
                assets={'large_image_url':'sunny',
                        'large_text':'sunny',
                        'large_image_url':'sunny',
                        'large_text':'sunny'},
                details = f"За бортом {weather['temperature']}, {self.weather_codes[weather['weathercode']]}",                
                state='in development',

                ))
            print('fail')
            '''        
            
    async def on_message(self, message):
        if message.author == client.user:
            return        
                
        if message.channel.id == TEST_CHANEL_ID or message.channel.id == CHAT_CHANEL_ID:

            if message.content.startswith('id'):    
                await message.channel.send(message.channel.id)
        
            else:                
                '''
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
                '''
                print(message.content)


intents=discord.Intents.default()
intents.message_content = True
client = MyClient(intents=intents)
client.run(BOT_TOKEN)