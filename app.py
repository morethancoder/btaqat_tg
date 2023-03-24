# pyrogram set
import os
import time
import random
import traceback
import logging
import threading
import modules.db as db
import modules.tools as tools
import modules.setup as setup
from pyrogram import Client, filters, enums, types
from pyrogram.errors import FloodWait,UserIsBlocked,InputUserDeactivated,UserDeactivated,UserDeactivatedBan,MessageDeleteForbidden
from dotenv import load_dotenv


logging.basicConfig(filename="pyrogramErrors.log", level=logging.WARNING,
                    format="%(asctime)s:%(levelname)s:%(message)s")

placeholder = None
# ? init enviroment variables
load_dotenv()
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
DATA_PATH = os.getenv('DATA_PATH')

# ? init setup
data = setup.load_data(DATA_PATH)
bot_language = setup.CONFIG_TEMPLATE['bot_language']
message_holder = setup.CONFIG_TEMPLATE['message_holder']
folders = setup.CONFIG_TEMPLATE['folders']
bot = Client('btaqat_tg', api_id=API_ID,
             api_hash=API_HASH, bot_token=BOT_TOKEN)

bot.set_parse_mode(enums.ParseMode.HTML)
# commands = tools.get_commands(setup.CONFIG_TEMPLATE['commands_data'])
# bot.set_bot_commands(commands)


@bot.on_message(filters.private & filters.command(['start', 'help', 'set', 'designs', 'fonts', 'broadcast', 'text',
                                                   'sub', 'dev', 'statistics', 'settings']))
def send_text(client, message):
    try:
        params = tools.get_message_params(message)
        user_id = params["user_id"]
        chat_id = params["chat_id"]
        first_name = params["first_name"]
        user_url = f"<a href='tg://user?id={user_id}'> {first_name} </a>"
        from_owner = tools.msg_from_owner(message, data['owner']['id'])
        markup = None
        text = None
        if message.text == '/start':
            text = data['text']['start']
            markup = tools.get_message_markup('start', data)
            
        elif message.text == '/dev':
            text = bot_language['on_command']['dev']
        elif from_owner:
            # on_owner_command
            if message.text == '/help':
                text = bot_language['on_command']['owner_help']
                markup = types.ReplyKeyboardRemove()
            elif message.text == '/settings':
                text = bot_language['on_command']['settings']
            elif message.text == '/statistics':
                user_count = db.get_users_count()
                must_sub = bot_language['enable']['sub'] if data['sub'] else bot_language['disable']['sub']
                start_text = data['text']['start']
                select_design_text = data['text']['select_design']
                select_font_text = data['text']['select_font']
                done_text = data['text']['done']
                error_text = data['text']['error']
                wait_text = data['text']['wait']
                sub_text = data['text']['sub']
                if '{channel_username}' in sub_text:
                    sub_text = sub_text.format(
                    channel_username='channel_username')

                text = bot_language['on_command']['statistics'].format(
                    user_count=user_count,
                    must_sub=must_sub,
                    start_text=start_text,
                    select_design_text=select_design_text,
                    select_font_text=select_font_text,
                    done_text=done_text,
                    error_text=error_text,
                    wait_text=wait_text,
                    sub_text=sub_text,

                )
            elif message.text == '/set':
                text = bot_language['query']['set']
                db.set_user_state(chat_id, 'set', 60*4)
            elif message.text == '/sub':
                text = bot_language['query']['sub']
                db.set_user_state(chat_id, 'sub', 60*4)
            elif message.text == '/broadcast':
                text = bot_language['query']['broadcast']
                db.set_user_state(chat_id, 'broadcast', 60*4)
            elif message.text == '/text':
                text = bot_language['query']['text']
                db.set_user_state(chat_id, 'text', 60*4)
            elif message.text == '/designs':
                text = data['routes']['designs_page']['title']
                markup = tools.get_route_inline_markup('designs_page', data)
            elif message.text == '/fonts':
                text = data['routes']['fonts_page']['title']
                markup = tools.get_route_inline_markup('fonts_page', data)

        else:
            # user_only_command
            if message.text == '/help':
                text = bot_language['on_command']['user_help']
                markup = types.ReplyKeyboardRemove()

        # ? text formating
        if text:
            if '{url}' in text:
                text = text.format(url=user_url)

        if from_owner:
            pass
        else:
            # ? adding user_id to db
            db.add_user_id(user_id)
            # ? sending the text
            if data["sub"]:
                channel_id = data["sub"]["channel_id"]
                channel_username = data["sub"]["username"]
                channel_url = f'https://t.me/{channel_username}'
                if tools.is_user_subscribed(client, chat_id, channel_id) == False:
                    text = data['text']['sub'].format(
                        channel_username=channel_username)
                    url_button = types.InlineKeyboardButton(
                        'إشتراك ⚠️', url=channel_url)
                    markup = types.InlineKeyboardMarkup([[url_button]])
                    return client.send_message(chat_id, text, reply_markup=markup)
                
        # ? sending the text
        client.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=markup,
        )


        return
    except MessageDeleteForbidden as e:
        pass
    except UserIsBlocked as e:
        db.delete_user(message.chat.id)
    except InputUserDeactivated as e:
        db.delete_user(message.chat.id)
    except UserDeactivated as e:
        db.delete_user(message.chat.id)
    except UserDeactivatedBan as e:
        db.delete_user(message.chat.id)
    except Exception as e:
        e=traceback.format_exc()
        logging.error(e)
        return

