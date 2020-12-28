import json
import os
import re
import random
import sys
import logging

from helper import Helper
from user import User
import dialogflow_v2 as dialogflow
import requests
from google.api_core.exceptions import InvalidArgument
from slack_bolt import App
from slack_sdk.errors import SlackApiError

headers = {
    'Content-Type': 'application/json',
}

# Initializes your app with your bot token and signing secret
app = App(
    token=Helper.loadEnvKey("SLACK_BOT_TOKEN"),
    signing_secret=Helper.loadEnvKey("SLACK_SIGNING_SECRET")
)

# Initialize the list for storing the user objects
users = []
# Initialize the dictionary to hold all get to know messages
gatherInfo = {}
# Initzialie the dictionary to hold the users from Slack
users_store = {}

# Regex patterns
RE_EMOJI = re.compile("\s*:[^:\s]*(?:::[^:\s]*)*:")
RE_MENTION = re.compile("\s*<@\w*>")
RE_USERID = re.compile("@\w*")

# Get environment variables
BIG_FIVE = Helper.loadEnvKey("BIG_FIVE").lower()
LIMIT = int(Helper.loadEnvKey("LIMIT").lower())
DIALOGFLOW_PROJECT_ID = Helper.loadEnvKey("DIALOGFLOW_PROJECT_ID")
DIALOGFLOW_LANGUAGE_CODE = Helper.loadEnvKey("DIALOGFLOW_LANGUAGE_CODE")
DIALOGFLOW_INTENT_GETTOKNOW = Helper.loadEnvKey("GETTOKNOW")
REQUEST_URL = Helper.loadEnvKey("URL")
HIGH_VALUE = float(Helper.loadEnvKey("HIGH_VALUE"))
AGENT_TALK = Helper.loadEnvKey("AGENT_TALK")

# Variable for the output file
OUTPUT_FILENAME = "output.json"


def clear_message(text):
    """
    This method cleans the input message from the user.
    It removes all whitespaces, mentions and emojis
    :param text: Expects a user message
    :return: Clean user message
    """
    # remove all whitespaces (space, tab, newline, return, formfeed)
    tmpstr = " ".join(text.split())
    # remove mentions
    tmpstr = RE_MENTION.sub(r"", tmpstr)
    # remove emojis
    tmpstr = RE_EMOJI.sub(r"", tmpstr)
    return tmpstr


def initial_import():
    """
    Method to import the data from the json file
    Creates the missing file
    :return: None
    """
    if os.path.isfile(OUTPUT_FILENAME):
        with open(OUTPUT_FILENAME) as f:
            data = json.load(f)
        for user in data:
            users.append(User(**user))
        logging.info("Imported users")
    else:
        logging.info("File is not readable or missing, creating file...")
        open(OUTPUT_FILENAME, "w")
        logging.info("New output file was created")


def handle_user_message(userid, chat_text):
    """
    Method to handle the user input
    :param userid: Current userid
    :param chat_text: Text from the user
    :return: None
    """
    global users
    if users:
        for user in users:
            if userid == user.userId:
                user.messages.append(chat_text)
                break
        else:
            users.append(User(userid, [chat_text], [], {},
                              random.randint(1, 100000)))
    else:
        users = [User(userid, [chat_text], [], {}, random.randint(1, 100000))]
    logging.info("Handled user input")


def getBigFive(data):
    """
    Gets the big five from a users input
    :param data: data request string with all user messages
    :return: big five dimensions
    """
    try:
        response = requests.post(REQUEST_URL, headers=headers,
                                 data=data.encode("utf-8"),
                                 verify=False)
    except requests.exceptions.RequestException as e:
        logging.error(e)
        sys.exit(1)

    result = json.loads(response.content.decode("utf-8"))
    logging.info("BigFive: " + str(result))
    result.pop("wordCount", None)
    return result


def addBigFive(userid, bigFive):
    """
    Adds the big five result to the user object
    :param userid: Current userid
    :param bigFive: Result of the big five analysis
    :return: None
    """
    for user in users:
        if userid == user.userId:
            user.bigFive = bigFive


def get_message_length(userid):
    """
    Gets the total message length
    :param userid: Current userid
    :return: length of all messages of the current user
    """
    for user in users:
        if userid == user.userId:
            return len(" ".join(user.messages).split())


def get_all_messages(userid):
    """
    Gets all messages
    :param userid: Current userid
    :return: all messages of the current user as a single string
    """
    for user in users:
        if userid == user.userId:
            return " ".join(user.messages)


def get_message_count(userid):
    """
    Gets the count of messages
    :param userid: Current userid
    :return: count of all messages
    """
    for user in users:
        if userid == user.userId:
            return len(user.messages)


