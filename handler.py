import hashlib
import base64
import io
import telegram
from telegram.ext import ConversationHandler, ContextTypes
from config import *
import os
import params
from params import *
import logging
from telegram import *
import requests
import config
import time
from database import clients, lastMessages
import re
import jdatetime
from datetime import datetime
from typing import Dict
from io import BytesIO

checkUserJoinedChannel = False


def setup_logger(logger_name: str, log_file: str, level=logging.INFO):
    """
    Setup the logger.
    :param logger_name: logger name
    :type logger_name: str
    :param log_file: logger file name
    :type log_file: str
    :param level: logging level
    :type level: int
    :return: None
    """
    l = logging.getLogger(logger_name)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    fileHandler = logging.FileHandler(log_file, mode="w")
    fileHandler.setFormatter(formatter)
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)

    # Filter to only log messages with severity level ERROR or higher
    filter = logging.Filter()
    filter.filter = lambda record: record.levelno >= logging.ERROR
    fileHandler.addFilter(filter)
    streamHandler.addFilter(filter)

    l.setLevel(level)
    l.addHandler(fileHandler)
    l.addHandler(streamHandler)


logging.basicConfig(
    filename=os.path.join(params.LOG_PATH, "ERROR.log"),
    filemode="w",
    level=logging.ERROR,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
setup_logger(__name__, os.path.join(params.LOG_PATH, "INFO.log"))
logger = logging.getLogger(__name__)


async def joinChannelCheck(user_id, context):
    member = await context.bot.getChatMember(chat_id=CHANNEL_ID, user_id=user_id)
    if member.status == "left":
        return False
    else:
        return True


async def generate_password(keyInt):
    key = str(keyInt)
    # Create a SHA-256 hash object
    sha256 = hashlib.sha256()
    key = key + HASH_EXTEND
    # Convert the key to bytes and hash it
    sha256.update(key.encode("utf-8"))

    # Get the hashed password as a hexadecimal string
    hashed_password = sha256.hexdigest()

    # Return the hashed password
    return hashed_password


async def userAuth(user_id):
    response = await signup(user_id)
    if response.status_code == 201:
        data = response.json()
        token = {"Authorization": "Token " + data["user"]["token"]}

        clients.add_client(
            USER_ID.format(user_id), data["user"]["token"]
        )
        userAPIKey = clients.get_all_clients()
        print(userAPIKey)
    else:
        response = await login(user_id)
        data = response.json()
        if clients.get_clients_by_id(user_id) != None:
            clients.update_client(user_id, data["user"]["token"])

        else:
            token = {"Authorization": "Token " + data["user"]["token"]}

            clients.add_client(
                USER_ID.format(user_id), data["user"]["token"]
            )


async def signup(user_id):
    api = LEXEME_ADDRESS + LEXEME_SIGNUP
    password = await generate_password(user_id)
    response = requests.post(
        api,
        json={"username": USER_ID.format(user_id), "password": password[0:9]},
        headers=API_TOKEN,
    )

    return response


async def login(user_id):
    api = LEXEME_ADDRESS + LEXEME_LOGIN
    password = await generate_password(user_id)
    response = requests.post(
        api,
        json={
            "username_or_phone_or_email": USER_ID.format(user_id),
            "password": password[0:9],
        },
    )
    return response





async def defautlKeyboardUpdate():
    # keyboard_buttons = [
    # [KeyboardButton(NEW_CONV),KeyboardButton(SHOW_MODES)],
    # [KeyboardButton(SHOW_PACKAGES),KeyboardButton(SHOW_COINS)],
    # [KeyboardButton(INVITE_CODE),KeyboardButton(SUPPORT_BUTTON)],
    # ]
    keyboard_buttons = [
        [KeyboardButton(NEW_AD)],
        [KeyboardButton(SHOW_STATS)],
        [KeyboardButton(SHOW_PACKAGES), KeyboardButton(BUY_PACKAGES)],
        [KeyboardButton(SUPPORT_BUTTON)],
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard_buttons, resize_keyboard=True, one_time_keyboard=False
    )
    return reply_markup


# async def start(update, context):
 

async def getMyPackages(update: Update, context):
    user_id = update.effective_user.id
    api = AD_ADDRESS + ACCOUNT_API
    client = clients.get_clients_by_id(USER_ID.format(user_id))
    if client == None:
        await userAuth(user_id)
        client = clients.get_clients_by_id(USER_ID.format(user_id))
    token = {"Authorization": "Token " + client["token"]}
    getAds = AD_ADDRESS + PURCHASED_PLANS_API
    response = requests.get(getAds, headers=token)
    if response.status_code == 200:
        data = response.json()
        is_empty = True
        for package in data["results"]:
            if(package["status"] == CREATED):
                await update.message.reply_text(PACKAGE_INFO.format(str(package["plan_views"])))
                is_empty = False
        if is_empty == True:
            await update.message.reply_text(text = DONT_HAVE_PACKAGE,reply_markup=await defautlKeyboardUpdate())

async def getPackages(update, context):
    user_id = update.effective_user.id
    client = clients.get_clients_by_id(USER_ID.format(user_id))
    if client == None:
        await userAuth(user_id)
        client = clients.get_clients_by_id(USER_ID.format(user_id))
    # token = {"Authorization": "Token " + client["token"]}
    getPackage = AD_ADDRESS + PLANS_API
    response = requests.get(getPackage, headers=API_TOKEN)

    if response.status_code == 200:
        data = response.json()
        keyboard = [[]]
        for package in data["results"]:
            button = InlineKeyboardButton(
                PURCHASE
                + str(package["views"])
                + VIEW
                + str(package["cost"])
                + CURRENCY,
                callback_data=PREFIX_PURCHASE_PACKAGE + str(package["id"]),
            )
            row = [button]
            keyboard.append(row)

        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=user_id, text=CHOOSE_PACKAGE, reply_markup=reply_markup
        )
        await context.bot.send_message(chat_id=user_id, text=CLICK_COIN_BUTTON)

    else:
        await context.bot.send_message(chat_id=user_id, text=SERVICEDOWN)