@bot.on_message(filters.private & filters.command(['button']))
def on_command_prompt(client, message):
    "what happend after command with prompt"
    try:
        if message.text.split()[0] == '/button':
            if tools.enable_refferal_button(client, message, bot_language, data):
                return setup.save_data(data, DATA_PATH)
    except Exception:
        e=traceback.format_exc()
        logging.error(e)
        return



@bot.on_message(filters.private)
def after_new_message(client, message):
    """
    get user state and follow up from there
    --
    """
    try:
        params = tools.get_message_params(message)
        chat_id = params['chat_id']
        message_id = params['message_id']
        user_state = db.get_user_state(chat_id)
        from_owner = tools.msg_from_owner(message, data['owner']['id'])
        if user_state and from_owner == False:
            client.send_message(chat_id, 'عذرا, عليك اكمال طلبك السابق قبل ارسال اخر')
            return 
        if user_state == None:
            if message.text and len(message.text) <= 15 :
                if from_owner == False:
                    db.add_user_id(chat_id)
                    if data["sub"]:
                        channel_id = data["sub"]["channel_id"]
                        channel_username = data["sub"]["username"]
                        channel_url = f'https://t.me/{channel_username}'
                        if tools.is_user_subscribed(client, chat_id, channel_id) == False:
                            client.delete_messages(chat_id, message_id)
                            text = data['text']['sub'].format(
                                channel_username=channel_username)
                            url_button = types.InlineKeyboardButton(
                                'إشتراك ⚠️', url=channel_url)
                            markup = types.InlineKeyboardMarkup([[url_button]])
                            return client.send_message(chat_id, text, reply_markup=markup)
                        
                    
                    requests_count = len(db.redis_store.keys()) - 1
                    if requests_count <= 30:
                        pass
                    else:
                        waiting_message = client.send_message(
                        chat_id, data['text']['wait'])
                        time.sleep(10)
                        client.delete_messages(chat_id,waiting_message.id)
                        return

                requested_text = message.text
                
                tools.show_option_markup(
                    client, chat_id,'design', data)
                
                db.set_user_state(
                    chat_id, f'requested_text::{requested_text}', 40)
                return

            elif  message.text and len(message.text) > 30 :
                client.send_message(chat_id, data['text']['error'])
                return 
        # ? owner only functionality
        if from_owner:
            global placeholder
            if user_state == 'set':
                if tools.change_ownership(client, message, bot_language, data):
                    setup.save_data(data, DATA_PATH)
                db.delete_user_state(chat_id)
                return
            elif user_state == 'sub':
                if tools.enable_must_sub(client, message, bot_language, data):
                    setup.save_data(data, DATA_PATH)
                db.delete_user_state(chat_id)
                return
            elif user_state == 'broadcast':
                thread = threading.Thread(
                    target=tools.broadcast, args=(client, message, bot_language))
                # Set the thread as a daemon thread
                thread.setDaemon(True)
                thread.start()  # start
                db.delete_user_state(chat_id)
                return
            elif user_state == 'text':
                placeholder = tools.choose_text_holder_markup(
                    client, message, message_holder, bot_language)
                if placeholder != None:
                    db.set_user_state(chat_id, 'text_select', 60*3)
                return
            elif user_state == 'text_select':
                if tools.change_text(client, message, placeholder, message_holder, bot_language, data):
                    setup.save_data(data, DATA_PATH)
                db.delete_user_state(chat_id)
                placeholder = None
                return
            elif user_state == 'filter_title':
                bot.delete_messages(chat_id, placeholder[0].id)
                placeholder = tools.set_new_filter_title(
                    client, message, bot_language, placeholder[1], data)
                if placeholder == True:
                    setup.save_data(data, DATA_PATH)
                    placeholder = None
                    db.delete_user_state(chat_id)
                else:
                    db.set_user_state(chat_id, 'filter_file', 60*3)
                return
            elif user_state == 'filter_file':
                bot.delete_messages(chat_id, placeholder[0].id)
                if tools.set_filter_file(client, message, placeholder[1], folders, data):
                    setup.save_data(data, DATA_PATH)
                placeholder = None
                db.delete_user_state(chat_id)
                return
    except MessageDeleteForbidden as e:
        pass
    except UserIsBlocked as e:
        db.delete_user(message.chat.id)
    except InputUserDeactivated as e:
        db.delete_user(message.chat.id)
    except UserDeactivated as e:
        db.delete_user(message.chat.id)
    except UserDeactivatedBan as e:
        db.delete_user(message.chat.id)
    except Exception as e:
        e=traceback.format_exc()
        logging.error(e)
        return

