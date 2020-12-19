import json
import os
import re
import random
#from sys import path
import sys

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

users = []
test = {}

RE_EMOJI = re.compile('\s*:[^:\s]*(?:::[^:\s]*)*:')
RE_MENTION = re.compile("\s*<@\w*>")
RE_USERID = re.compile("@\w*")

BIG_FIVE = Helper.loadEnvKey("BIG_FIVE").lower()

DIALOGFLOW_PROJECT_ID = Helper.loadEnvKey("DIALOGFLOW_PROJECT_ID")
DIALOGFLOW_LANGUAGE_CODE = Helper.loadEnvKey("DIALOGFLOW_LANGUAGE_CODE")


def strip_message(text):
    """
    @param text:
    @return:
    """
    # remove all whitespaces (space, tab, newline, return, formfeed)
    tmpstr = " ".join(text.split())
    # remove mentions
    tmpstr = RE_MENTION.sub(r"", tmpstr)
    # remove emojis
    tmpstr = RE_EMOJI.sub(r'', tmpstr)

    return tmpstr


def initial_import():
    if os.path.isfile("output.json"):
        with open("output.json") as f:
            data = json.load(f)
        print(data)

        for user in data:
            users.append(User(**user))

        print([user.__dict__ for user in users])
    else:
        print("File is not readable or missing, creating file...")
        open("output.json", "w")


def handle_user_message(userid, chat_text):
    global users
    if users:
        for user in users:
            if userid == user.userId:
                # user.messages.append(message["text"])
                user.messages.append(chat_text)
                break
        else:
            users.append(User(userid, [chat_text], [], {}, random.randint(1, 100000)))
    else:
        users = [User(userid, [chat_text], [], {}, random.randint(1, 100000))]


def handle_user_dialog(userid, dialog_text):
    global users
    if users:
        for user in users:
            if userid == user.userId:
                user.dialogMessages.append(dialog_text)
                break
        else:
            users.append(User(userid, [], [dialog_text], {}, random.randint(1, 100000)))
    else:
        users = [User(userid, [], [dialog_text], {}, random.randint(1, 100000))]


def addBigFive(userid, bigFive):
    for user in users:
        if userid == user.userId:
            user.bigFive = bigFive


def get_message_length(userid):
    for user in users:
        if userid == user.userId:
            return len(" ".join(user.messages).split())


def get_all_messages(userid):
    for user in users:
        if userid == user.userId:
            return " ".join(user.messages)


def get_message_count(userid):
    for user in users:
        if userid == user.userId:
            print(len(user.messages))
            return len(user.messages)


def write_json(data, filename='output.json'):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)


def clear_messages(userid):
    for user in users:
        if userid == user.userId and len(user.messages) != 0:
            print(user.messages)
            user.messages.clear()
            try:
                user.bigFive.clear()
            except KeyError:
                print("No Big Five Data")
            try:
                user.dialogMessages.clear()
            except KeyError:
                print("No dialog messages")
            return True
    return False


def clear_dialogmessages(userid):
    for user in users:
        if userid == user.userId:
            try:
                user.dialogMessages.clear()
            except KeyError:
                print("No dialog messages")


def get_sessionid(userid):
    for user in users:
        if userid == user.userId:
            return user.lastSessionId


def new_sessionid(userid):
    for user in users:
        if userid == user.userId:
            user.lastSessionId = random.randint(1, 100000)
            return user.lastSessionId


def save_to_file(content, filename):
    with open(filename, mode='w') as f:
        f.write(json.dumps(content, indent=4, ensure_ascii=False))


# Listen to the team_join event to hear when a
# user joins a workspace your app is installed on
@app.event("team_join")
def team_join(body, client, logger, say):
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


users_store = {}


# Fetch users using the users.list method
def fetch_users(client, logger):
    try:
        # Call the users.list method using the built-in WebClient
        # users.list requires the users:read scope
        result = client.users_list()
        save_users(result["members"])

    except SlackApiError as e:
        logger.error("Error creating conversation: {}".format(e))


# Put users into the dict
def save_users(users_array):
    for user in users_array:
        if not user["deleted"]:
            # Key user info on their unique user ID
            user_id = user["id"]
            # Store the entire user object (you may not need all of the info)
            users_store[user_id] = user["name"]

    save_to_file(users_store, "users.json")
    save_to_file(users_array, "users_all.json")


