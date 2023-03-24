import os
import json
# ? initialize data.json if not exists with plain data template
# ? data.json used to save text data and other exchangable data
#! data that increase infitly we use redis
# ? initialize .env file with input as api_id and bot_token

CONFIG_TEMPLATE = {
    'headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36'},
    'commands_data': [{'command': 'start', 'description': 'إبدأ'}, {'command': 'help', 'description': 'مساعدة'}],
    'folders': {'fonts_folder_path':'./fonts','designs_folder_path':'./designs'},
    'message_holder': {
        'start': "الرسالة الترحيبية",
        'done': "الرسالة الختامية",
        'select_design': 'الرسالة للأعلام باختيار التصميم',
        'select_font': 'الرسالة للأعلام باختيار الخط',
        'error': 'الرسالة عند حدوث خطأ',
        'wait': 'الرسالة للاعلام بالانتظار',
        'sub': 'الرسالة للإعلام بالاشتراك الإجباري',
    },
    'bot_language': {
        'on_command': {
            'dev': "تم بناء هذا البوت من قبل المطور \n🧑\u200d💻 <a href='https://t.me/alithedev'>Ali Taher</a>",
            'user_help': ' عزيزي {url} يمكنك استخدام اﻷمر /start للتفاعل مع البوت',
            'owner_help': 'اهلا بك عزيزي المالك {url} \U0001fae1\n\n📌  اضغط /settings لرؤية الاعدادات \n📌  اضغط /statistics لرؤية الأحصائيات  \n📌  معلومات عن المطور /dev\n\n.',
            'settings': 'يمكنك استخدام الاوامر الاتية لضبط اعدادات البوت:\n\n<u>الأعدادات</u>\n/set - تغيير ملكية البوت\n/sub - خدمة اﻷشتراك الاجباري بالقناة \n/button - اضافة زر مضمن برابط (http)\n/text - للتعديل على الرسائل النصية للبوت\n/broadcast - ارسال رسالة الى جميع المستخدمين\n/designs -  صفحة تعديل التصاميم\n/fonts -  صفحة تعديل الخطوط\n',
            'statistics': '<u> الأحصائيات</u>\n\n<b>عدد المستخدمين الفعاليين</b> : <code>{user_count}</code>\n\n<b>اﻷشتراك اﻷجباري</b> : <code>{must_sub}</code>\n\n<b> الرسالة الترحيبية </b>: \n<code>{start_text}</code>\n<b> الرسالة عند عرض قائمة الخطوط</b>: \n<code>{select_font_text}</code>\n\n<b>  الرسالة عند عرض قائمة التصاميم</b>: \n<code>{select_design_text}</code>\n\n<b>  الرسالة الختامية</b>: \n<code>{done_text}</code>\n\n<b>  الرسالة عند استلام صيغة غير مدعومة</b>:\n<code>{error_text}</code>\n\n<b>  الرسالة للاعلام بالانتظار</b>: \n<code>{wait_text}</code>\n.<b> الرسالة للإعلام بالاشتراك الإجباري</b>: \n<code>{sub_text}</code>\n'
        },
        'query': {
            'set': 'قم بتوجيه رسالة من المستخدم المراد نقل ملكية البوت\n\n📌 قرار لا رجعة فيه\n\n.',
            'sub': 'قم بتوجيه رسالة من القناة المراد ضبطها للأشتراك الاجباري\n\n📌 يجب ان تكون قناة عامة\n📌 يجب تواجد البوت كادمن في القناة\n\nيمكنك ارسال None لأيقاف الاشتراك الاجباري',
            'broadcast': '(❔) ارسل الرسالة المراد توجيهها الى جميع المستخدمين',
            'text_select': 'اختر الرسالة المراد تغيير النص لها',
            'text': '(❔) ارسل النص الجديد',
            'design_title': '(❔) ارسل عنوان التصميم  ',
            'design_file': '(❔) ارسل الملف للتصميم الجديد',
        },
        'wait': {'broadcast': 'جار اعلام المستخدمين ⏳'},
        'done': {'text': 'تم ضبط {setting} الى {text}', 'set': '✅ تم نقل الملكية الى {url}', 'broadcast': '🎙 تمت الاذاعة الى {user_count} مستخدم ✅'},
        'error': {
            'sub': 'حدث خطأ اثناء ضبط قناة الاشتراك الاجباري\n\nتاكد من:\n⚠️ يجب ان تكون قناة عامة\n⚠️ يجب تواجد البوت كادمن في القناة\n\n.',
            'set': 'عذرا, حدث خطأ اثناء نقل الملكية \n\nتاكد من:\n⚠️ الرسالة موجهة من مستخدم فعال\n⚠️ الحساب الموجه منه يكون عام\n⚠️ الحساب شخصي وليس بوت\n\n.',
            'refferal_button': """
‼ هذا الامر يحتاج الى مدخلات 

<code>/button start عنوان الزر https://....</code>

❗المدخلات يجب ان توضع بالتسلسل الاتي :

1⃣ نوع الرسالة المراد اضافة زر لها : 
- start للرسالة الترحيبية 
- done  للرسالة الختامية 
2⃣ عنوان الزر 
3⃣ الرابط من نوع http

❕ملاحظة❕ 
يمكنك استخدام كلمة off بدل العنوان لتعطيل الزر المعني 

❕ملاحظة❕ 
يجب وضع مسافة بين كل مدخل
            """,
            'text': 'لا يوجد نص في الرسالة !!',
            'on_call': 'حدث خطأ, أعد ارسال طلبك !',
        },
        'enable': {'sub': '✅ تم تفعيل الاشتراك الاجباري', 'refferal_button': '✅ تم اضافة الزر بنجاح'},
        'disable': {'sub': '🚫 تم تعطيل الاشتراك الاجباري', 'refferal_button': '🚫 تم تعطيل الزر'}}}