def clear_messages(userid):
    """
    Clears the stored messages, bigfive and dialogmessages of a user
    :param userid: Current userid
    :return:
    """
    for user in users:
        if userid == user.userId and len(user.messages) != 0:
            user.messages.clear()
            try:
                user.bigFive.clear()
            except KeyError:
                logging.error("No Big Five Data")
            try:
                user.dialogMessages.clear()
            except KeyError:
                logging.error("No dialog messages")
            return True
    return False


def clear_dialogmessages(userid):
    """
    Clears all dialog messages
    :param userid: Current userid
    :return: None
    """
    for user in users:
        if userid == user.userId:
            try:
                user.dialogMessages.clear()
            except KeyError:
                logging.error("No dialog messages")


def get_sessionid(userid):
    """
    Gets the current session id
    :param userid: Current userid
    :return: None
    """
    for user in users:
        if userid == user.userId:
            return user.lastSessionId


def new_sessionid(userid):
    """
    Creates a new sessions id
    :param userid: Current userid
    :return: New user id
    """
    for user in users:
        if userid == user.userId:
            user.lastSessionId = random.randint(1, 100000)
            return user.lastSessionId


def save_to_file(content, filename):
    """
    Serialize to JSON
    :param content: Content to save
    :param filename: Export file name
    :return: None
    """
    with open(filename, mode="w") as f:
        f.write(json.dumps(content, indent=4, ensure_ascii=False))


@app.event("team_join")
def team_join(body, client, logger, say):
    """
    Listen to the team_join event
    User joined a workspace
    :param body:
    :param client:
    :param logger:
    :param say:
    :return:
    """
    try:
        # Call the users.info method using the built-in WebClient
        result = client.users_info(
            # Call users.info for the user that joined the workspace
            user=body["event"]["user"]["id"]
        )
        logger.info(result)

        user = result["user"]["id"]
        text = f"Willkommen <@{user}>, schön dass du da bist! :slightly_smiling_face:"
        say(text=text, channel=user)

    except SlackApiError as e:
        logger.error("Error fetching conversations: {}".format(e))


def fetch_users(client, logger):
    """
    Fetch the users from Slack
    :param client:
    :param logger:
    :return: None
    """
    try:
        # Call the users.list method using the built-in WebClient
        result = client.users_list()
        save_users(result["members"])
    except SlackApiError as e:
        logger.error("Error creating conversation: {}".format(e))


def save_users(users_array):
    """
    Save the fetched and active users to a file
    :param users_array: All users from users.list
    :return: None
    """
    for user in users_array:
        if not user["deleted"]:
            user_id = user["id"]
            # Store the entire user object
            users_store[user_id] = user["name"]
    # only user names
    save_to_file(users_store, "users.json")
    # all user info
    save_to_file(users_array, "users_all.json")


def getCountGetToKnow(project_id):
    """
    Gets the total number of possible replies
    :param project_id: Current project_id
    :return: count of all reply possibilities
    """
    intents_client = dialogflow.IntentsClient()
    parent = intents_client.project_agent_path(project_id)
    intents = intents_client.list_intents(parent)
    for intent in intents:
        if intent.display_name == DIALOGFLOW_INTENT_GETTOKNOW:
            length = int(str(intent.messages[0].text).count("\n"))
            return length


@app.message(":del")
def message_hello(message, say):
    """
    Listen to a message_event
    Used for deleting the saved chat history
    :param message: Message from the user
    :param say:
    :return: None
    """
    userids = re.findall(r"U\w*", message["text"])
    for userid in userids:
        if userid == message["user"]:
            if clear_messages(userid):
                say(f"Ich habe den Verlauf von <@{userid}> gelöscht.")
                new_sessionid(message["user"])
                save_to_file([user.__dict__ for user in users], OUTPUT_FILENAME)
                try:
                    gatherInfo[message["user"]].clear()
                except KeyError:
                    logging.error("No data")
            else:
                say(f"Ich konnte keinen Verlauf von <@{userid}> finden.")
        else:
            say(f"Du hast nicht die benötigten Berechtigungen um den Verlauf von <@{userid}> zu löschen.")