@bot.on_callback_query()
def on_call(client, call):

    try:
        global placeholder
        params = tools.get_message_params(call)
        chat_id = params['chat_id']
        message_id = params['message_id']
        callback_data = call.data
        if len(callback_data.split()) > 1:
            if callback_data.split()[1] == 'user': 
                    user_state = db.get_user_state(chat_id)
                    option_id = callback_data.split()[0]
                    if user_state:
                        requested_text = user_state.split('::')[-1]
                        if user_state.split('::')[0] == 'requested_text':
                            client.delete_messages(chat_id, message_id)
                            tools.show_option_markup(client,chat_id,'font',data)
                            db.set_user_state(
                                chat_id, f'apply::{option_id}::{requested_text}', 30)
                            return
                        if user_state.split('::')[0] == 'apply':
                            design_id = user_state.split('::')[1]
                            font_id = option_id
                            threading.Thread(target=tools.respond_to_user,args=(client,call,requested_text,design_id,font_id,data)).start()
                            db.delete_user_state(chat_id)
                            return
                            
                    else:
                        try:
                            client.delete_messages(call.message.chat.id, call.message.id)
                            client.send_message(call.message.chat.id,'حاول مرة اخرى ')
                            # client.answer_callback_query(call.id, bot_language['error']['on_call'],show_alert=True)
                            return
                        except FloodWait as e:
                            return time.sleep(e.value)
                        except UserIsBlocked as e:
                            db.delete_user(call.message.chat.id)
                        except InputUserDeactivated as e:
                            db.delete_user(call.message.chat.id)
                        except UserDeactivated as e:
                            db.delete_user(call.message.chat.id)
                        except UserDeactivatedBan as e:
                            db.delete_user(call.message.chat.id)
                        except Exception as e:
                            e=traceback.format_exc()
                            logging.error(e)
                            return
                        
        for route in data['routes']:
            if route == 'edit_filter_page':
                callback_data = call.data.split()[0]
            for button_data in data['routes'][route]['buttons']:
                if callback_data == button_data['id']:
                    if button_data['nav'] != None:
                        tools.handle_nav_call(client, call, button_data, data)
                    if button_data['toggle'] == 'add_new_filter':
                        placeholder = tools.send_filter_query(
                            client, call, bot_language['query']['filter_title'])
                        db.set_user_state(chat_id, 'filter_title', 60*3)
                        return
                    elif button_data['toggle'] == 'change_filter_title':
                        target_id = callback_data = call.data.split()[1]
                        placeholder = tools.send_filter_query(
                            client, call, bot_language['query']['filter_title'], target_id)
                        db.set_user_state(chat_id, 'filter_title', 60*3)
                        return

                    elif button_data['toggle'] == 'change_filter_file':
                        target_id = callback_data = call.data.split()[1]
                        placeholder = tools.send_filter_query(
                            client, call, bot_language['query']['filter_file'], target_id)
                        db.set_user_state(chat_id, 'filter_file', 60*3)
                        return

                    elif button_data['toggle'] == 'delete_filter':
                        if tools.handle_delete_target_filter_call(client, call, data):
                            return setup.save_data(data, DATA_PATH)

                    elif button_data['toggle'] == 'delete_all_filters':
                        if tools.handle_delete_all_filters_call(client, call, folders, data):
                            return setup.save_data(data, DATA_PATH)
    except MessageDeleteForbidden as e:
        pass
    except UserIsBlocked as e:
        db.delete_user(call.message.chat.id)
    except InputUserDeactivated as e:
        db.delete_user(call.message.chat.id)
    except UserDeactivated as e:
        db.delete_user(call.message.chat.id)
    except UserDeactivatedBan as e:
        db.delete_user(call.message.chat.id)
    except Exception as e:
        e=traceback.format_exc()
        logging.error(e)
        return

bot.run()
