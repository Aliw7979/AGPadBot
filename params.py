#Interface titles
WELCOME = '''سلام به ربات دانا خوش آمدید. شما می‌توانید از این بات برای گفت‌و‌گو به صورت متنی و یا وویس استفاده کنید.'''
NOWCOINS = ''' مقدار سکه های فعلی شما: {} '''
PACKAGE_DURATION = "زمان باقی مانده بسته شما: {}"
UNLIMITED = 'نامحدود'
LIMIT_PACKAGE = 'محدودیت زمانی: {}'
LIMIT_PACKAGE_DAYS = "{} روزه"
DURATION = 'تا تاریخ {}/{}/{} و ساعت {}:{}:{}'
WARN_ACTIVE_PACKAGE = '📌بسته دیگری برای شما فعال می‌باشد، برای خرید بسته جدید باید تا پایان بسته فعلی صبر کنید.'
SERVICEDOWN = '''در حال حاضر سرویس در دسترس نمی‌باشد'''
CHOOSE_PACKAGE = '''لطفا بسته مورد نظر خود را برای خرید سکه انتخاب کنید : '''
PURCHASE_LINK = ''' لینک خرید سکه مورد نظر :'''
INSUFFICIENT_COIN = '''❌شما سکه کافی ندارید❌'''
TOO_MANY_REQ = '''تعداد درخواست های شما از حد مجاز گذشته است لطفا صبر کنید. با تشکر🙏'''
ENROLMENT = '''لطفا اول در کانال ما عضو شوید.'''
ENROLMENT_BUTTON = '''عضویت در کانال ما'''
INVITE_LINK_DESCRIPTION = '''لینک دعوت شما :'''
CURRENCY = ''' تومان'''
COIN = '''سکه '''
PURCHASE = '''خرید '''
WAITING = '''پیام شما در حال پردازش می باشد...'''
CHOOSE_MODE = '''لطفا نقش ربات را انتخاب کنید.'''
MODE_CHANGED = '''حال ربات در نقش {} با شما حرف می‌زند.'''
RESET_CHAT = '''گفت‌و‌گو جدید آغاز شد.'''
CONVERT_TO_VOICE = '''دریافت پیام به صورت صوت'''
CLICK_COIN_BUTTON = '''با لمس گزینه های بالا می‌توانید لینک خرید سکه را دریافت کنید.'''
CLICK_MODE_BUTTON = '''با لمس گزینه‌های بالا می‌توانید نقش ربات را انتخاب کنید.'''
CONVERTED_USER_VOICE = '''پیام شما: \n {}'''
GET_FREE_COIN_DESCRIPTION = '''شما با دادن این لینک به دوستانتان می‌توانید آن ها را به بات دعوت کنید و به ازای اولین خرید هرکدام از دوستانتان به شما ۵ سکه هدیه داده می‌شود.'''
INVITATION_MESSAGE = 'سلام!✋\nمن از بات دانا که دستیار هوشمند صوتی می‌باشد استفاده می‌کنم و پیشنهاد می‌کنم تو هم استفاده بکنی.\nکافیه رو لینک زیر کلیک کنی:\n{}'
SUPPORT_MESSAGE = '''شناسه کاربر:
{}

تهیه شده توسط شرکت عصرگویش‌پرداز:
https://www.asr-gooyesh.com

کانال شرکت:
@asrgooyeshpardaz

ارتباط با ادمین:
@asrgooyesh

اینستاگرام:
AsrGooyesh

شماره تماس:
۰۲۱-۶۱۹۳۱۰۰۰
'''

#Api stuff
LEXEME_ADDRESS = "http://79.132.193.62:81/"
DANA_ADDRESS = "http://79.132.193.62:80/"
SET_INVITER = "api/accounts/inviter/{}"
BALE_BOT_LINK = "https://ble.ir/AgpDanaBot/"
LEXEME_SIGNUP = "account/signup/telegrambot"
LEXEME_LOGIN = "account/login"
DANA_GET_KEY = "api/accounts/api_keys/"
USER_ID = "telegram_user_{}"
API_URL = 'http://79.132.193.62/api/telegram/'
ACCOUNT_API = 'api/accounts/info'
PACKAGES_API = "api/packages/"
PURCHASE_PACKAGES_API = "{}/direct_payment/"
CHAT_API = 'api/chatbot/messages/'
VOICE_API = 'api/chatbot/voice/{}'
MODES = "api/chatbot/modes/"
SELECT_MODE = "api/chatbot/new_conversation?mode_id={}"
DEFAULT_CONV = "api/chatbot/new_conversation"
RESET_API = 'reset/'
TELEGRAM_BOT_LINK = "https://t.me/AgpDanaBot"
CHANNEL_LINK = "https://t.me/asrgooyeshpardaz"
CHANNEL_ID = "@asrgooyeshpardaz"
MESSAGE_PENDING = "PENDING"
MESSAGE_FAILED = "FAILURE"
MESSAGE_SUCCESS = "SUCCESS"
MESSAGE_STARTED = "STARTED"
#log
LOG_PATH = "log"
#prefixes
PREFIX_PURCHASE_COIN = "purchaseCoin_"
PREFIX_MODE = "mode_"
PREFIX_MESSAGE_TO_VOICE = "messageToVoice_"


#buttons
START = '''شروع دوباره'''
SHOW_COINS = u"تعداد سکه‌های شما💰"  
SHOW_PACKAGES = u"خرید سکه🥇" 
INVITE_CODE = u'''کد دعوت شما👥'''
SHOW_STATS = u'''مشاهده آمار تبلیغات شما📊'''  
NEW_AD = '''ساختن تبلیغ➕'''
CANCEL = 'انصراف❌'
SUBMIT = 'تأیید نهایی✅'
SUPPORT_BUTTON = '''پشتیبانی☎️'''


#conv
CHOOSING, TYPING_REPLY, TYPING_CHOICE = range(3)
