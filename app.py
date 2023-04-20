# pyrogram set
import os
import time
import random
from io import BytesIO
import traceback
import logging
import threading
import modules.db as db
import modules.tools as tools
import modules.setup as setup
from modules.img import Img
from pyrogram import Client, filters, enums, types
from pyrogram.errors import FloodWait,UserIsBlocked,InputUserDeactivated,UserDeactivated,UserDeactivatedBan,MessageDeleteForbidden
from dotenv import load_dotenv
import multiprocessing

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
                        
limit_text ="""
⚠️ عذرًا عزيزي .. 

[ توجد هناك طلبات كثيرة ] 🤖 

‏يرجى إرسال طلبك من جديد بعد 30 ثانية .
"""


@bot.on_message(filters.private & filters.command(['start', 'help', 'set','follow','refferal_messages','button', 'designs', 'fonts', 'broadcast', 'text',
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
                follow_text=data['text']['follow']
                follow_sure_text=data['text']['follow_sure']
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
                    follow_text=follow_text,
                    follow_sure_text=follow_sure_text,

                )
            elif message.text == '/set':
                text = bot_language['query']['set']
                db.set_user_state(chat_id, 'set', 60*4)
            elif message.text == '/sub':
                text = bot_language['query']['sub']
                db.set_user_state(chat_id, 'sub', 60*4)

            elif message.text == '/follow':
                text = bot_language['query']['follow']
                db.set_user_state(chat_id, 'follow', 60*4)
            elif message.text == '/button':
                text = bot_language['query']['refferal_button']
                markup = types.ReplyKeyboardMarkup([
                    [types.KeyboardButton('start')],
                    [types.KeyboardButton('done')],
                ])
                markup.resize_keyboard = True
                db.set_user_state(chat_id, 'refferal_button_link', 60*4)

            elif message.text == '/refferal_messages':
                if data['refferal_messages']:
                    text = 'تتوفر رسائل للتصاميم الاتية\n'
                    for item in data['refferal_messages']:
                        for button_data in data['routes']['designs_page']['buttons'][:-2]:
                            if button_data['id'] == item:
                                text = text + '\n التصميم : ' + button_data['title'] 
                    client.send_message(
                    chat_id=chat_id,
                    text=text,
                    )
                text = bot_language['query']['refferal_messages']
                db.set_user_state(chat_id, 'refferal_messages', 60*4)

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

        if data['follow'] and from_owner == False:
            status = f'{chat_id}:status'
            user_status = db.get_user_state(chat_id,status)
            if user_status == None :
                db.set_user_state(
                    chat_id, 'follow_sure', 40,status)
                text = data['text']['follow']
                url_button = types.InlineKeyboardButton('متابعة ⚠️', url=data['follow'])
                markup = types.InlineKeyboardMarkup([[url_button]])
                return client.send_message(chat_id, text, reply_markup=markup)
            
            elif user_status == 'follow_sure':
                text = data['text']['follow_sure']
                db.set_user_state(
                    chat_id, 'followed', (60*60) * 24,status)
                url_button = types.InlineKeyboardButton('متابعة ⚠️', url=data['follow'])
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
        status = f'{chat_id}:status'
        user_status = db.get_user_state(chat_id,status)
        # print(user_state)
        if user_state:
            if user_state == 'user_rate_limit':
                remaining_seconds = db.get_expire_time_in_seconds(chat_id)
                text = f"""
⚠️ عذرًا عزيزي .. 

[ توجد هناك طلبات كثيرة ] 🤖 

‏يرجى إرسال طلبك من جديد بعد {remaining_seconds} ثانية .
"""
                return client.send_message(chat_id, text)
            
            if 'apply' in user_state  or 'requested_text' in user_state:
                return client.send_message(chat_id, '⚠️ عذرًا عزيزي ..  \n [ عليك الانتظار قبل ارسال  طلب اخر ] 🤖\n\n اعد المحاولة لاحقاً')
            
        from_owner = tools.msg_from_owner(message, data['owner']['id'])
        if data['follow']:
            if user_status == None and from_owner == False:
                db.set_user_state(
                        chat_id, 'follow_sure', 40,status)
                text = data['text']['follow']
                url_button = types.InlineKeyboardButton('متابعة ⚠️', url=data['follow'])
                markup = types.InlineKeyboardMarkup([[url_button]])
                return client.send_message(chat_id, text, reply_markup=markup)
        
        if data['follow'] and from_owner == False:
            if user_status == 'follow_sure' or user_status == 'follow':
                client.delete_messages(chat_id, message_id)
                text = data['text']['follow_sure']
                db.set_user_state(
                    chat_id, 'followed', (60*60) * 24,status)
                url_button = types.InlineKeyboardButton(
                    'متابعة ⚠️', url=data['follow'])
                markup = types.InlineKeyboardMarkup([[url_button]])
                return client.send_message(chat_id, text, reply_markup=markup)
   
        if user_state == None or data['follow'] and user_status and 'followed' in user_status :
            if message.text and len(message.text) <= 30 :
                if from_owner == False:
                    new_user = db.add_user_id(chat_id)   
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

                    if len(threading.enumerate()) <= 30:
                        pass
                    else:
                        client.send_message(
                            chat_id, limit_text)
                        db.redis_store.delete('wait')
                        db.delete_user_state(channel_id)
                        return
                    # requests_count = db.get_set_items_count('wait')
                    # if requests_count <= 10:
                    #     pass
                    # else:
                    #     client.send_message(
                    #         chat_id, limit_text)
                    #     db.redis_store.delete('wait')
                    #     return

                requested_text = message.text
                
                if tools.show_option_markup(
                    client, chat_id,'design', data):
                    db.set_user_state(
                        chat_id, f'requested_text::{requested_text}', 30)
                return

            elif  message.text and len(message.text) > 30 :
                client.send_message(chat_id, data['text']['error'])
                return 
        # ? owner only functionality
        if from_owner:
            global placeholder
            if user_state:
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
                elif user_state == 'follow':
                    if tools.enable_follow_me(client, message,  data):
                        setup.save_data(data, DATA_PATH)
                    db.delete_user_state(chat_id)
                    return
                elif user_state == 'refferal_messages':
                    placeholder = tools.enable_refferal_messages(client, message,  data)
                    if placeholder == True:
                        setup.save_data(data, DATA_PATH)
                        db.delete_user_state(chat_id)
                        return
                    if placeholder:
                        db.set_user_state(chat_id, 'refferal_messages_place', 60*3)
                    return
                elif user_state == 'refferal_messages_place':
                    if tools.enable_refferal_messages(client, message,  data,message_info=placeholder):
                        setup.save_data(data, DATA_PATH)
                    db.delete_user_state(chat_id)
                    return
                
                #? refferal button
                elif user_state == 'refferal_button_link':
                    placeholder = tools.enable_refferal_button(client, message,data)
                    if placeholder:
                        db.set_user_state(chat_id, 'refferal_button_title', 60*3)
                    return
                elif user_state == 'refferal_button_title':
                    placeholder = tools.enable_refferal_button(client, message, data, button_data=placeholder)
                    if placeholder == True:
                        setup.save_data(data, DATA_PATH)
                        db.delete_user_state(chat_id)
                        return
                    if placeholder:
                        db.set_user_state(chat_id, 'refferal_button_add', 60*3)
                    return
                elif user_state == 'refferal_button_add':
                    if tools.enable_refferal_button(client, message, data, button_data=placeholder):
                        setup.save_data(data, DATA_PATH)
                    db.delete_user_state(chat_id)
                    placeholder = None
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
                elif '_title' in user_state:
                    target_type = user_state.split('_')[0]
                    bot.delete_messages(chat_id, placeholder[0].id)
                    placeholder = tools.set_new_target_title(
                        client, message,target_type, bot_language, placeholder[1], data)
                    if placeholder == True:
                        setup.save_data(data, DATA_PATH)
                        placeholder = None
                        db.delete_user_state(chat_id)
                    else:
                        db.set_user_state(chat_id, f'{target_type}_file', 60*3)
                    return
                elif '_file' in user_state:
                    target_type = user_state.split('_')[0]
                    bot.delete_messages(chat_id, placeholder[0].id)
                    if tools.set_target_file(client, message,target_type, placeholder[1], folders, data):
                        setup.save_data(data, DATA_PATH)
                    placeholder = None
                    db.delete_user_state(chat_id)
                    return
                
                elif 'set' in user_state:
                    target_id = placeholder[1]
                    target_type = user_state.split()[1]
                    target_setting = user_state.split()[-1]
                    bot.delete_messages(chat_id, placeholder[0].id) #deleting the ask message
                    if target_setting == 'location':
                        photo = tools.get_photo(client,message)
                        location = Img(photo).get_point_location('#ff00ff')
                        data['designs_settings'][target_id]['location'] = location
                        text = f'تم ضبط الاعداد {target_setting} بنجاح !!'
                        client.send_message(
                            chat_id=chat_id,
                            text=text
                        )
                        placeholder = None
                        db.delete_user_state(chat_id)
                        setup.save_data(data, DATA_PATH)
                        return 
                    else:
                        if tools.set_target_setting(
                            client, message,target_type,target_setting, target_id,bot_language, data):
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

                            # tools.show_option_markup(client,chat_id,'font',data)
                            # db.set_user_state(
                            #     chat_id, f'apply::{option_id}::{requested_text}', 30)
                            # return
                            # design_id = user_state.split('::')[1]
                            # font_id = option_id

                            # requests_count = db.get_set_items_count('wait')

                           
                            # logging.error(len(threading.enumerate()))
                            threading.Thread(target=tools.respond_to_user,args=(bot,call,requested_text,option_id,data)).start()
                            return client.answer_callback_query(call.id,'تم استقبال طلبك بنجاح',False)
                            
                        # if user_state.split('::')[0] == 'apply':
                        #     design_id = user_state.split('::')[1]
                        #     font_id = option_id
                        #     threading.Thread(target=tools.respond_to_user,args=(bot,call,requested_text,design_id,font_id,folders,data)).start()
                        #     return client.answer_callback_query(call.id,'تم استقبال طلبك بنجاح',False)
                            
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
                        
        if 'set' in call.data:
            #? handle target settings
            target_id = call.data.split()[1]
            target_type = call.data.split()[2]
            target_setting = call.data.split()[-1]
            query = f'{target_type}_{target_setting}'
            if target_setting == 'location':
                client.delete_messages(chat_id, call.message.id)
                file_path = None
                for design_data in data['routes']['designs_page']['buttons'][:-2]:
                    if design_data['id'] == target_id:
                        file_path = design_data['toggle']
                with open(file_path , 'rb') as f:
                    image = f.read()
                image_data = Img(image).to_greyscale()
                sent = bot.send_document(chat_id,BytesIO(image_data),caption=bot_language['query'][query],file_name='IMAGE.PNG')
                placeholder = [sent,target_id]
            else:
                placeholder = tools.ask_for_input(
                    client, call, bot_language['query'][query],target_id)
            
            db.set_user_state(chat_id, f'set {target_type} {target_setting}', 60*3)
            return         
        for route in data['routes']:
            if 'edit' in route:
                callback_data = call.data.split()[0]
            for button_data in data['routes'][route]['buttons']:
                if callback_data == button_data['id']:
                    if button_data['nav'] != None:
                        tools.handle_nav_call(client, call, button_data, data)
                    if button_data['toggle']:

                        if 'add_new_' in button_data['toggle']:
                            target_type = button_data['toggle'].split('_')[-1]
                            placeholder = tools.ask_for_input(
                                client, call, bot_language['query'][f'{target_type}_title'])
                            
                            db.set_user_state(chat_id, f'{target_type}_title', 60*3)
                            return
                        elif 'change_' in  button_data['toggle']:
                            toggle_words = button_data['toggle'].split('_')
                            target_type = toggle_words[1]
                            target_option = toggle_words[2] 
                            target_id = callback_data = call.data.split()[1]
                            
                            placeholder = tools.ask_for_input(
                                client, call, bot_language['query'][f'{target_type}_{target_option}'], target_id)
                            
                            db.set_user_state(chat_id, f'{target_type}_{target_option}', 60*3)
                            return

                        elif 'delete_all_' in button_data['toggle'] :
                            toggle_words = button_data['toggle'].split('_')
                            target_type = toggle_words[2] #* designs or fonts
                            if tools.handle_delete_all_call(client, call, target_type ,folders, data):
                                return setup.save_data(data, DATA_PATH)
                            
                        elif '_settings' in button_data['toggle'] :
                            toggle_words = button_data['toggle'].split('_')
                            target_type = toggle_words[0] #* designs or fonts
                            if tools.show_target_settings(client, call, target_type , data):
                                return setup.save_data(data, DATA_PATH)

                        elif 'delete_' in button_data['toggle']:
                            toggle_words = button_data['toggle'].split('_')
                            target_type = toggle_words[1] #* design or font
                            if tools.handle_delete_target_call(client, call,target_type, data):
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