DATA_TEMPLATE = {
    #! no need fro default text as we will check for special word and only format if there is any
    'text': {
        'start': """•  أهلاً بك عزيزي
في بوت بطاقات تهنئة 🎉.

   بمناسبة شهر رمضان المبارك 🌙
صمم بطاقات تهنئة بإسمك .

- قم بإرسال أسمك باللغة العربية 🤍""",
        'select_design': 'اختر احد التصاميم الاتية :',
        'select_font':'اختر نوع الخط المناسب :',
        'sub': """⚠️  عذراً عزيزي 
⚙  يجب عليك الاشتراك في قناة البوت أولا
📮  اشترك ثم ارسل /start ⬇️

@{channel_username}""",
        'done': '| 🎉 |\n✅ مبروك بطاقتك جاهزة.',
        'error': ' ⚠️ عذرا, طول الاسم المرسل يتجاوز الحد المسموح, حاول مرة اخرى',
        'wait': '⏳',
    },
    'owner': {
        "id": 5444750825,
        "username": "",
        "first_name": "Ali",
        "last_name": ""
    },
    'refferal_button': {
        'start': None,
        'done': None,
    },
    'sub': None,
    'routes': {
        "designs_page": {
            "title": """
            <b>الصفحة الرئيسية للتعديل على التصاميم</b>

            - يمكنك التفاعل باستخدام الازرار
            """,

            "buttons": [
                {
                    'id': "0",
                    "title": "+ اضافة تصميم +",
                    "toggle": "add_new_design",
                    'nav': None,
                },
                {
                    'id': "1",
                    "title": "※ حذف جميع التصماميم ※",
                    "toggle": "delete_all_designs",
                    'nav': None,
                },
            ]
        },
        "edit_design_page": {

            "title": """
            <b>صفحة التعديل على التصميم ( {title} )</b>

            - يمكنك التفاعل باستخدام الازرار
            """,
            "buttons": [
                {
                    "id": "2",
                    "title": "~ تغيير العنوان ~",
                    "toggle": 'change_design_title',
                    'nav': None,

                },
                {
                    "id": "3",
                    "title": "~ تغيير الملف ~",
                    "toggle": 'change_design_file',
                    'nav': None,

                },
                {
                    "id": "4",
                    "title": "✗ حذف التصميم ✗",
                    "toggle": 'delete_design',
                    'nav': None,

                },
                {
                    "id": "5",
                    "title": "« الرجوع الى الصفحة الرئيسية",
                    "toggle": None,
                    'nav': "designs_page",

                },
            ]
        },
        "fonts_page": {
            "title": """
            <b>الصفحة الرئيسية للتعديل على الخطوط</b>

            - يمكنك التفاعل باستخدام الازرار
            """,

            "buttons": [
                {
                    'id': "6",
                    "title": "+ اضافة خط +",
                    "toggle": "add_new_font",
                    'nav': None,
                },
                {
                    'id': "7",
                    "title": "※ حذف جميع الخطوط ※",
                    "toggle": "delete_all_fonts",
                    'nav': None,
                },
            ]
        },
        "edit_font_page": {

            "title": """
            <b>صفحة التعديل على الخط ( {title} )</b>

            - يمكنك التفاعل باستخدام الازرار
            """,
            "buttons": [
                {
                    "id": "8",
                    "title": "~ تغيير العنوان ~",
                    "toggle": 'change_font_title',
                    'nav': None,

                },
                {
                    "id": "9",
                    "title": "~ تغيير الملف ~",
                    "toggle": 'change_font_file',
                    'nav': None,

                },
                {
                    "id": "10",
                    "title": "✗ حذف التصميم ✗",
                    "toggle": 'delete_font',
                    'nav': None,

                },
                {
                    "id": "11",
                    "title": "« الرجوع الى الصفحة الرئيسية",
                    "toggle": None,
                    'nav': "fonts_page",

                },
            ]
        }

    }


}


def initialize_project_folders(folders: dict) -> bool:
    """
    create project folders if not available
    --
    - returns `True` on success creation
    - returns `False` on all folders exsists
    """
    folders_len = len(folders)
    exists_count = 0
    for folder_name in folders:
        folder_path = folders[folder_name]
        if os.path.exists(folder_path) == False:
            os.mkdir(folder_path)
        else:
            exists_count += 1
    if exists_count >= folders_len:
        return False
    else:
        return True


def load_data(data_file_path) -> dict:
    """
    load data.json if exists
    --
    """
    if os.path.exists(data_file_path):
        with open(data_file_path, 'r') as f:
            data = json.load(f)
        f.close()
        return data
    else:
        with open(data_file_path, 'w') as f:
            json.dump(DATA_TEMPLATE, f, indent=2)
        f.close()
        return DATA_TEMPLATE


def save_data(data, data_file_path):
    """
    save data.json if exists
    --
    """
    if os.path.exists(data_file_path):
        with open(data_file_path, 'w') as f:
            json.dump(data, f, indent=2)
        f.close()
        return True
    else:
        return False


# ? on import
initialize_project_folders(CONFIG_TEMPLATE['folders'])