async def purchasePlan(update, context):
    user_id = update.effective_user.id
    query = update.callback_query
    button_data = query.data
    button_data = button_data[len(PREFIX_PURCHASE_PACKAGE
) : len(button_data)]
    api = AD_ADDRESS + PLANS_API + PURCHASE_PACKAGES_API.format(button_data)
    client = clients.get_clients_by_id(USER_ID.format(user_id))
    if client == None:
        await userAuth(user_id)
        client = clients.get_clients_by_id(USER_ID.format(user_id))
    token = {"Authorization": "Token " + client["token"]}
    response = requests.get(api, headers=token)

    if checkUserJoinedChannel == True:
        if await joinChannelCheck(user_id, context) == False:
            keyboard = [[InlineKeyboardButton(ENROLMENT_BUTTON, url=CHANNEL_LINK)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(
                chat_id=user_id, text=ENROLMENT, reply_markup=reply_markup
            )
            return

    if response.status_code == 200:
        data = response.json()
        await context.bot.send_message(
                chat_id=user_id,
                text=PURCHASE_LINK
                + "\n"
                + data["redirect_url"]
                + "\n"
                + str(data["plan_views"])
                + " "
                + VIEW
                + "\n"
                + str(data["plan_cost"])
                + " "
                + CURRENCY,
            )
    elif response.status_code == 409:
        await context.bot.send_message(chat_id=user_id, text=WARN_ACTIVE_PACKAGE)
    else:
        await context.bot.send_message(chat_id=user_id, text=SERVICEDOWN)

    print(
        f"button data = {button_data}, responscode = {response.status_code}, response = {response.json()} "
    )


async def convertToVoiceKeyboard():
    keyboard = [
        [InlineKeyboardButton(CONVERT_TO_VOICE, callback_data=PREFIX_MESSAGE_TO_VOICE)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


async def deleteConvertToVoiceButton(
    update, context, user_id, voiceButtonClicked=False
):
    try:
        if voiceButtonClicked == False:
            last_message_id = update.message.message_id - 1
        else:
            last_message_id = update.message.message_id

        empty_keyboard = InlineKeyboardMarkup([])
        await context.bot.edit_message_reply_markup(
            chat_id=user_id, message_id=last_message_id, reply_markup=empty_keyboard
        )
    except telegram.error.BadRequest:
        print("")


async def insertToLastMessage(user_id, id):
    exist = lastMessages.get_message_by_id(user_id)
    if exist == None:
        lastMessages.add_message(USER_ID.format(user_id), id)
    else:
        lastMessages.update_message(user_id, id)


# async def getCoinWithInviteLink(update, context):
#     user_id = update.effective_user.id
#     client = clients.get_clients_by_id(USER_ID.format(user_id))
#     if client == None:
#         await userAuth(user_id)
#         client = clients.get_clients_by_id(USER_ID.format(user_id))

#     token = {"Authorization" : "Token " + client["token"]}
#     api = AD_ADDRESS + ACCOUNT_API
#     response = requests.get(api, headers=token)
#     invite_link = response.json()["invitation_code"]

#     # if checkUserJoinedChannel == True:
#     #     if await joinChannelCheck(user_id, context) == False:
#     #         keyboard = [[InlineKeyboardButton(ENROLMENT_BUTTON, url=CHANNEL_LINK)]]
#     #         reply_markup = InlineKeyboardMarkup(keyboard)
#     #         await context.bot.send_message(
#     #             chat_id=user_id, text=ENROLMENT.format(CHANNEL_LINK),
#     #         )
#     #         return

#     await deleteConvertToVoiceButton(update, context, user_id)
#     await context.bot.send_message(chat_id=user_id, text=GET_FREE_COIN_DESCRIPTION)
#     text = INVITATION_MESSAGE.format("\n" + f"{TELEGRAM_BOT_LINK}?start={invite_link}")
#     await context.bot.send_message(chat_id=user_id, text=text)

async def support(update, context):
    await context.bot.sendMessage(
        chat_id=update.message.chat_id,
        text=SUPPORT_MESSAGE.format(f"telegram_user_{update.message.chat_id}"),
    )


async def help(update, context):
    await context.bot.sendMessage(
        chat_id=update.message.chat_id, text=params.intro, disable_web_page_preview=True
    )



async def end(update, context):
    logger.info("User {0} chat timeouted.".format(update.effective_chat))
    return ConversationHandler.TIMEOUT


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    response = await signup(user_id)
    if response.status_code == 201:
        data = response.json()
        token = {"Authorization": "Token " + data["user"]["token"]}
        clients.add_client(
            USER_ID.format(user_id), data["user"]["token"]
        )
        userAPIKey = clients.get_all_clients()
        await context.bot.send_message(
            chat_id=user_id, text=WELCOME, reply_markup=await defautlKeyboardUpdate()
        )

        unique_identifier = context.args[0] if len(context.args) > 0 else None
        if unique_identifier == None:
            invite_link_id = ""
        else:
            invite_link_id = unique_identifier
            inviter_api = AD_ADDRESS + SET_INVITER.format(invite_link_id)
            response = requests.post(inviter_api, headers=token)
    else:
        response = await login(user_id)
        print(response.json())
        data = response.json()
        if clients.get_clients_by_id(user_id) != None:
            clients.update_client(user_id, data["user"]["token"])

        else:
            token = {"Authorization": "Token " + data["user"]["token"]}
            clients.add_client(
                USER_ID.format(user_id), data["user"]["token"]
            )
        await context.bot.send_message(
            chat_id=user_id, text=WELCOME, reply_markup=await defautlKeyboardUpdate()
        )

    if checkUserJoinedChannel == True:
        if await joinChannelCheck(user_id, context) == False:
            keyboard = [[InlineKeyboardButton(ENROLMENT_BUTTON, url=CHANNEL_LINK)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            context.bot.send_message(
                chat_id=user_id, text=ENROLMENT, reply_markup=reply_markup
            )
            return


async def secondryKeyboard():
    keyboard_buttons = [[KeyboardButton(CANCEL)]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard_buttons, resize_keyboard=True, one_time_keyboard=False
    )
    return reply_markup

async def extractButtons(package):
    keyboard = [[]]
    keyboardIsEmpty = True
    if(package["button1text"] != None):
        keyboardIsEmpty = False
        button = InlineKeyboardButton(
                text = package["button1text"],
                url=package["button1link"]
            )
        row = [button]
        keyboard.append(row)
    if(package["button2text"] != None):
        keyboardIsEmpty = False
        button = InlineKeyboardButton(
                text = package["button1text"],
                url=package["button1link"]
            )
        row = [button]
        keyboard.append(row)
    if(package["button3text"] != None):
        keyboardIsEmpty = False
        button = InlineKeyboardButton(
                text = package["button1text"],
                url=package["button1link"]
            )
        row = [button]
        keyboard.append(row)
    print(keyboard)
    reply_markup_pre = InlineKeyboardMarkup(keyboard)
    if(keyboardIsEmpty == True):
        return False, reply_markup_pre
    else:
        return True, reply_markup_pre

async def adChoice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask the user for info about the selected predefined choice."""
    user_id = update.effective_user.id
    text = update.message.text
    context.user_data["choice"] = text
    if text == NEW_AD:
        client = clients.get_clients_by_id(USER_ID.format(user_id))
        if client == None:
            await userAuth(user_id)
            client = clients.get_clients_by_id(USER_ID.format(user_id))
        token = {"Authorization": "Token " + client["token"]}
        getAds = AD_ADDRESS + PURCHASED_PLANS_API
        response = requests.get(getAds, headers=token)
        if response.status_code == 200:
            data = response.json()
            keyboard = [[]]
            is_empty = True
            for package in data["results"]:
                if(package["status"] == CREATED):
                    button = InlineKeyboardButton(
                        PACKAGE_INFO.format(str(package["plan_views"])), 
                        callback_data = PREFIX_PACKAGE_TO_USE + str(package["id"]),
                    )
                    row = [button]
                    keyboard.append(row)
                    is_empty = False
            if is_empty == True:
                await update.message.reply_text(text = DONT_HAVE_PACKAGE,reply_markup=await defautlKeyboardUpdate())
                return ConversationHandler.END
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(text = REQUEST_REVIEWED,reply_markup=await secondryKeyboard())
            await context.bot.send_message(
                chat_id=user_id, text=CHOOSE_PURCHASED_PACKAGE, reply_markup=reply_markup
            )
            return SELECT_PACKAGE
        else:
            await update.message.reply_text(SERVICEDOWN, reply_markup=await defautlKeyboardUpdate())
            return ConversationHandler.END
    
    if text == SHOW_STATS:
        client = clients.get_clients_by_id(USER_ID.format(user_id))
        if client == None:
            await userAuth(user_id)
            client = clients.get_clients_by_id(USER_ID.format(user_id))
        token = {"Authorization": "Token " + client["token"]}
        getAds = AD_ADDRESS + PURCHASED_PLANS_API + "?limit=100"
        response = requests.get(getAds, headers=token)
        is_empty = True
        if response.status_code == 200:
            data = response.json()
            for package in data["results"]:
                if(package["status"] == CREATED):
                    continue
                responseOfImage = requests.get(package['image'])
                textOfAd = package['text']
                if package['status'] == EDITED:
                    hasKeyboard,keyboardButtons = await extractButtons(package)
                    if(hasKeyboard == False):
                        await update.message.reply_photo(BytesIO(responseOfImage.content), caption = SHOW_STATS_BODY.format(textOfAd,str(package["plan_views"]),AD_PENDING,""))
                    else:
                        await update.message.reply_photo(BytesIO(responseOfImage.content), caption = SHOW_STATS_BODY.format(textOfAd,str(package["plan_views"]),AD_PENDING,""),reply_markup=keyboardButtons)
                if package['status'] == VERIFIED:
                    hasKeyboard,keyboardButtons = await extractButtons(package)
                    if(hasKeyboard == False):
                        await update.message.reply_photo(BytesIO(responseOfImage.content), caption = SHOW_STATS_BODY.format(textOfAd,str(package["plan_views"]),AD_REVIWED,""))
                    else:
                        await update.message.reply_photo(BytesIO(responseOfImage.content), caption = SHOW_STATS_BODY.format(textOfAd,str(package["plan_views"]),AD_REVIWED,""),reply_markup=keyboardButtons)
                elif package['status'] == REJECTED:
                    hasKeyboard,keyboardButtons = await extractButtons(package)
                    if(hasKeyboard == False):
                        await update.message.reply_photo(BytesIO(responseOfImage.content), caption = SHOW_STATS_BODY.format(textOfAd,str(package["plan_views"]),AD_NOT_CONFIRMED,ADMIN_COMMENT))
                    else:
                        await update.message.reply_photo(BytesIO(responseOfImage.content), caption = SHOW_STATS_BODY.format(textOfAd,str(package["plan_views"]),AD_NOT_CONFIRMED,ADMIN_COMMENT),reply_markup=keyboardButtons)

                elif package['status'] == FINISHED:
                    hasKeyboard,keyboardButtons = await extractButtons(package)
                    if(hasKeyboard == False):
                        await update.message.reply_photo(BytesIO(responseOfImage.content), caption = SHOW_STATS_BODY.format(textOfAd,str(package["plan_views"]),AD_REVIWED,FINISHED_VIEWS))
                    else:
                        await update.message.reply_photo(BytesIO(responseOfImage.content), caption = SHOW_STATS_BODY.format(textOfAd,str(package["plan_views"]),AD_REVIWED,FINISHED_VIEWS),reply_markup=keyboardButtons)

        else:
            await update.message.reply_text(SERVICEDOWN, reply_markup=await defautlKeyboardUpdate())
                    


# async def received_information(
#     update: Update, context: ContextTypes.DEFAULT_TYPE
# ) -> int:
#     """Store info provided by user and ask for the next category."""
#     text = update.message.text
#     choice = context.user_data["choice"]
#     if choice == CANCEL:
#         return
#     context.user_data[choice] = text.lower()
#     del context.user_data["choice"]

#     await update.message.reply_text(
#         "Neat! Just so you know, this is what you already told me:"
#         f"{facts_to_str(context.user_data)}"
#         "You can tell me more, or change your opinion on something.",
#         reply_markup=await defautlKeyboardUpdate(),
#     )

#     return CHOOSING


async def receivedImage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Get the photo file ID
    photoId = update.message.photo[-1].file_id
    # Store the photo file ID in user data
    context.user_data["photo_id"] = photoId

    await update.message.reply_text(
        text=SEND_TEXT_OF_AD, reply_markup=await secondryKeyboard()
    )
    return SEND_TEXT


async def receivedText(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data["ad_text"] = update.message.text
        keyboard_buttons = [[KeyboardButton(YES)], [KeyboardButton(NO)]]
        reply_markup = ReplyKeyboardMarkup(
            keyboard_buttons, resize_keyboard=True, one_time_keyboard=False
        )
        await update.message.reply_text(text=WANT_ADD_BUTTON, reply_markup=reply_markup)
        #init buton and link info
        context.user_data['button1text'] = ''
        context.user_data['button2text'] = ''
        context.user_data['button3text'] = ''
        context.user_data['button1link'] = ''
        context.user_data['button2link'] = ''
        context.user_data['button3link'] = ''
        return BUTTON_CONFIRM
    except Exception as e:
        print(e)
        return await cancelOperation(update, context)

async def addButtonConfirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if(update.message.text == YES):
        keyboard_buttons = [[KeyboardButton(CANCEL)]]
        reply_markup = ReplyKeyboardMarkup(
            keyboard_buttons, resize_keyboard=True, one_time_keyboard=False
        )
        await update.message.reply_text(text = FILL_BUTTON_TEXT,reply_markup=reply_markup)
        return BUTTON_TEXT
    elif(update.message.text == NO):
        await adPreview(update, context)
        return CONFIRMATION
    else:
        return BUTTON_CONFIRM
    
async def cancelButton(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await adPreview(update, context)
    return CONFIRMATION

async def setButtonText(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    
    if context.user_data['button1text'] != '' and context.user_data['button2text'] != '' and context.user_data['button3text'] != '':
        await adPreview(update, context)
        return CONFIRMATION
    else:
        if context.user_data['button1text'] == '':
            context.user_data['button1text'] = update.message.text
            await update.message.reply_text(text = FILL_BUTTON_LINK)
            return BUTTON_LINK
        if context.user_data['button2text'] == '':
            context.user_data['button2text'] = update.message.text
            await update.message.reply_text(text = FILL_BUTTON_LINK)
            return BUTTON_LINK    
        if context.user_data['button3text'] == '':
            context.user_data['button3text'] = update.message.text
            await update.message.reply_text(text = FILL_BUTTON_LINK)
            return BUTTON_LINK
    
async def setButtonLink(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if context.user_data['button1text'] != '' and context.user_data['button2text'] != '' and context.user_data['button3link'] != '':
        await adPreview(update, context)
        return CONFIRMATION
    else:
        if update.message.text.startswith('@'):
            await update.message.reply_text(text = CANT_USE_ATSIGN)
            await update.message.reply_text(text = FILL_BUTTON_LINK)
            return BUTTON_LINK
        if context.user_data['button1text'] != '' and context.user_data['button1link'] == '':
            context.user_data['button1link'] = update.message.text
            await update.message.reply_text(text = BUTTON_ADDED)
            keyboard_buttons = [[KeyboardButton(YES)], [KeyboardButton(NO)]]
            reply_markup = ReplyKeyboardMarkup(
            keyboard_buttons, resize_keyboard=True, one_time_keyboard=True
            )
            await update.message.reply_text(text=NEXT_BUTTON_CONFIRMATION, reply_markup=reply_markup)
            return BUTTON_CONFIRM
        elif context.user_data['button2text'] != '' and context.user_data['button2link'] == '':
            context.user_data['button2link'] = update.message.text
            await update.message.reply_text(text = BUTTON_ADDED)
            keyboard_buttons = [[KeyboardButton(YES)], [KeyboardButton(NO)]]
            reply_markup = ReplyKeyboardMarkup(
            keyboard_buttons, resize_keyboard=True, one_time_keyboard=False
            )
            await update.message.reply_text(text=NEXT_BUTTON_CONFIRMATION, reply_markup=reply_markup)
            return BUTTON_CONFIRM
        elif context.user_data['button3text'] != '' and context.user_data['button3link'] == '':
            context.user_data['button3link'] = update.message.text
            await update.message.reply_text(text = BUTTONS_ADDED)
            await adPreview(update, context)
            return CONFIRMATION
    
async def adPreview(update:Update,context: ContextTypes.DEFAULT_TYPE):
    data = {}
    keyboard = [[]]
    keyboardIsEmpty = True
    if(context.user_data["button1text"] !=''):
        button = InlineKeyboardButton(
                context.user_data["button1text"],
                url=context.user_data["button1link"]
            )
        row = [button]
        keyboard.append(row)
        keyboardIsEmpty = False

    if(context.user_data["button2text"] !=''):
        button = InlineKeyboardButton(
                context.user_data["button2text"],
                url=context.user_data["button2link"]
            )
        row = [button]
        keyboard.append(row)
    if(context.user_data["button3text"] !=''):
        button = InlineKeyboardButton(
                context.user_data["button3text"],
                url=context.user_data["button3link"]
            )
        row = [button]
        keyboard.append(row)
    
    reply_markup_pre = InlineKeyboardMarkup(keyboard)
    keyboard_buttons = [[KeyboardButton(CONFIRM)], [KeyboardButton(CANCEL)]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard_buttons, resize_keyboard=True, one_time_keyboard=False
    )
    photo_id = context.user_data.get("photo_id")
    if photo_id and keyboardIsEmpty == False:
            # Send the photo to the user
            await context.bot.send_photo(
                chat_id= update.effective_chat.id,
                photo=photo_id,
                caption=context.user_data["ad_text"],reply_markup=reply_markup_pre
            )
    elif photo_id and keyboardIsEmpty == True:
            # Send the photo to the user
            await context.bot.send_photo(
                chat_id= update.effective_chat.id,
                photo=photo_id,
                caption=context.user_data["ad_text"]
            )
    else:
        # Send the photo to the user
            await context.bot.send_message(
                chat_id= update.effective_chat.id,
                text=context.user_data["ad_text"]
            )
    await update.message.reply_text(text=AD_CONFIRMATION, reply_markup=reply_markup)

async def choosePackageToUse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    query = update.callback_query
    button_data = query.data
    button_data = button_data[len(PREFIX_PACKAGE_TO_USE
    ) : len(button_data)]
    context.user_data["ad_id"] = button_data
    # client = clients.get_clients_by_id(USER_ID.format(user_id))
    # if client == None:
    #     await userAuth(user_id)
    #     client = clients.get_clients_by_id(USER_ID.format(user_id))
    # token = {"Authorization": "Token " + client["token"]}
    # response = requests.get(AD_ADDRESS + GET_SELECTED_AD.format(context), headers=token)
    await context.bot.send_message(chat_id=user_id,text = SELECTED_PACKAGE + "\n" + SEND_IMAGE_OF_AD)
    await context.bot.answer_callback_query(callback_query_id=query.id, text = WAITING)
    return SEND_IMAGE


async def confirmOperation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id  = update.effective_chat.id
    photo_id = context.user_data["photo_id"]
    ad_id = context.user_data["ad_id"]
    ad_text = context.user_data["ad_text"]
    if update.message.text == CANCEL:
        await update.message.reply_text(text=CANCEL_MESSAGE)
        return await cancelOperation(update,context)

    else:
        file = await context.bot.get_file(photo_id)
        photo_url = file.file_path
        photo_data = requests.get(photo_url).content

        data = {}
        TEXT = "{}"
        data["text"] = TEXT.format(ad_text)
        if(context.user_data["button1text"] !=''):
            data["button1text"] = context.user_data["button1text"]
            data["button1link"] = context.user_data["button1link"]
        if(context.user_data["button2text"] !=''):
            data["button2text"] = context.user_data["button2text"]
            data["button2link"] = context.user_data["button2link"]
        if(context.user_data["button3text"] !=''):
            data["button3text"] = context.user_data["button3text"]
            data["button3link"] = context.user_data["button3link"]
        # Prepare the file to be sent to the API
        print(data)
        files = {'image': ('photo.jpg', photo_data)}
        client = clients.get_clients_by_id(USER_ID.format(user_id))
        if client == None:
            await userAuth(user_id)
            client = clients.get_clients_by_id(USER_ID.format(user_id))
        
        token = {"Authorization": "Token " + client["token"]}
        # Get the file path using the getFile method
        # file_path = await context.bot.get_file(photo_id).file_path
        # # Download the photo using the file path
        # photo_url = f"https://api.telegram.org/file/bot{context.bot.token}/{file_path}"
        # photo_file = requests.get(photo_url)
        TEXT = "{}"
        response = requests.put(AD_ADDRESS + GET_SELECTED_AD.format(context.user_data["ad_id"]),headers=token,files = files , data=data)
        if response.status_code == 200:
            await update.message.reply_text(
                text=AD_DONE, reply_markup=await defautlKeyboardUpdate()
            )
            return ConversationHandler.END
        else:
            await update.message.reply_text(
                text=SERVICEDOWN, reply_markup=await defautlKeyboardUpdate()
            )
            return ConversationHandler.END
            
async def done(update:Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return ConversationHandler.END


async def cancelOperation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        text=CANCEL_MESSAGE, reply_markup=await defautlKeyboardUpdate()
    )
    return ConversationHandler.END