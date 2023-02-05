import discord
from discord.ext import commands
import asyncio
from API_KEYS import BOT_TOKEN, TEST_CHANEL_ID, CHAT_CHANEL_ID, API_KEY, LAT, LON, WEATHER_CHANNEL_ID, GPT_CHANNEL_ID, SISTER_CHANNEL_ID
import openai
from openmeteo_py import Options,OWmanager
import json
import requests
import tiktoken

ENCODER = tiktoken.get_encoding("gpt2")

def get_max_tokens(prompt: str) -> int:
    """
    Get the max tokens for a prompt
    """
    return 4000 - len(ENCODER.encode(prompt))

#This part of code was taken from github.com/acheong08/ChatGPT
class Chatbot:
    def __init__(self, api_key: str, buffer: int = None) -> None:
        """
        Initialize Chatbot with API key (from https://platform.openai.com/account/api-keys)
        """
        openai.api_key = API_KEY
        self.conversations = Conversation()
        self.prompt = Prompt(buffer=buffer)
        self.ENGINE = "text-chat-davinci-002-20221122"

    def _get_completion(
        self,
        prompt: str,
        temperature: float = 0.5,
        stream: bool = False,
    ):
        """
        Get the completion function
        """
        return openai.Completion.create(
            engine=self.ENGINE,
            prompt=prompt,
            temperature=temperature,
            max_tokens=get_max_tokens(prompt),
            stop=["\n\n\n"],
            stream=stream,
        )

    def _process_completion(
        self, user_request: str, completion: dict, conversation_id: str = None, user: str = "User"
    ) -> dict:
        '''
        if completion.get("choices") is None:
            raise Exception("ChatGPT API returned no choices")
        if len(completion["choices"]) == 0:
            raise Exception("ChatGPT API returned no choices")
        if completion["choices"][0].get("text") is None:
            raise Exception("ChatGPT API returned no text")
        completion["choices"][0]["text"] = completion["choices"][0]["text"].rstrip(
            "<|im_end|>",
        )
        '''
        if completion.get("choices") is None:
            return "ChatGPT API returned no choices"
        if len(completion["choices"]) == 0:
            return "ChatGPT API returned no choices"
        if completion["choices"][0].get("text") is None:
            return 'ChatGPT API returned no text'            
        completion["choices"][0]["text"] = completion["choices"][0]["text"].rstrip(
            "<|im_end|>",
        )
        # Add to chat history
        self.prompt.add_to_history(user_request, completion["choices"][0]["text"], user=user)
        if conversation_id is not None:
            self.save_conversation(conversation_id)
        return completion

    def _process_completion_stream(
        self, user_request: str, completion: dict, conversation_id: str = None, user: str = "User"
    ) -> str:
        full_response = ""
        for response in completion:
            try:
                if response.get("choices") is None:
                    return "ChatGPT API returned no choices"
                if len(response["choices"]) == 0:
                    return "ChatGPT API returned no choices"
                if response["choices"][0].get("finish_details") is not None:
                    break
                if response["choices"][0].get("text") is None:
                    return "ChatGPT API returned no text"
                if response["choices"][0]["text"] == "<|im_end|>":
                    break
                yield response["choices"][0]["text"]
                full_response += response["choices"][0]["text"]
            except:
                yield ''

        # Add to chat history
        self.prompt.add_to_history(user_request, full_response, user)
        if conversation_id is not None:
            self.save_conversation(conversation_id)

    def ask(
        self, user_request: str, temperature: float = 0.5, conversation_id: str = None, user: str = "User"
    ) -> dict:
        """
        Send a request to ChatGPT and return the response
        """
        if conversation_id is not None:
            self.load_conversation(conversation_id)
        completion = self._get_completion(
            self.prompt.construct_prompt(user_request, user=user),
            temperature,
        )
        return self._process_completion(user_request, completion, user=user)

    def ask_stream(
        self, user_request: str, temperature: float = 0.5, conversation_id: str = None, user: str = "User"
    ) -> str:
        """
        Send a request to ChatGPT and yield the response
        """
        if conversation_id is not None:
            self.load_conversation(conversation_id)
        prompt = self.prompt.construct_prompt(user_request, user=user)
        return self._process_completion_stream(
            user_request=user_request,
            completion=self._get_completion(prompt, temperature, stream=True),
            user=user,
        )

    def make_conversation(self, conversation_id: str) -> None:
        """
        Make a conversation
        """
        self.conversations.add_conversation(conversation_id, [])

    def rollback(self, num: int) -> None:
        """
        Rollback chat history num times
        """
        for _ in range(num):
            self.prompt.chat_history.pop()

    def reset(self) -> None:
        """
        Reset chat history
        """
        self.prompt.chat_history = []

    def load_conversation(self, conversation_id) -> None:
        """
        Load a conversation from the conversation history
        """
        if conversation_id not in self.conversations.conversations:
            # Create a new conversation
            self.make_conversation(conversation_id)
        self.prompt.chat_history = self.conversations.get_conversation(conversation_id)

    def save_conversation(self, conversation_id) -> None:
        """
        Save a conversation to the conversation history
        """
        self.conversations.add_conversation(conversation_id, self.prompt.chat_history)