@app.message("")
def message_hello(message, say):
    """
    Listen to a message_event
    Message can contain anything
    Main function for handling the logic between Slack, Dialogflow and MiPinG
    :param message: Message from the user
    :param say:
    :return: None
    """
    logging.info("User: " + message["user"] + " wrote " + message['text'])
    clean_msg = clear_message(message["text"])
    logging.info("User: " + message["user"] + " wrote clean: " + clean_msg)

    # Check if messsage is valid for further processing
    if len(clean_msg) > 0:
        # Erzeuge users Datei
        fetch_users(app.client, app.logger)

        # Handle the user input
        handle_user_message(message["user"], clean_msg)

        # Prepare data for request
        data = '{"slackMessage":" ' + get_all_messages(message["user"]) + '"}'

        # Serialize users to JSON
        save_to_file([user.__dict__ for user in users], OUTPUT_FILENAME)

        # Random session id for not interupting the current session
        reply = detect_intent_texts(DIALOGFLOW_PROJECT_ID, random.randint(1, 100000), [clean_msg[:256]],
                                    DIALOGFLOW_LANGUAGE_CODE)

        # Checking if the conversation was ended by the user
        if reply[1] == "Goodbye":
            say(reply[0])
            # Clean up old data
            clear_dialogmessages(message["user"])
            # get new id
            new_sessionid(message["user"])
            save_to_file([user.__dict__ for user in users], OUTPUT_FILENAME)
            return

        # Welcome message if dialog messages is empty otherwise continue
        for user in users:
            if user.userId == message["user"]:
                if reply[1] == "Default Welcome Intent" and len(user.dialogMessages) == 0:
                    say(reply[0])
                    return

        logging.info("Total word count: " + str(get_message_length(message["user"])))

        # Got enough messages from the user
        # Getting big five and starting the conversation
        if get_message_length(message["user"]) >= LIMIT:
            logging.info("The user wrote a total of " + str(get_message_length(message["user"])) + " words.")
            # Get the big five for the current user
            for user in users:
                if user.userId == message["user"]:
                    if len(user.dialogMessages) == 0:
                        res = getBigFive(data)
                        addBigFive(message["user"], res)

            for user in users:
                if user.userId == message["user"]:
                    # Check if choosen big five value is above a certain value
                    if user.bigFive["big5_" + BIG_FIVE] >= HIGH_VALUE:
                        logging.info("High value of " + BIG_FIVE + ": " + str(user.bigFive["big5_" + BIG_FIVE]))
                        # check if this was reached before, if not trigger the event
                        # if high value -> low agreeableness
                        if len(user.dialogMessages) == 0:
                            say(detect_event_texts(DIALOGFLOW_PROJECT_ID, get_sessionid(message["user"]),
                                                   "abschluss_kennenlernen",
                                                   DIALOGFLOW_LANGUAGE_CODE))
                            reply = detect_event_texts(DIALOGFLOW_PROJECT_ID, get_sessionid(message["user"]),
                                                       "low_agreeableness",
                                                       DIALOGFLOW_LANGUAGE_CODE)
                            user.dialogMessages.append(reply)
                            say(reply)
                        # logic for the rest of the conversation paths
                        else:
                            reply = detect_intent_texts(DIALOGFLOW_PROJECT_ID,
                                                        get_sessionid(message["user"]), [clean_msg[:256]],
                                                        DIALOGFLOW_LANGUAGE_CODE)
                            user.dialogMessages.append(reply[0])
                            say(reply[0])
                            # end of conversation
                            # names of the fallback intents
                            if reply[1] == "schlecht - fallback" or reply[1] == "gut - fallback":
                                try:
                                    user.dialogMessages.clear()
                                    new_sessionid(message["user"])
                                    res = getBigFive(data)
                                    addBigFive(message["user"], res)
                                    logging.info("Cleared dialog messages and updated BigFive")
                                except KeyError:
                                    logging.error("No dialog messages")
                    else:
                        logging.info("Low value of " + BIG_FIVE + ": " + str(user.bigFive["big5_" + BIG_FIVE]))
                        # check if this was reached before, if not trigger the event
                        # if low value -> high agreeableness
                        if len(user.dialogMessages) == 0:
                            say(detect_event_texts(DIALOGFLOW_PROJECT_ID, get_sessionid(message["user"]),
                                                   "abschluss_kennenlernen",
                                                   DIALOGFLOW_LANGUAGE_CODE))
                            reply = detect_event_texts(DIALOGFLOW_PROJECT_ID, get_sessionid(message["user"]),
                                                       "high_agreeableness",
                                                       DIALOGFLOW_LANGUAGE_CODE)
                            user.dialogMessages.append(reply)
                            say(reply)
                        # logic for the rest of the conversation paths
                        else:
                            reply = detect_intent_texts(DIALOGFLOW_PROJECT_ID, get_sessionid(message["user"]),
                                                        [clean_msg[:256]],
                                                        DIALOGFLOW_LANGUAGE_CODE)
                            user.dialogMessages.append(reply[0])
                            say(reply[0])
                            # end of conversation
                            # names of the fallback intents
                            if reply[1] == "schlecht - fallback - fallback" or reply[1] == "gut - fallback - fallback":
                                try:
                                    user.dialogMessages.clear()
                                    new_sessionid(message["user"])
                                    res = getBigFive(data)
                                    addBigFive(message["user"], res)
                                    logging.info("Cleared dialog messages, updated BigFive")
                                except KeyError:
                                    logging.error("No dialog messages")

            save_to_file([user.__dict__ for user in users], OUTPUT_FILENAME)

        # Get more input from the user for a better big five prediction
        else:
            # welcome message
            if get_message_count(message["user"]) == 1 or get_intent(DIALOGFLOW_PROJECT_ID,
                                                                     get_sessionid(message["user"]),
                                                                     [clean_msg[:256]],
                                                                     DIALOGFLOW_LANGUAGE_CODE) == "Default Welcome Intent":
                say(detect_event_texts(DIALOGFLOW_PROJECT_ID, get_sessionid(message["user"]), "Welcome",
                                       DIALOGFLOW_LANGUAGE_CODE))
            # get more input from the user
            elif get_message_count(message["user"]) >= 2 and not get_intent(DIALOGFLOW_PROJECT_ID,
                                                                            get_sessionid(message["user"]),
                                                                            [clean_msg[:256]],
                                                                            DIALOGFLOW_LANGUAGE_CODE) == "Default Welcome Intent":
                # trigger event
                answer = detect_event_texts(DIALOGFLOW_PROJECT_ID, get_sessionid(message["user"]), "MoreInput",
                                            DIALOGFLOW_LANGUAGE_CODE)
                # logic for random answers
                key = message["user"]
                gatherInfo.setdefault(key, [])
                while True:
                    # compare count saved replies with count all replies
                    if len(gatherInfo[key]) >= getCountGetToKnow(AGENT_TALK):
                        break
                    elif answer in gatherInfo[key]:
                        answer = detect_event_texts(DIALOGFLOW_PROJECT_ID, get_sessionid(message["user"]), "MoreInput",
                                                    DIALOGFLOW_LANGUAGE_CODE)
                    else:
                        gatherInfo[key].append(answer)
                        break
                say(answer)
        save_to_file([user.__dict__ for user in users], OUTPUT_FILENAME)
    else:
        logging.info("User: " + message["user"] + " message was too short.")


