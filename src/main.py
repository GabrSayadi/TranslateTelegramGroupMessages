import json
import pytz
import configparser
import requests
import mysql.connector
import datetime
import asyncio
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.messages import (GetHistoryRequest)
from telethon.tl.types import (
    PeerChannel
)

# Reading Configs
config = configparser.ConfigParser()
config.read("config.ini")

# Setting configuration values
api_id = config['Telegram']['api_id']
api_hash = config['Telegram']['api_hash']

api_hash = str(api_hash)

phone = config['Telegram']['phone']
username = config['Telegram']['username']

# Database Connection
conn = mysql.connector.connect(
    host=config['Telegram']['host'],
    user=config['Telegram']['user'],
    password=config['Telegram']['password'],
    database=config['Telegram']['database']
)
cursor = conn.cursor()

# Data insert time
now = datetime.datetime.now()

# Search data from database
def select_data(sql):
    data_list = []
    try:
        cursor.execute(sql)
        data_list = cursor.fetchall()
    except Exception as e:
        print(f'Error executing SQL query: {e}')
        conn.rollback()
    return data_list

# Count of data
def count_of_data(sql):
    cursor.execute(sql)
    count_of_table = cursor.fetchone()[0]
    return count_of_table

# Insert data to database
def insert_data(sql, message_list):
    for i in message_list:
        try:
            data = (0, i, now)
            cursor.execute(sql, data)
        except Exception as e:
            print(f'Error executing SQL query: {e}')
    conn.commit()
    print('Inserted')

# Translate text function
def translate_text(text, target='ar'):
    api_key = config['Telegram']['api_key']
    url = f'https://translation.googleapis.com/language/translate/v2?key={api_key}'
    data = {
        'q': text,
        'target': target
    }
    response = requests.post(url, data=data)
    response_data = response.json()
    return response_data['data']['translations'][0]['translatedText']

client = TelegramClient(username, api_id, api_hash)

# Create client & get messages
async def main(phone):
    await client.start()
    print("Client Created")
    if await client.is_user_authorized() == False:
        await client.send_code_request(phone)
        try:
            await client.sign_in(phone, input('Enter the code: '))
        except SessionPasswordNeededError:
            await client.sign_in(password=input('Password: '))

    thirty_min_ago = datetime.datetime.now(pytz.utc) - datetime.timedelta(minutes=5)

    me = await client.get_me()

    # Telegram channel link:
    user_input_channel = "https://t.me/...."

    if user_input_channel.isdigit():
        entity = PeerChannel(int(user_input_channel))
    else:
        entity = user_input_channel

    my_channel = await client.get_entity(entity)

    offset_id = 0
    limit = 200
    all_messages = []

    while True:
        history = await client(GetHistoryRequest(
            peer=my_channel,
            offset_id=offset_id,
            offset_date=None,
            add_offset=0,
            limit=limit,
            max_id=0,
            min_id=0,
            hash=0
        ))
        if not history.messages:
            break
        messages = history.messages
        for message in messages:
            if message.date < thirty_min_ago:
                break
            all_messages.append(message.to_dict())
        offset_id = messages[len(messages) - 1].id
        if message.date < thirty_min_ago:
            break

# Count of data on en
    data_count = count_of_data("SELECT COUNT(*) FROM en;")
    new_data_count = data_count

    mes_len = len(all_messages)
    if mes_len != 0:
        messages_data = []
        for mes in all_messages:
            if 'message' in mes:
                messages_data.append(mes['message'])

        # Insert data to en
        en_inset_sql = "INSERT INTO en (id, message, insert_time) VALUES(%s, %s, %s);"
        insert_data(en_inset_sql, messages_data)

        # Search message from en & add it to  list
        en_select_sql = f"SELECT message FROM en WHERE id > {int(new_data_count)};"
        en_list = select_data(en_select_sql)

        # translate messages && add translated text to ar_data list
        ar_data = []
        for i in en_list:
            translated_text = translate_text(i)
            ar_data.append(translated_text)

        # Count of data on ar
        data_count_ar = count_of_data("SELECT COUNT(*) FROM ar;")
        new_data_count_ar = data_count_ar

        # Insert translated text to ar in database
        ar_insert_sql = "INSERT INTO ar (id, message, insert_time) VALUES(%s, %s, %s);"
        insert_data(ar_insert_sql, ar_data)

        # Search message from ar & add it to new list
        ar_new_sql = f"SELECT message FROM ar WHERE id > {int(new_data_count_ar)};"
        ar_data_list = select_data(ar_new_sql)

        # Eend all message to our group
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        for i in ar_data_list:
            data = {"chat_id": config['Telegram']['chat_id'], "text": i[0], 'parse_mode': 'HTML'}
            telegram_post_request = requests.post(config['Telegram']['url'], data=json.dumps(data), headers=headers)

with client:
    client.loop.run_until_complete(main(phone))

# Close database connection & cursor
cursor.close()
conn.close()