@app.message(":del")
# @app.message(re.compile("".del\s<@\w*>"))
def message_hello(message, say):
    print(message["text"])
    ids = re.findall(r"U\w*", message["text"])
    for id in ids:
        if id == message["user"]:
            print(id)
            if clear_messages(id):
                say(f"Ich habe den Verlauf von <@{id}> gelöscht.")
                new_sessionid(message["user"])
                save_to_file([user.__dict__ for user in users], "output.json")
                try:
                    test[message["user"]].clear()
                except KeyError:
                    print("No data")
            else:
                say(f"Ich konnte keinen Verlauf von <@{id}> finden.")
        else:
            say(f"Du hast nicht die benötigten Berechtigungen um den Verlauf von <@{id}> zu löschen.")


# Listens to incoming messages that contain anything
@app.message("")
def message_hello(message, say):
    # print(data)
    print(message)
    print(message['user'])
    print("User msg: " + message['text'])
    # SESSION_ID = message['user']
    clean_msg = strip_message(message['text'])
    print("Clean msg: " + clean_msg)
    requestURL = Helper.loadEnvKey("URL")
    if len(clean_msg) > 0:
        # Erzeuge users Datei
        fetch_users(app.client, app.logger)
        # say() sends a message to the channel where the event was triggered
        # say("Hi" + message['user'])
        # say(f"Hey there <@{message['user']}>!")
        handle_user_message(message["user"], clean_msg)

        json_string = json.dumps([user.__dict__ for user in users], ensure_ascii=False).encode("utf-8")
        print(json_string.decode())

        # detect_intent_texts(DIALOGFLOW_PROJECT_ID, SESSION_ID, [clean_msg], DIALOGFLOW_LANGUAGE_CODE)

        # say(detect_intent_texts(DIALOGFLOW_PROJECT_ID, SESSION_ID, [clean_msg], DIALOGFLOW_LANGUAGE_CODE))

        data = '{"slackMessage":" ' + get_all_messages(message["user"]) + '"}'

        with open('output.json', mode='w') as f:
            f.write(json.dumps([user.__dict__ for user in users], indent=4, ensure_ascii=False))

        reply = detect_intent_texts(DIALOGFLOW_PROJECT_ID, random.randint(1, 100000), [clean_msg[:256]],
                                    DIALOGFLOW_LANGUAGE_CODE)
        if reply[1] == "Goodbye":
            say(reply[0])
            clear_dialogmessages(message["user"])
            new_sessionid(message["user"])
            save_to_file([user.__dict__ for user in users], "output.json")
            return
        for user in users:
            if user.userId == message["user"]:
                if reply[1] == "Default Welcome Intent" and len(user.dialogMessages) == 0:
                    say(reply[0])
                    return
        """
        else:
            with open('output.json') as feedjson:
                feeds = json.load(feedjson)
            feeds.append(outp)
            with open('output.json', mode='w') as f:
                f.write(json.dumps(outp, indent=4))
        """

        # write_json(json.dumps([user.__dict__ for user in users], indent=4, sort_keys=False))
        # json_objects = [user.to_json() for user in users]
        # print(json_objects)

        """
        user_getter = attrgetter('userId')
        if users:
            if user_getter((user for user in users)) is not None:
                user_getter(user for user in users).append(message["text"])
            else:
                users.append(User(message["user"], [message["text"]]))
        else:
            users = [User(message["user"], [message["text"]])]
        # for user in users:
        #    if message["user"] not in user
        #if User.userId(message["user"]) not in users:
        #    users.append(User(message["user"], [message["text"]]))
    
        print(users)
        """
        print("DEBUG: Anzahl der Wörter: " + str(get_message_length(message["user"])))
        if get_message_length(message["user"]) >= 200:

            print("DEBUG: Du hast " + str(get_message_length(message["user"])) + " Wörter geschrieben.")

            for user in users:
                if user.userId == message["user"]:
                    if len(user.dialogMessages) == 0:
                        try:
                            #response = requests.post('http://localhost:9200/slackpost', headers=headers,
                            #                         data=data.encode("utf-8"),
                            #                         verify=False)
                            response = requests.post(requestURL, headers=headers,
                                                     data=data.encode("utf-8"),
                                                     verify=False)
                        except requests.exceptions.RequestException as e:
                            print(e)
                            sys.exit(1)

                        result = json.loads(response.content.decode("utf-8"))
                        print(result)
                        # with open("data.json", "w") as outfile:
                        #      json.dump(result, outfile)
                        print(json.dumps(result, indent=4, sort_keys=True))
                        result.pop("wordCount", None)

                        addBigFive(message["user"], result)
                        print([user.__dict__ for user in users])


            for user in users:
                if user.userId == message["user"]:

                    if user.bigFive["big5_" + BIG_FIVE] >= 0.6:
                        print("hoher wert " + BIG_FIVE + ": " + str(user.bigFive["big5_" + BIG_FIVE]))
                        if len(user.dialogMessages) == 0:
                            say(detect_event_texts(DIALOGFLOW_PROJECT_ID, get_sessionid(message["user"]),
                                                   "abschluss_kennenlernen",
                                                   DIALOGFLOW_LANGUAGE_CODE))
                            reply = detect_event_texts(DIALOGFLOW_PROJECT_ID, get_sessionid(message["user"]),
                                                       "low_agreeableness",
                                                       DIALOGFLOW_LANGUAGE_CODE)
                            user.dialogMessages.append(reply)
                            say(reply)
                        else:
                            reply = detect_intent_texts(DIALOGFLOW_PROJECT_ID,
                                                        get_sessionid(message["user"])[clean_msg[:256]],
                                                        DIALOGFLOW_LANGUAGE_CODE)
                            user.dialogMessages.append(reply[0])
                            say(reply[0])

                            if reply[1] == "schlecht - fallback" or reply[1] == "gut - fallback":
                                try:
                                    user.dialogMessages.clear()
                                    new_sessionid(message["user"])
                                    try:
                                        #response = requests.post('http://localhost:9200/slackpost', headers=headers,
                                        #                         data=data.encode("utf-8"),
                                        #                         verify=False)
                                        response = requests.post(requestURL, headers=headers,
                                                                 data=data.encode("utf-8"),
                                                                 verify=False)
                                    except requests.exceptions.RequestException as e:
                                        print(e)
                                        sys.exit(1)

                                    result = json.loads(response.content.decode("utf-8"))
                                    print(result)
                                    print(json.dumps(result, indent=4, sort_keys=True))
                                    result.pop("wordCount", None)

                                    addBigFive(message["user"], result)
                                    print("Cleared dialog messages, updated BigFive")
                                    print([user.__dict__ for user in users])
                                except KeyError:
                                    print("No dialog messages")
                    else:
                        print("niedriger wert " + BIG_FIVE + ": " + str(user.bigFive["big5_" + BIG_FIVE]))
                        if len(user.dialogMessages) == 0:
                            say(detect_event_texts(DIALOGFLOW_PROJECT_ID, get_sessionid(message["user"]),
                                                   "abschluss_kennenlernen",
                                                   DIALOGFLOW_LANGUAGE_CODE))
                            reply = detect_event_texts(DIALOGFLOW_PROJECT_ID, get_sessionid(message["user"]),
                                                       "high_agreeableness",
                                                       DIALOGFLOW_LANGUAGE_CODE)
                            user.dialogMessages.append(reply)
                            say(reply)
                        else:
                            reply = detect_intent_texts(DIALOGFLOW_PROJECT_ID, get_sessionid(message["user"]),
                                                        [clean_msg[:256]],
                                                        DIALOGFLOW_LANGUAGE_CODE)
                            user.dialogMessages.append(reply[0])
                            say(reply[0])

                            if reply[1] == "schlecht - fallback - fallback" or reply[1] == "gut - fallback - fallback":
                                try:
                                    user.dialogMessages.clear()
                                    new_sessionid(message["user"])
                                    try:
                                        #response = requests.post('http://localhost:9200/slackpost', headers=headers,
                                        #                         data=data.encode("utf-8"),
                                        #                         verify=False)
                                        response = requests.post(requestURL, headers=headers,
                                                                 data=data.encode("utf-8"),
                                                                 verify=False)
                                    except requests.exceptions.RequestException as e:
                                        print(e)
                                        sys.exit(1)

                                    result = json.loads(response.content.decode("utf-8"))
                                    print(result)
                                    print(json.dumps(result, indent=4, sort_keys=True))
                                    result.pop("wordCount", None)

                                    addBigFive(message["user"], result)
                                    print("Cleared dialog messages, updated BigFive")
                                    print([user.__dict__ for user in users])
                                except KeyError:
                                    print("No dialog messages")

            save_to_file([user.__dict__ for user in users], "output.json")

        else:
            if get_message_count(message["user"]) == 1 or get_intent(DIALOGFLOW_PROJECT_ID,
                                                                     get_sessionid(message["user"]),
                                                                     [clean_msg[:256]],
                                                                     DIALOGFLOW_LANGUAGE_CODE) == "Default Welcome Intent":
                say(detect_event_texts(DIALOGFLOW_PROJECT_ID, get_sessionid(message["user"]), "Welcome",
                                       DIALOGFLOW_LANGUAGE_CODE))
            elif get_message_count(message["user"]) >= 2 and not get_intent(DIALOGFLOW_PROJECT_ID,
                                                                            get_sessionid(message["user"]),
                                                                            [clean_msg[:256]],
                                                                            DIALOGFLOW_LANGUAGE_CODE) == "Default Welcome Intent":

                answer = detect_event_texts(DIALOGFLOW_PROJECT_ID, get_sessionid(message["user"]), "MoreInput",
                                            DIALOGFLOW_LANGUAGE_CODE)
                key = message["user"]
                test.setdefault(key, [])
                while True:
                    if len(test[key]) >= 13:
                        break
                    elif answer in test[key]:
                        print("ist vorhanden")
                        answer = detect_event_texts(DIALOGFLOW_PROJECT_ID, get_sessionid(message["user"]), "MoreInput",
                                                    DIALOGFLOW_LANGUAGE_CODE)
                    else:
                        print("ist noch nicht vorhanden")
                        test[key].append(answer)
                        break

                print(test)
                say(answer)
        save_to_file([user.__dict__ for user in users], "output.json")

    else:
        print("Message war zu kurz")