class Conversation:
    """
    For handling multiple conversations
    """

    def __init__(self) -> None:
        self.conversations = {}

    def add_conversation(self, key: str, history: list) -> None:
        """
        Adds a history list to the conversations dict with the id as the key
        """
        self.conversations[key] = history

    def get_conversation(self, key: str) -> list:
        """
        Retrieves the history list from the conversations dict with the id as the key
        """
        return self.conversations[key]

    def remove_conversation(self, key: str) -> None:
        """
        Removes the history list from the conversations dict with the id as the key
        """
        del self.conversations[key]

    def __str__(self) -> str:
        """
        Creates a JSON string of the conversations
        """
        return json.dumps(self.conversations)

    def save(self, file: str) -> None:
        """
        Saves the conversations to a JSON file
        """
        with open(file, "w", encoding="utf-8") as f:
            f.write(str(self))

    def load(self, file: str) -> None:
        """
        Loads the conversations from a JSON file
        """
        with open(file, encoding="utf-8") as f:
            self.conversations = json.loads(f.read())


class Prompt:
    """
    Prompt class with methods to construct prompt
    """

    def __init__(self, buffer: int = None) -> None:
        """
        Initialize prompt with base prompt
        """
        self.base_prompt = ("ChatGPT: Hello! How can I help you today?")
        # Track chat history
        self.chat_history: list = []
        self.buffer = buffer

    def add_to_chat_history(self, chat: str) -> None:
        """
        Add chat to chat history for next prompt
        """
        self.chat_history.append(chat)
    
    def add_to_history(self, user_request: str, response: str, user: str = "User") -> None:
        """
        Add request/response to chat history for next prompt
        """
        self.add_to_chat_history(
            user+": "
            + user_request
            + "\n\n\n"
            + "ChatGPT: "
            + response
            + "<|im_end|>\n"
        )

    def history(self, custom_history: list = None) -> str:
        """
        Return chat history
        """
        return "\n".join(custom_history or self.chat_history)

    def construct_prompt(self, new_prompt: str, custom_history: list = None, user: str = "User") -> str:
        """
        Construct prompt based on chat history and request
        """
        prompt = (
            self.base_prompt
            + self.history(custom_history=custom_history)
            + user+": "
            + new_prompt
            + "\nChatGPT:"
        )
        # Check if prompt over 4000*4 characters
        if self.buffer is not None:
            max_tokens = 4000 - self.buffer
        else:
            max_tokens = 3200
        if len(ENCODER.encode(prompt)) > max_tokens:
            # Remove oldest chat
            self.chat_history.pop(0)
            # Construct prompt again
            prompt = self.construct_prompt(new_prompt, custom_history, user)
        return prompt




