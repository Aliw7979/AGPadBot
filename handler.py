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


checkUserJoinedChannel = True


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
        dana = await getDanaAPIKey(token)
        userToken = dana.json()
        clients.add_client(
            USER_ID.format(user_id), data["user"]["token"], api_key=userToken["key"]
        )
        userAPIKey = clients.get_all_clients()
        print(userAPIKey)
    else:
        response = await login(user_id)
        print(response.json())
        data = response.json()
        if clients.get_clients_by_id(user_id) != None:
            userToken = dana.json()
            clients.update_client(user_id, data["user"]["token"], None)

        else:
            token = {"Authorization": "Token " + data["user"]["token"]}
            dana = await getDanaAPIKey(token)
            userToken = dana.json()
            clients.add_client(
                USER_ID.format(user_id), data["user"]["token"], api_key=userToken["key"]
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


async def getDanaAPIKey(token):
    api = DANA_ADDRESS + DANA_GET_KEY
    response = requests.post(api, headers=token)
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
        [KeyboardButton(SHOW_PACKAGES), KeyboardButton(SHOW_COINS)],
        [KeyboardButton(SUPPORT_BUTTON)],
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard_buttons, resize_keyboard=True, one_time_keyboard=False
    )
    return reply_markup


async def start(update, context):
    user_id = update.effective_user.id

    await deleteConvertToVoiceButton(update, context, user_id)

    response = await signup(user_id)
    if response.status_code == 201:
        data = response.json()
        token = {"Authorization": "Token " + data["user"]["token"]}
        dana = await getDanaAPIKey(token)
        userToken = dana.json()
        clients.add_client(
            USER_ID.format(user_id), data["user"]["token"], api_key=userToken["key"]
        )
        userAPIKey = clients.get_all_clients()
        print(userAPIKey)
        await context.bot.send_message(
            chat_id=user_id, text=WELCOME, reply_markup=await defautlKeyboardUpdate()
        )

        unique_identifier = context.args[0] if len(context.args) > 0 else None
        if unique_identifier == None:
            invite_link_id = ""
        else:
            invite_link_id = unique_identifier
            inviter_api = DANA_ADDRESS + SET_INVITER.format(invite_link_id)
            response = requests.post(inviter_api, headers=token)
    else:
        response = await login(user_id)
        print(response.json())
        data = response.json()
        if clients.get_clients_by_id(user_id) != None:
            userToken = dana.json()
            clients.update_client(user_id, data["user"]["token"], None)

        else:
            token = {"Authorization": "Token " + data["user"]["token"]}
            dana = await getDanaAPIKey(token)
            userToken = dana.json()
            clients.add_client(
                USER_ID.format(user_id), data["user"]["token"], api_key=userToken["key"]
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


async def getCoinWallet(update, context):
    user_id = update.effective_user.id
    api = DANA_ADDRESS + ACCOUNT_API
    client = clients.get_clients_by_id(USER_ID.format(user_id))
    if client == None:
        await userAuth(user_id)
        client = clients.get_clients_by_id(USER_ID.format(user_id))
    token = {"Authorization": "Token " + client["token"]}
    response = requests.get(api, headers=token)

    await deleteConvertToVoiceButton(update, context, user_id)

    if response.status_code == 200:
        data = response.json()
        if data["package_end_time"] == None:
            await context.bot.send_message(
                chat_id=user_id,
                text=NOWCOINS.format(str(data["package_coin_remain"]))
                + "\n"
                + PACKAGE_DURATION.format(str(UNLIMITED)),
            )
        else:
            dt = datetime.strptime(data["package_end_time"], "%Y-%m-%dT%H:%M:%S%z")

            # Extract year, month, and day
            jdate = jdatetime.datetime.fromgregorian(datetime=dt)

            # Extract the Jalali year, month, and day
            jalali_year = jdate.year
            jalali_month = jdate.month
            jalali_day = jdate.day
            duration = DURATION.format(
                jalali_year, jalali_month, jalali_day, dt.hour, dt.minute, dt.second
            )
            await context.bot.send_message(
                chat_id=user_id,
                text=NOWCOINS.format(str(data["package_coin_remain"]))
                + "\n"
                + PACKAGE_DURATION.format(duration),
            )

    else:
        await context.bot.send_message(chat_id=user_id, text=SERVICEDOWN)


async def getPackages(update, context):
    user_id = update.effective_user.id
    client = clients.get_clients_by_id(USER_ID.format(user_id))
    if client == None:
        await userAuth(user_id)
        client = clients.get_clients_by_id(USER_ID.format(user_id))
    token = {"Authorization": "Token " + client["token"]}
    getPackage = DANA_ADDRESS + PACKAGES_API
    response = requests.get(getPackage, headers=token)

    await deleteConvertToVoiceButton(update, context, user_id)

    if response.status_code == 200:
        data = response.json()
        keyboard = [[]]
        for coin in data:
            if coin["duration"] == None:
                button = InlineKeyboardButton(
                    PURCHASE
                    + str(coin["coin"])
                    + COIN
                    + str(coin["cost"])
                    + CURRENCY
                    + "\n"
                    + LIMIT_PACKAGE.format(UNLIMITED),
                    callback_data=PREFIX_PURCHASE_COIN + str(coin["id"]),
                )
            else:
                numbers = re.findall(r"\d+", coin["duration"])
                # Extract the days, hours, minutes, and seconds from the numbers list
                days = int(numbers[0])
                button = InlineKeyboardButton(
                    PURCHASE
                    + str(coin["coin"])
                    + COIN
                    + str(coin["cost"])
                    + CURRENCY
                    + "\n"
                    + LIMIT_PACKAGE.format(LIMIT_PACKAGE_DAYS.format(days)),
                    callback_data=PREFIX_PURCHASE_COIN + str(coin["id"]),
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


async def purchaseCoinHandler(update, context):
    user_id = update.effective_user.id
    query = update.callback_query
    button_data = query.data
    button_data = button_data[len(PREFIX_PURCHASE_COIN) : len(button_data)]
    api = DANA_ADDRESS + PACKAGES_API + PURCHASE_PACKAGES_API.format(button_data)
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
        numbers = re.findall(r"\d+", data["package_duration"])
        # Extract the days, hours, minutes, and seconds from the numbers list
        days = int(numbers[0])
        if days == None:
            await context.bot.send_message(
                chat_id=user_id,
                text=PURCHASE_LINK
                + "\n"
                + data["redirect_url"]
                + "\n"
                + LIMIT_PACKAGE.format(UNLIMITED)
                + "\n"
                + str(data["package_coins"])
                + " "
                + COIN
                + "\n"
                + str(data["package_cost"])
                + " "
                + CURRENCY,
            )
        else:
            await context.bot.send_message(
                chat_id=user_id,
                text=PURCHASE_LINK
                + "\n"
                + data["redirect_url"]
                + "\n"
                + LIMIT_PACKAGE.format(LIMIT_PACKAGE_DAYS.format(days))
                + "\n"
                + str(data["package_coins"])
                + " "
                + COIN
                + "\n"
                + str(data["package_cost"])
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


async def textMessageHandler(update, context):
    try:
        pendingMessage = None
        user_id = update.effective_user.id
        api = DANA_ADDRESS + CHAT_API
        if checkUserJoinedChannel == True:
            if await joinChannelCheck(user_id, context) == False:
                keyboard = [[InlineKeyboardButton(ENROLMENT_BUTTON, url=CHANNEL_LINK)]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await context.bot.send_message(
                    chat_id=user_id, text=ENROLMENT, reply_markup=reply_markup
                )
                return

        pendingMessage = await context.bot.send_message(chat_id=user_id, text=WAITING)
        reply_markup = await convertToVoiceKeyboard()
        await deleteConvertToVoiceButton(update, context, user_id)
        userAPIKey = clients.get_clients_by_id(USER_ID.format(user_id))
        if userAPIKey == None:
            await userAuth(user_id)
            userAPIKey = clients.get_clients_by_id(USER_ID.format(user_id))
        api_key = {"x-api-key": userAPIKey["api_key"]}
        response = requests.post(
            api, headers=api_key, json={"text": update.message.text}
        )
        if response.status_code == 200:
            if response.json()["status"] == MESSAGE_PENDING:
                trackingUrl = response.json()["tracking_url"]
                print(f"respose from server : {response.json()}")

                while True:
                    time.sleep(0.3)
                    trackResponse = requests.get(trackingUrl, headers=api_key)
                    print(trackResponse.json())
                    if (
                        trackResponse.json()["status"] == MESSAGE_PENDING
                        or trackResponse.json()["status"] == MESSAGE_STARTED
                    ):
                        continue
                    elif trackResponse.json()["status"] == MESSAGE_FAILED:
                        await context.bot.send_message(
                            chat_id=user_id, text=SERVICEDOWN
                        )
                        break
                    elif trackResponse.json()["status"] == MESSAGE_SUCCESS:
                        await insertToLastMessage(
                            user_id, trackResponse.json()["message_id"]
                        )
                        await context.bot.edit_message_text(
                            chat_id=user_id,
                            message_id=pendingMessage.message_id,
                            text=trackResponse.json()["result"],
                            reply_markup=reply_markup,
                        )
                        break

        elif response.status_code == 402:
            print(response.json())
            await context.bot.edit_message_text(
                chat_id=user_id,
                message_id=pendingMessage.message_id,
                text=INSUFFICIENT_COIN.format(response.json()["time_remains"]),
            )

        elif response.status_code == 429:
            await context.bot.send_message(chat_id=user_id, text=TOO_MANY_REQ)
        else:
            await context.bot.send_message(chat_id=user_id, text=SERVICEDOWN)
    except Exception as e:
        print(e)


async def voiceMessageHandler(update, context):
    pendingMessage = None
    user_id = update.effective_user.id
    api = DANA_ADDRESS + CHAT_API
    userAPIKey = clients.get_clients_by_id(USER_ID.format(user_id))
    api_key = {"x-api-key": userAPIKey["api_key"]}
    if checkUserJoinedChannel == True:
        if await joinChannelCheck(user_id, context) == False:
            keyboard = [[InlineKeyboardButton(ENROLMENT_BUTTON, url=CHANNEL_LINK)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(
                chat_id=user_id, text=ENROLMENT, reply_markup=reply_markup
            )
            return

    await deleteConvertToVoiceButton(update, context, user_id)

    reply_markup = await convertToVoiceKeyboard()

    pendingMessage = await context.bot.send_message(chat_id=user_id, text=WAITING)

    voice_file_id = update.message.voice.file_id
    file_url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/getFile?file_id={voice_file_id}"
    response = requests.get(file_url)
    file_data = response.json()["result"]
    file_url = (
        f'https://api.telegram.org/file/bot{config.BOT_TOKEN}/{file_data["file_path"]}'
    )
    response = requests.get(file_url)

    voice_data = response.content

    files = {"audio": ("voice_message.ogg", voice_data)}
    response = requests.post(api, headers=api_key, files=files)
    print(f"voice message structure : {response.json()}")

    if response.status_code == 200:
        if response.json()["status"] == MESSAGE_PENDING:
            trackingUrl = response.json()["tracking_url"]
            while True:
                time.sleep(0.3)
                trackResponse = requests.get(trackingUrl, headers=api_key)
                if (
                    trackResponse.json()["status"] == MESSAGE_PENDING
                    or trackResponse.json()["status"] == MESSAGE_STARTED
                ):
                    continue
                elif trackResponse.json()["status"] == MESSAGE_FAILED:
                    await context.bot.send_message(chat_id=user_id, text=SERVICEDOWN)
                    break
                elif trackResponse.json()["status"] == MESSAGE_SUCCESS:
                    await insertToLastMessage(
                        user_id, trackResponse.json()["message_id"]
                    )
                    print(f"voice message structure : {trackResponse.json()}")
                    await context.bot.edit_message_text(
                        chat_id=user_id,
                        message_id=pendingMessage.message_id,
                        text=CONVERTED_USER_VOICE.format(
                            trackResponse.json()["message"]
                        ),
                    )
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=trackResponse.json()["result"],
                        reply_markup=reply_markup,
                    )
                    break
    elif response.status_code == 402:
        await context.bot.edit_message_text(
            chat_id=user_id,
            message_id=pendingMessage.message_id,
            text=INSUFFICIENT_COIN.format(response.json()["time_remains"]),
        )

    elif response.status_code == 429:
        await context.bot.send_message(chat_id=user_id, text=TOO_MANY_REQ)
    else:
        await context.bot.send_message(chat_id=user_id, text=SERVICEDOWN)


async def messageToVoice(update, context):
    query = update.callback_query
    user_id = update.effective_user.id
    api = DANA_ADDRESS + VOICE_API
    lastMessageUserRecieved = lastMessages.get_message_by_id(USER_ID.format(user_id))
    api = api.format(lastMessageUserRecieved["message"])
    userAPIKey = clients.get_clients_by_id(USER_ID.format(user_id))
    if userAPIKey == None:
        await userAuth(user_id)
        userAPIKey = clients.get_clients_by_id(USER_ID.format(user_id))
    api_key = {"x-api-key": userAPIKey["api_key"]}
    response = requests.get(api, headers=api_key)

    if response.status_code == 200:
        audio_bytes = base64.b64decode(response.json()["voice"])
        audio_file = io.BytesIO(audio_bytes)
        voice = telegram.InputFile(audio_file)
        await context.bot.send_voice(chat_id=user_id, voice=voice)
        # await context.bot.answer_callback_query(callback_query_id=query.id, text = WAITING)
        try:
            await context.bot.edit_message_reply_markup(
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                reply_markup=None,
            )
        except telegram.error.BadRequest as e:
            return

    else:
        if response["code"] == 2:
            await context.bot.send_message(chat_id=user_id, text=INSUFFICIENT_COIN)

        else:
            await context.bot.send_message(chat_id=user_id, text=SERVICEDOWN)


# async def getCoinWithInviteLink(update, context):
#     user_id = update.effective_user.id
#     client = clients.get_clients_by_id(USER_ID.format(user_id))
#     if client == None:
#         await userAuth(user_id)
#         client = clients.get_clients_by_id(USER_ID.format(user_id))

#     token = {"Authorization" : "Token " + client["token"]}
#     api = DANA_ADDRESS + ACCOUNT_API
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


async def getChatModes(update, context):
    user_id = update.effective_user.id
    getPackage = DANA_ADDRESS + MODES
    userAPIKey = clients.get_clients_by_id(USER_ID.format(user_id))
    if userAPIKey == None:
        await userAuth(user_id)
        userAPIKey = clients.get_clients_by_id(USER_ID.format(user_id))
    api_key = {"x-api-key": userAPIKey["api_key"]}
    response = requests.get(getPackage, headers=api_key)

    if checkUserJoinedChannel == True:
        if await joinChannelCheck(user_id, context) == False:
            keyboard = [[InlineKeyboardButton(ENROLMENT_BUTTON, url=CHANNEL_LINK)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            context.bot.send_message(
                chat_id=user_id, text=ENROLMENT, reply_markup=reply_markup
            )
            return

    await deleteConvertToVoiceButton(update, context, user_id)

    if response.status_code == 200:
        data = response.json()
        keyboard = [[]]
        for mode in data:
            button = InlineKeyboardButton(
                str(mode["name"]), callback_data=PREFIX_MODE + str(mode["id"])
            )

            row = [button]
            keyboard.append(row)

        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=user_id, text=CHOOSE_MODE, reply_markup=reply_markup
        )
        await context.bot.send_message(
            chat_id=user_id,
            text=CLICK_MODE_BUTTON,
            reply_markup=await defautlKeyboardUpdate(),
        )

    else:
        await context.bot.send_message(chat_id=user_id, text=SERVICEDOWN)


async def chooseModeHandler(update, context):
    user_id = update.effective_user.id
    query = update.callback_query
    button_data = query.data
    button_data = button_data[len(PREFIX_MODE) : len(button_data)]
    api = DANA_ADDRESS + SELECT_MODE.format(button_data)
    userAPIKey = clients.get_clients_by_id(USER_ID.format(user_id))
    if userAPIKey == None:
        await userAuth(user_id)
        userAPIKey = clients.get_clients_by_id(USER_ID.format(user_id))
    api_key = {"x-api-key": userAPIKey["api_key"]}
    response = requests.get(api, headers=api_key)

    if checkUserJoinedChannel == True:
        if await joinChannelCheck(user_id, context) == False:
            keyboard = [[InlineKeyboardButton(ENROLMENT_BUTTON, url=CHANNEL_LINK)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            context.bot.send_message(
                chat_id=user_id, text=ENROLMENT, reply_markup=reply_markup
            )
            return

    if response.status_code == 200:
        await context.bot.send_message(
            chat_id=user_id, text=MODE_CHANGED.format(response.json()["bot_mode_name"])
        )
        await context.bot.answer_callback_query(
            callback_query_id=query.id, text=WAITING
        )
        # await context.bot.edit_message_reply_markup(chat_id=user_id, message_id=query.message.message_id, reply_markup=)
    else:
        await context.bot.send_message(chat_id=user_id, text=SERVICEDOWN)


async def newChat(update, context):
    user_id = update.effective_user.id
    api = DANA_ADDRESS + DEFAULT_CONV
    userAPIKey = clients.get_clients_by_id(USER_ID.format(user_id))
    if userAPIKey == None:
        await userAuth(user_id)
        userAPIKey = clients.get_clients_by_id(USER_ID.format(user_id))
    api_key = {"x-api-key": userAPIKey["api_key"]}
    response = requests.get(api, headers=api_key)
    await deleteConvertToVoiceButton(update, context, user_id)

    if checkUserJoinedChannel == True:
        if await joinChannelCheck(user_id, context) == False:
            keyboard = [[InlineKeyboardButton(ENROLMENT_BUTTON, url=CHANNEL_LINK)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            context.bot.send_message(
                chat_id=user_id, text=ENROLMENT, reply_markup=reply_markup
            )
            return

    if response.status_code == 200:
        await context.bot.send_message(
            chat_id=user_id, text=RESET_CHAT, reply_markup=await defautlKeyboardUpdate()
        )
    else:
        await context.bot.send_message(chat_id=user_id, text=SERVICEDOWN)


async def support(update, context):
    await context.bot.sendMessage(
        chat_id=update.message.chat_id,
        text=SUPPORT_MESSAGE.format(f"telegram_user_{update.message.chat_id}"),
    )


async def help(update, context):
    await context.bot.sendMessage(
        chat_id=update.message.chat_id, text=params.intro, disable_web_page_preview=True
    )


async def restart(update, context):
    logger.info("User {0} ended the chat.".format(update.effective_chat))
    return CHOOSING


async def end(update, context):
    logger.info("User {0} chat timeouted.".format(update.effective_chat))
    return ConversationHandler.TIMEOUT


def facts_to_str(user_data: Dict[str, str]) -> str:
    """Helper function for formatting the gathered user info."""
    facts = [f"{key} - {value}" for key, value in user_data.items()]
    return "\n".join(facts).join(["\n", "\n"])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation, display any stored data and ask user for input."""
    reply_text = "Hi! My name is Doctor Botter."
    if context.user_data:
        reply_text += (
            f" You already told me your {', '.join(context.user_data.keys())}. Why don't you "
            "tell me something more about yourself? Or change anything I already know."
        )
    else:
        reply_text += (
            " I will hold a more complex conversation with you. Why don't you tell me "
            "something about yourself?"
        )
    await update.message.reply_text(
        reply_text, reply_markup=await defautlKeyboardUpdate()
    )

    return CHOOSING


async def secondryKeyboard():
    keyboard_buttons = [[KeyboardButton(CANCEL)]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard_buttons, resize_keyboard=True, one_time_keyboard=False
    )
    return reply_markup


async def adChoice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask the user for info about the selected predefined choice."""
    text = update.message.text.lower()
    context.user_data["choice"] = text
    if text == NEW_AD:
        reply_text = SEND_IMAGE_OF_AD
    await update.message.reply_text(reply_text, reply_markup=await secondryKeyboard())
    return SEND_IMAGE


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
    context.user_data["ad_text"] = update.message.text
    keyboard_buttons = [[KeyboardButton(CONFIRM)], [KeyboardButton(CANCEL)]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard_buttons, resize_keyboard=True, one_time_keyboard=False
    )
    photo_id = context.user_data.get("photo_id")
    if photo_id:
        # Get the File object for the photo
        file = await context.bot.get_file(photo_id)
        if file:
            # Send the photo to the user
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=file,
                caption=context.user_data["ad_text"],
            )

    await update.message.reply_text(text=AD_CONFIRMATION, reply_markup=reply_markup)

    return CONFIRMATION


async def show_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display the gathered info."""
    await update.message.reply_text(
        f"This is what you already told me: {facts_to_str(context.user_data)}"
    )


async def done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display the gathered info and end the conversation."""
    if "choice" in context.user_data:
        del context.user_data["choice"]

    await update.message.reply_text(
        f"I learned these facts about you: {facts_to_str(context.user_data)}Until next time!",
        reply_markup=ReplyKeyboardRemove(),
    )
    return CHOOSING


async def confirmOperation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == CANCEL:
        await update.message.reply_text(text=CANCEL_MESSAGE)
        return await cancelOperation(update,context)


    await update.message.reply_text(
        text=AD_DONE, reply_markup=await defautlKeyboardUpdate()
    )


async def cancelOperation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        text=CANCEL_MESSAGE, reply_markup=await defautlKeyboardUpdate()
    )
    return CHOOSING