def detect_event_texts(project_id, session_id, event, language_code):
    session = session_client.session_path(project_id, session_id)
    event_input = dialogflow.types.EventInput(name=event, language_code=language_code)
    query_input = dialogflow.types.QueryInput(event=event_input)
    try:
        response = session_client.detect_intent(session=session, query_input=query_input)

    except InvalidArgument:
        raise

    print('=' * 20)
    print('Query text: {}'.format(response.query_result.query_text))
    print('Detected intent: {} (confidence: {})\n'.format(
        response.query_result.intent.display_name,
        response.query_result.intent_detection_confidence))
    print('Fulfillment text: {}\n'.format(
        response.query_result.fulfillment_text))
    return response.query_result.fulfillment_text


def detect_intent_texts(project_id, session_id, texts, language_code):
    """Returns the result of detect intent with texts as inputs.
    Using the same `session_id` between requests allows continuation
    of the conversation."""

    session = session_client.session_path(project_id, session_id)
    print('Session path: {}\n'.format(session))

    for text in texts:
        text_input = dialogflow.types.TextInput(
            text=text, language_code=language_code)

        query_input = dialogflow.types.QueryInput(text=text_input)
        try:
            response = session_client.detect_intent(session=session, query_input=query_input)

        except InvalidArgument:
            raise

        print('=' * 20)
        print('Query text: {}'.format(response.query_result.query_text))
        print('Detected intent: {} (confidence: {})\n'.format(
            response.query_result.intent.display_name,
            response.query_result.intent_detection_confidence))
        print('Fulfillment text: {}\n'.format(
            response.query_result.fulfillment_text))
        # print(response.query_result)

    return response.query_result.fulfillment_text, response.query_result.intent.display_name


def get_intent(project_id, session_id, texts, language_code):
    session = session_client.session_path(project_id, session_id)
    print('Session path: {}\n'.format(session))

    for text in texts:
        text_input = dialogflow.types.TextInput(
            text=text, language_code=language_code)

        query_input = dialogflow.types.QueryInput(text=text_input)
        try:
            response = session_client.detect_intent(session=session, query_input=query_input)

        except InvalidArgument:
            raise

        print('=' * 20)
        print('Query text: {}'.format(response.query_result.query_text))
        print('Detected intent: {} (confidence: {})\n'.format(
            response.query_result.intent.display_name,
            response.query_result.intent_detection_confidence))
        print('Fulfillment text: {}\n'.format(
            response.query_result.fulfillment_text))

    return response.query_result.intent.display_name


# Start your app
if __name__ == "__main__":
    initial_import()
    Helper.loadEnvKey("GOOGLE_APPLICATION_CREDENTIALS")
    session_client = dialogflow.SessionsClient()
    app.start(port=int(Helper.loadEnvKey("PORT")))
