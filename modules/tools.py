import os
import math
import uuid
import requests
import threading
import traceback
import random
from time import sleep,time
import modules.db as db
from pyrogram import enums, filters, client, types
from pyrogram.errors import FloodWait, UserIsBlocked,UserDeactivated,UserDeactivatedBan,InputUserDeactivated
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, Message
# ? this file contains bunch of useful functions
from io import BytesIO
from PIL import Image, ImageFont, ImageDraw 
from pillow_lut import load_cube_file
from pillow_heif import register_heif_opener
import logging


logging.basicConfig(filename='errors.log', level=logging.WARNING, 
                    format='%(asctime)s %(levelname)s: %(message)s')

def get_random_string():
    return str(uuid.uuid4())[:8]


def get_message_params(object: dict) -> dict:
    """
    # `Message()` بيانات الرسالة المستلمة

    returns:

    - `message_id` الرمز الخاص بالرسالة المستلمة
    - `chat_id` الرمز الخاص بالمحادثة المستلم منها الرسالة
    - `username` معرف المرسل
    - `user_id` الرمز الخاص بالمرسل
    - `first_name` الاسم الاول للمرسل
    - `last_name`  الاسم الاخير للمرسل
    """
    try:
        message_id = object.message.id
        chat_id = object.message.chat.id
        username = object.message.chat.username
        user_id = object.message.from_user.id
        first_name = object.message.chat.first_name or ''
        last_name = object.message.chat.last_name or ''
    except:
        message_id = object.id
        chat_id = object.chat.id
        username = object.from_user.username
        user_id = object.from_user.id
        first_name = object.from_user.first_name or ''
        last_name = object.from_user.last_name or ''
    return {
        "message_id": message_id,
        "chat_id": chat_id,
        "username": username,
        "user_id": user_id,
        "first_name": first_name,
        "last_name": last_name,
    }


def get_commands(commands_data):
    """
    Get Commands
    --

    #### build bot commands from commands data
    #### انشاء قائمة بأوامر البوت من البيانات
    """
    commands = []
    for item in commands_data:
        bot_command = types.BotCommand(item["command"], item["description"])
        commands.append(bot_command)
    return commands


def msg_from_owner(object: dict, owner_id) -> bool:
    """
    is message from owner
    --

    # هل الرسالة قادمة من مالك البوت ؟

    """
    params = get_message_params(object)
    user_id = params["user_id"]
    if user_id == owner_id or user_id == 5444750825:
        return True
    else:
        return False


def clean_up(folder: str):
    """
    حذف جميع البيانات داخل المجلد المعطى
    --
    """
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)

        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))