def detect_event_texts(project_id, session_id, event, language_code):
    """
    Dialogflow: Triggers intent by event
    :param project_id: dialogflow project id
    :param session_id: same id to allow continuation of conversations
    :param event: event to trigger
    :param language_code: language code
    :return: Fulfillment text for the event
    """
    session = session_client.session_path(project_id, session_id)
    event_input = dialogflow.types.EventInput(name=event, language_code=language_code)
    query_input = dialogflow.types.QueryInput(event=event_input)
    try:
        response = session_client.detect_intent(session=session, query_input=query_input)
    except InvalidArgument:
        raise
    return response.query_result.fulfillment_text


def detect_intent_texts(project_id, session_id, texts, language_code):
    """
    Dialogflow: Detect intent by input text. Return fulfillment text and intent display name
    :param project_id: dialogflow project id
    :param session_id: same id to allow continuation of conversations
    :param texts: Text to match with intents
    :param language_code: language code
    :return: fulfillment text and intent display name
    """
    session = session_client.session_path(project_id, session_id)
    for text in texts:
        text_input = dialogflow.types.TextInput(
            text=text, language_code=language_code)

        query_input = dialogflow.types.QueryInput(text=text_input)
        try:
            response = session_client.detect_intent(session=session, query_input=query_input)

        except InvalidArgument:
            raise
    return response.query_result.fulfillment_text, response.query_result.intent.display_name


def get_intent(project_id, session_id, texts, language_code):
    """
    Dialogflow: Detect intent by input text. Return intent display name
    :param project_id: dialogflow project id
    :param session_id: same id to allow continuation of conversations
    :param texts: Text to match with intents
    :param language_code: language code
    :return: fulfillment text and intent display name
    """
    session = session_client.session_path(project_id, session_id)
    for text in texts:
        text_input = dialogflow.types.TextInput(
            text=text, language_code=language_code)

        query_input = dialogflow.types.QueryInput(text=text_input)
        try:
            response = session_client.detect_intent(session=session, query_input=query_input)

        except InvalidArgument:
            raise
    return response.query_result.intent.display_name


# Starts Raffi
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, filemode="w", filename="raffi.log",
                        format="%(asctime)s - %(levelname)s - %(message)s", datefmt="%d-%m-%y %H:%M:%S")
    initial_import()
    Helper.loadEnvKey("GOOGLE_APPLICATION_CREDENTIALS")
    session_client = dialogflow.SessionsClient()
    app.start(port=int(Helper.loadEnvKey("PORT")))