class MyClient(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        openai.api_key = API_KEY        
        with open('data/weather_code.json', 'r') as json_file:
            self.weather_codes = json.load(json_file)
        self.bg_task = self.loop.create_task(self.my_background_task())
        self.stream = True

    async def on_ready(self):
        await self.change_presence(activity=discord.Activity(
            type=discord.ActivityType.watching, name="за погодой"))
        print(f'Вечер в хату {self.user} (ID: {self.user.id})')        

    async def get_weather(self, coords=(LAT, LON)):
        self.coords = coords
        options = Options(*self.coords, current_weather=True)
        mgr = OWmanager(options)
        meteo = mgr.get_data()
        return meteo['current_weather']

    async def get_embed_weather(self, coords=(LAT, LON), location='Москва'):
        weather_data = await self.get_weather(coords)    

        embed = discord.Embed(title=f'Прогноз погоды', 
                        description=f"""За бортом {weather_data['temperature']}° 
                        {self.weather_codes[str(weather_data['weathercode'])]['name']}
                        {location}""",
                        color=int(self.weather_codes[str(weather_data['weathercode'])]['color'], 16))
        
        if weather_data['time'][11:13] in ('07', '08', '09', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19'):
            embed.set_thumbnail(url=f"{self.weather_codes[str(weather_data['weathercode'])]['image_day']}")
        else:
            embed.set_thumbnail(url=f"{self.weather_codes[str(weather_data['weathercode'])]['image_night']}")

        return embed


    async def my_background_task(self):
        await self.wait_until_ready()          
        channel = self.get_channel(WEATHER_CHANNEL_ID)  # ID канала для отправки погоды  
        embed = await self.get_embed_weather()    # Тут получать данные месаги
        weather_message = await channel.send(embed=embed)
        while not self.is_closed():
            await asyncio.sleep(60)  # Каждые N секунд перезапускать таск
            embed = await self.get_embed_weather()
            await weather_message.edit(embed=embed)
    


intents=discord.Intents.default()
intents.message_content = True
bot = MyClient(intents=intents)
chatbot_for_us = Chatbot(api_key=API_KEY)
chatbot_for_sister = Chatbot(api_key=API_KEY)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return        
    
    if message.channel.id == CHAT_CHANEL_ID:
        if message.content.startswith('id'):    
            await message.channel.send(message.channel.id)
        else:          
            response = openai.Completion.create(
            model="text-davinci-003",
            prompt=message.content,
            temperature=0.7,
            max_tokens=3000,
            top_p=1.0,
            frequency_penalty=0.5,
            presence_penalty=0.0,
            )     
            text = response['choices'][0]['text']
            while text != '':
                await message.channel.send(text[:1800])
                text = text[1800:]


    if message.channel.id in (GPT_CHANNEL_ID, SISTER_CHANNEL_ID, TEST_CHANEL_ID):
        if message.channel.id == GPT_CHANNEL_ID or message.channel.id == TEST_CHANEL_ID:
            chatbot = chatbot_for_us
        if message.channel.id == SISTER_CHANNEL_ID:
            chatbot = chatbot_for_sister
        temperature = 0.5
        prompt = message.content

        if message.content.startswith('!'):    
            if message.content.startswith('!help'):    
                await message.channel.send('''
                            !help - Display this message
                !rollback - Rollback chat history
                !reset - Reset chat history
                !prompt - Show current prompt
                !temperature - Set temperature
                !stream (True/False)
                ''')
            elif message.content.startswith("!temperature"):
                try:
                    temperature = float(message.content[13:])
                    if temperature < 0 or temperature > 1:
                        raise ValueError
                    await message.channel.send(f'temperature is now {temperature}')
                except ValueError:
                    temperature = 0.5
                    await message.channel.send(f'temperature is now {temperature}')
            elif message.content.startswith("!rollback"):
                chatbot.rollback(1)
                await message.channel.send('Rolled back by 1 message')
            elif message.content.startswith("!reset"):
                chatbot.reset()
                await message.channel.send('History reseted')
            elif message.content.startswith("!prompt"):
                await message.channel.send(chatbot.prompt.construct_prompt(""))
            elif message.content.startswith("!stream"):
                stream = message.content[8:]
                if stream == 'True' or "False":
                    bot.stream = bool(stream)
                    await message.channel.send(f'Stream is now set to {bot.stream}')
                else:
                    await message.channel.send('Incorrect input')
        else:
            if bot.stream:
                #Word by word return
                text = None
                temp_words_count = 0
                all_words_count = 0
                for response in chatbot.ask_stream(prompt, temperature=temperature):
                    if text == None:
                        if response == '' or response == ' ' or response == '\n':
                            continue
                        text = response
                        bot_message = await message.channel.send(response)
                    else:
                        all_words_count += 1
                        temp_words_count += 1
                        text += response
                        if temp_words_count == 10:
                            temp_words_count = 0
                            await bot_message.edit(text)
                    if all_words_count > 1800:
                        text = None
                bot_message = None
                text = None
            else:
                #Full answer return
                response = chatbot.ask(prompt, temperature=temperature)
                text = response['choices'][0]['text']
                while text != '':
                    await message.channel.send(text[:1800])
                    text = text[1800:]
                        

@bot.slash_command(name='погода_по_адресу', guild_ids=['958615114595045376'])
#@bot.slash_command(name='погода_по_адресу', guild_ids=[...])
#@bot.slash_command(name='погода_по_адресу')
async def weather_to_specific_coords(ctx, message):
    url = f'https://nominatim.openstreetmap.org/search/{message}?format=json'
    print(url)
    print(message)
    response = requests.get(url).json()
    if response == []:
        await ctx.respond('Введён некорректный адрес')
    else:
        print(response[0]["lat"], response[0]["lon"], message)
        embed = await bot.get_embed_weather(coords=(float(response[0]["lat"]), float(response[0]["lon"])), location=message)
        await ctx.respond(embed=embed)


bot.run(BOT_TOKEN)