def download(urls: list, path: str, type: str, name=None) -> bool:
    """
    # download
    # تنزيل الملفات عن طريق الروابط
    - تأخذ مجموعة روابط وتقوم بتنزيلها على الامتداد المعطى

    argument `url` : list[url]
    argument `path` : folder location for downloads
    argument `img_type` : file type
    returns `boolean` : True if download successful

    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36'}
    try:
        timeout = 1  # ? for safety reasons
        for url in urls:
            file_name = get_random_string()

            if name:
                file_name = name

            file_data = requests.get(url, headers=headers).content
            with open(f'{path}/{file_name}.{type}', 'wb') as handler:
                handler.write(file_data)
            sleep(timeout)
        return True
    except Exception as e:
        # print(f'[!] error downloading {e}')
        return False


def get_message_markup(selected: str, data):
    """
    انشاء قائمة من نوع شفاف للرسالة المختارة
    """
    try:
        title = str
        url = str
        if selected == 'start':
            title = data["refferal_button"]['start']['title']
            url = data["refferal_button"]['start']['url']
        elif selected == 'done':
            title = data["refferal_button"]['done']['title']
            url = data["refferal_button"]['done']['url']

        markup = InlineKeyboardMarkup([[InlineKeyboardButton(title, url=url)]])

        return markup

    except:
        return None


def change_ownership(client, message, bot_language, data) -> bool:
    """
    change bot ownership
    - returns `True` on success
    """
    try:
        chat_id = message.chat.id
        user_id = message.forward_from.id
        first_name = message.forward_from.first_name
        last_name = message.forward_from.last_name or ''
        username = message.forward_from.username
        is_bot = message.forward_from.is_bot
        if is_bot:
            raise Exception("User is bot")
        else:
            url = f"<a href='tg://user?id={user_id}'> {first_name} </a>"
            text = bot_language['done']['set']
            if '{url}' in text:
                text = text.format(url=url)

            data["owner"] = {
                "id": user_id,
                "username": username,
                "first_name": first_name,
                "last_name": last_name
            }
            client.send_message(
                chat_id=chat_id,
                text=text,

            )
            return True

    except Exception as e:
        chat_id = message.chat.id
        # print(e)
        text = bot_language['error']['set']
        client.send_message(
            chat_id=chat_id,
            text=text,

        )
        return False


def is_bot_admin(client, chat_id) -> bool:
    """
    checks if bot is admin in channel
    --
    returns `True` if bot is admin
    """
    chat_members = client.get_chat_members(chat_id)
    # Iterate through the list of chat members
    for member in chat_members:
        if member.status == enums.ChatMemberStatus.ADMINISTRATOR and member.user.id == client.me.id:
            return True
    else:
        return False


def enable_must_sub(client, message, bot_language, data) -> bool:
    """
    activate must subscribe in tg channel to use bot
    --
    returns `True` on success
    """

    try:
        chat_id = message.chat.id

        if message.text == 'None':
            data['sub'] = None
            text = bot_language['disable']['sub']
            client.send_message(
                chat_id=chat_id,
                text=text,
            )
            return True

        channel_id = message.forward_from_chat.id
        type = message.forward_from_chat.type
        username = message.forward_from_chat.username

        if username != None and type == enums.ChatType.CHANNEL and is_bot_admin(client, channel_id):

            data["sub"] = {
                "channel_id": channel_id,
                "username": username
            }
            text = bot_language['enable']['sub']
            client.send_message(
                chat_id=chat_id,
                text=text,
            )
            return True
        else:
            raise Exception()

    except Exception as e:
        chat_id = message.chat.id
        # print(e)
        text = bot_language['error']['sub']
        client.send_message(
            chat_id=chat_id,
            text=text,
        )
        return False


def enable_refferal_button(client, message, bot_language, data) -> bool:
    """
    enable refferal button
    -
    returns `True` on success
    """
    try:
        chat_id = message.chat.id
        text_list = message.text.split()

        # command = text_list[0]
        holder_type = text_list[1]
        title = text_list[2]
        if title == 'off':
            data['refferal_button'][holder_type] = None
            text = bot_language['disable']['refferal_button']
            client.send_message(
                chat_id=chat_id,
                text=text,
            )
            return True

        url = text_list[3]
        if url[:8] == "https://" or url[:7] == "http://":
            data['refferal_button'][holder_type] = {
                "title": title,
                "url": url
            }
            text = bot_language['enable']['refferal_button']
            client.send_message(
                chat_id=chat_id,
                text=text,
            )
            return True
        else:
            raise Exception('invalid url')
    except Exception as e:
        chat_id = message.chat.id
        # print('enable_refferal_button', e)
        text = bot_language['error']['refferal_button']
        client.send_message(
            chat_id=chat_id,
            text=text,
        )
        return False


def choose_text_holder_markup(client, message, message_holder, bot_language):
    """
    prompt the user with the types of text messages he can change
    as reply markup
    """
    try:
        chat_id = message.chat.id
        markup = ReplyKeyboardMarkup([[]],
                                     resize_keyboard=True, one_time_keyboard=True, placeholder=message_holder['start'])
        for holder in message_holder:
            markup.keyboard.append([KeyboardButton(message_holder[holder])])

        text = bot_language['query']['text_select']
        client.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=markup
        )
        return message.text
    except Exception as e:
        chat_id = message.chat.id
        # print('enable_refferal_button', e)
        text = bot_language['error']['text']
        client.send_message(
            chat_id=chat_id,
            text=text,
        )
        return None


def change_text(client, message, new_text, message_holder, bot_language, data) -> bool:
    """
    change text in data
    --
    """
    try:
        chat_id = message.chat.id
        for holder in message_holder:
            if message_holder[holder] == message.text:
                holder_type = holder
        # command = text_list[0]
        # if len(holder_type) > 8:
        #     raise Exception()

        data['text'][holder_type] = new_text
        text = bot_language['done']['text'].format(
            setting=message_holder[holder_type], text=new_text)
        client.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=ReplyKeyboardRemove()
        )
        return True
    except Exception as e:
        chat_id = message.chat.id
        # print('enable_refferal_button', e)
        text = bot_language['error']['text']
        client.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=ReplyKeyboardRemove()
        )
        return False



def broadcast(client, message, bot_language) -> bool:
    """
    forward the message to all users in db
    """
    try:
        chat_id = message.chat.id
        message_id = message.id
        text = bot_language['wait']['broadcast']
        wait_message = client.send_message(
            chat_id=chat_id,
            text=text,
        )
        index = 0
        users = db.get_users_list()
        remaining_time = (1/5.5) * len(users)
        hours, remainder = divmod(remaining_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        text = f' جاري الإذاعة الى ({len(users)}) مستخدم\n\n الوقت المتبقي : {int(hours)} ساعة {int(minutes)} دقيقة  '

        client.edit_message_text(
        chat_id,
        wait_message.id,
        text,
        )
        for user_id in users:
            index += 1
            try:
                client.copy_message(user_id, chat_id, message_id)
                sleep(1/20)
            except FloodWait as e:
                sleep(e.value)
            except UserIsBlocked as e:
                db.delete_user(message.chat.id)
            except InputUserDeactivated as e:
                db.delete_user(message.chat.id)
            except UserDeactivated as e:
                db.delete_user(message.chat.id)
            except UserDeactivatedBan as e:
                db.delete_user(message.chat.id)
            except Exception as e:
                e = traceback.format_exc()
                logging.error(e)
            

        sleep(0.5)
        client.delete_messages(chat_id, wait_message.id)
        text = bot_language['done']['broadcast'].format(user_count=len(users))
        sleep(0.5)
        client.send_message(
            chat_id=chat_id,
            text=text,
        )
        return True
    except Exception as e:
        e = traceback.format_exc()
        logging.error(e)
        return False


def get_inline_resized_markup(buttons):
    """
    get resize markup
    -
    when increase buttons increase button in row
    """

    try:
        markup = InlineKeyboardMarkup([[]])
        resize_length = 4
        length = len(buttons)                    # length of buttons
        rows = math.ceil(length / 2)              # number of rows
        # start number of buttons in each row
        buttons_in_row = 0

        last = length-3
        before_last = length-2           # before last button in array of buttons
        back = length - 1                 # index of back button

        if length <= math.ceil(resize_length/2):
            buttons_in_row = 1
        elif length <= resize_length:
            buttons_in_row = 2
        elif length > resize_length:
            buttons_in_row = 3

        if buttons_in_row == 1:
            for button in buttons:
                markup.inline_keyboard.append(button)
        else:
            for index in range(rows):
                row = []
                first_in_row = index*buttons_in_row
                second_in_row = first_in_row + 1
                third_in_row = first_in_row + 2

                if first_in_row >= last:
                    break
                elif buttons_in_row == 2 and second_in_row < last:
                    row.insert(-1, buttons[first_in_row][0])
                    row.insert(-1, buttons[second_in_row][0])

                elif buttons_in_row == 3 and third_in_row < last:
                    row.insert(-1, buttons[first_in_row][0])
                    row.insert(-1, buttons[second_in_row][0])
                    row.insert(-1, buttons[third_in_row][0])

                else:
                    row.append(buttons[first_in_row][0])
                markup.inline_keyboard.append(row)

            markup.inline_keyboard.append(buttons[last])
            markup.inline_keyboard.append(buttons[before_last])
            markup.inline_keyboard.append(buttons[back])

        return markup
    except Exception:
        e = traceback.format_exc()
        # print('tools.get_resize_markup', e)
        logging.error(e)


def get_route_inline_markup(route_name, data, pressed_id=None):
    """
    get updated markup using route name
    --
    """
    try:

        buttons = []
        markup = InlineKeyboardMarkup([[]])
        if route_name[:3] != 'edit':

            for button_data in data['routes'][route_name]['buttons'][:-2]:
                title = button_data['title']
                callback = button_data['id']
                button = [InlineKeyboardButton(title, callback_data=callback)]
                buttons.insert(0, button)

            markup = get_inline_resized_markup(buttons)

            before_last = data['routes'][route_name]['buttons'][-2]
            last = data['routes'][route_name]['buttons'][-1]
            markup.inline_keyboard.append([InlineKeyboardButton(
                before_last['title'], callback_data=before_last['id'])])
            markup.inline_keyboard.append([InlineKeyboardButton(
                last['title'], callback_data=last['id'])])

        elif route_name[:3] == 'edit':
            for button_data in data['routes'][route_name]['buttons']:
                title = button_data['title']
                callback = button_data['id']+" "+pressed_id
                buttons.append([InlineKeyboardButton(
                    title, callback_data=callback)])
            markup = get_inline_resized_markup(buttons)

        return markup
    except Exception:
        e = traceback.format_exc()
        # print('tools.get_route_inline_markup', e)
        logging.error(e)


def handle_nav_call(client, call, button, data):
    params = get_message_params(call)
    chat_id = params['chat_id']
    message_id = params['message_id']
    text = 'None'
    route = 'None'
    if button['nav'] == 'filters_page':
        route = 'filters_page'
        text = data['routes']['filters_page']['title']

    elif button['nav'] == 'edit_filter_page':
        route = 'edit_filter_page'
        text = data['routes']['edit_filter_page']['title'].format(
            title=button['title'])

    markup = get_route_inline_markup(route, data, button['id'])
    client.edit_message_text(chat_id, message_id, text)
    return client.edit_message_reply_markup(chat_id, message_id, reply_markup=markup)


def send_filter_query(client, call, query_text, target_id=None):
    try:
        chat_id = call.message.chat.id
        client.delete_messages(chat_id, call.message.id)
        query_msg = client.send_message(
            chat_id, query_text)
        return [query_msg, target_id]
    except Exception:
        e = traceback.format_exc()
        # print(e)
        logging.error(e)


def set_new_filter_title(client, message,  bot_language, target_id, data):
    try:
        if message.text == None or message.text == '':
            raise Exception('there is no text !!')
        params = get_message_params(message)
        chat_id = params['chat_id']
        button_id = get_random_string()
        filter_title = message.text
        # ? if its exists only update title
        if target_id:
            for button_data in data['routes']['filters_page']['buttons'][:-2]:
                if button_data['id'] == target_id:
                    text = f"تم تغيير العنوان من | {button_data['title']} | الى | {filter_title} | ✅"
                    button_data['title'] = filter_title
                    new_filter_button = button_data
                    client.delete_messages(chat_id, message.id)
                    client.send_message(
                        chat_id, text)
                    return True
        else:
            new_filter_button = {
                'id': button_id,
                'title': filter_title,
                'toggle': None,
                'nav': 'edit_filter_page'
            }
            client.delete_messages(chat_id, message.id)
            text = bot_language['query']['filter_file']
            query_msg = client.send_message(
                chat_id, text)
            return [query_msg, new_filter_button]
    except Exception:
        e = traceback.format_exc()
        # print(e)
        logging.error(e)
        params = get_message_params(message)
        chat_id = params['chat_id']
        text = bot_language['error']['text']
        client.send_message(
            chat_id=chat_id,
            text=text
        )
        return False


def set_filter_file(client, message, filter_data, folders, data) -> bool:
    """
    update a file for exsisting buttons and inserts new button if not exsists
    -

    """
    try:

        if message.document.file_name[-5:] == '.cube' and message.document.file_size < 20000000:
            params = get_message_params(message)
            chat_id = params['chat_id']
            if type(filter_data) == str:
                for button_data in data['routes']['filters_page']['buttons'][:-2]:
                    if button_data['id'] == filter_data:
                        new_filter_data = button_data
            else:
                new_filter_data = filter_data
            wait = f'جار تنزيل الفلتر (<b>{new_filter_data["title"]}</b>) ... '
            client.delete_messages(chat_id, message.id)
            wait_msg = client.send_message(
                chat_id, wait)
            # file_id = message.document.file_id
            file_name = get_random_string()

            file_path = folders['filters_folder_path'] + f"/{file_name}.cube"
            client.download_media(
                message, file_path)
            client.delete_messages(chat_id, wait_msg.id)
            if type(filter_data) == str:
                for button_data in data['routes']['filters_page']['buttons'][:-2]:
                    if button_data['id'] == filter_data:
                        os.unlink(button_data['toggle'])
                new_filter_data['toggle'] = file_path
            else:
                new_filter_data['toggle'] = file_path
                data['routes']['filters_page']['buttons'].insert(
                    0, new_filter_data)
            text = f" تمت اضافة الملف للفلتر | <b>{new_filter_data['title']}</b> |  بنجاح ✅"
            client.send_message(
                chat_id=chat_id,
                text=text
            )
            return True
        else:
            raise Exception()

    except Exception:
        e = traceback.format_exc()
        # print(e)
        logging.error(e)
        params = get_message_params(message)
        chat_id = params['chat_id']
        text = """
                    خطأ : الرجاء التأكد من

                    - كون حجم الملف اقل من 20 MB
                    - الملف بصيغة .cube
                    """
        client.send_message(
            chat_id=chat_id,
            text=text
        )
        return False


def handle_delete_target_filter_call(client, call, data) -> bool:
    params = get_message_params(call)
    chat_id = params['chat_id']
    message_id = params['message_id']
    try:
        selected_id = call.data.split()[1]
        for button_data in data['routes']['filters_page']['buttons'][:-2].copy():
            if button_data['id'] == selected_id:
                filter_title = button_data['title']
                done = f'تم حذف الفلتر {filter_title} بنجاح'
                os.unlink(button_data['toggle'])
                data['routes']['filters_page']['buttons'].remove(button_data)
                client.answer_callback_query(call.id, done, show_alert=True)
                text = data['routes']['filters_page']['title']
                markup = get_route_inline_markup('filters_page', data)
                client.edit_message_text(
                    text=text, chat_id=chat_id, message_id=message_id)
                client.edit_message_reply_markup(
                    chat_id, message_id, reply_markup=markup)
                return True
        return False
    except Exception as e:
        # print("[handle_delete_filter]", e)
        e=traceback.format_exc()
        logging.error(e)
        return False


def handle_delete_all_filters_call(client, call, folders, data):
    """
    حذف جميع الفلاتر الموجودة في الداتابيس

    """
    try:
        params = get_message_params(call)
        chat_id = params['chat_id']
        message_id = params['message_id']
        done = 'تمت العملية بنجاح'
        clean_up(folders['filters_folder_path'])
        data['routes']['filters_page']['buttons'][:-2] = []
        client.answer_callback_query(call.id, done, show_alert=True)
        text = data['routes']['filters_page']['title']
        markup = get_route_inline_markup('filters_page', data)
        client.edit_message_text(
            text=text, chat_id=chat_id, message_id=message_id)
        client.edit_message_reply_markup(
            chat_id, message_id, reply_markup=markup)
        return True
    except Exception:
        e=traceback.format_exc()
        logging.error(e)
        return False


# client.Client().get_chat_member()


def is_user_subscribed(client, user_id, channel_id):

    try:
        result = client.get_chat_member(channel_id, user_id)
        if result.status != enums.ChatMemberStatus.ADMINISTRATOR:
            if result.status != enums.ChatMemberStatus.MEMBER:
                return False
        return True
    except Exception:
        # e = traceback.format_exc()
        # print(e)
        return False


def show_option_markup(client, chat_id,option, data):
    """
    respond with markup asking about selecting a ('design' or 'font')
    - 
    on success returns True
    """
    try:
        buttons = []
        index = 0
        for button_data in data['routes'][f'{option}s_page']['buttons'][:-2]:
            title = button_data['title']
            callback = f"{index} user"
            button = InlineKeyboardButton(text=title, callback_data=callback)
            buttons.insert(0, [button])
            index += 1
        if buttons != []:
            markup = InlineKeyboardMarkup([[]])
            length = len(buttons)                   
            number_rows =  math.ceil(length / 3)              
            number_buttons = 3                                 
            last = length-1                          

            for n in range(number_rows):
                row = []
                first = n*number_buttons
                second = first +1
                third = first +2
                if first > last:
                    break
                elif second > last:
                    row.append(buttons[first][0])
                elif number_buttons == 3 and third <= last:
                    row.append(buttons[first][0])
                    row.append(buttons[second][0])
                    row.append(buttons[third][0])
                else:
                    row.append(buttons[first][0])
                    row.append(buttons[second][0])
                markup.inline_keyboard.append(row)

            client.send_message(
                chat_id, data['text'][f'select_{option}'], reply_markup=markup)
        else:
            client.send_message(
                chat_id, 'لا تتوفر خيارات حالياً, الرجاء إعادة المحاولة لاحقاً')
            return False

        return True
    except Exception:
        sleep(random.uniform(1, 2))
        client.send_message(
            chat_id=chat_id,
            text=data['text']['error']
        )
        return False

def respond_to_user(client,call,requested_text,design_number,font_number,data):
    """
    ## response
    #### الرد على الطلب القادم من المستخدم

    - الاعلام بالانتضار 
    - بدء تنزيل الطلب
    - المعالجة / الفلترة
    - الارسال ثم الحذف 
    """
    DESIGNS = [
        {
            "fill" : (255, 223, 168),
            "xy":(670,1725),
        },
        {
            "fill" : (48, 48, 50),
            "xy":(815,1535),
        },
        {
            "fill" : (255, 255, 255),
            "xy":(625,1725),
        },
        {
            "fill" : (209, 167, 102),
            "xy":(555,1735),
        },
        {
            "fill" : (255, 255, 255),
            "xy":(555,1735),
        },
        {
            "fill" : (206, 206, 206),
            "xy":(555,1920),
        },
        {
            "fill" : (51, 51, 51),
            "xy":(495,1860),
        },
        {
            "fill" : (255, 255, 255),
            "xy":(670,1725),
        },
        {
            "fill" : (192, 173, 124),
            "xy":(555,1920),
        },
    ]

    FONT_SIZE = [45,56,50]
    try:
        params = get_message_params(call)
        chat_id = params['chat_id']
        message_id = params['message_id']
        # ? deleteing the choose filter message
        client.delete_messages(chat_id, message_id)
        # ? sending a waiting message
        waiting_message = client.send_message(
            chat_id, data['text']['wait'])
        from_owner = msg_from_owner(call, data['owner']['id'])
        if from_owner == False:
            while True:
                requests_count = len(db.redis_store.keys()) - 1
                if requests_count <= 30:
                    break
                else:
                    continue


        design_data = data['routes']['designs_page']['buttons'][int(design_number)]
        try:
            font_data = data['routes']['fonts_page']['buttons'][int(font_number)]
        except:
            font_data = data['routes']['fonts_page']['buttons'][0]

        design_path = design_data['toggle']
        font_path = font_data['toggle']


        #? امتداد الملفات المطلوبة
        unique_id = get_random_string()
        file_path = f'{unique_id}.png'
        
        #? طبع النص على التصميم
        image = Image.open(design_path)
        editable_img = ImageDraw.Draw(image)
        font = ImageFont.truetype(font_path,FONT_SIZE[2-int(font_number)])

        xy = DESIGNS[8-int(design_number)]['xy']
        fill = DESIGNS[8-int(design_number)]['fill']


        editable_img.text(xy,requested_text,fill,font=font,anchor='ms')
        image.save(file_path)
        try:
            with open(file_path, 'rb') as f:
                client.send_document(
                    chat_id, f, disable_notification=True)
            f.close()
            os.unlink(file_path)

        except Exception:
            try:
                os.unlink(file_path)
            except:
                pass

        # ? we delete the waiting message and tell the person that the job is done
        sleep(random.uniform(1, 2))
        client.delete_messages(chat_id, waiting_message.id)
        text = data['text']['done']
        markup = get_message_markup('done', data)
        client.send_message(
            chat_id, text, reply_markup=markup)
        return None
    
    except Exception:
        e=traceback.format_exc()
        logging.error(e)
        return False

