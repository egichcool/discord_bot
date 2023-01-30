import os
import dotenv

dotenv.load_dotenv('.env')

API_KEY = os.environ['API_KEY']
BOT_TOKEN = os.environ['BOT_TOKEN']
TEST_CHANEL_ID = int(os.environ['TEST_CHANEL_ID'])
CHAT_CHANEL_ID = int(os.environ['CHAT_CHANEL_ID'])
EGICHCOOL_ID = int(os.environ['EGICHCOOL_ID'])
BOT_ID = os.environ['BOT_ID']
MAIN_CHANEL_ID = os.environ['MAIN_CHANEL_ID']