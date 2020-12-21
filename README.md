# Raffi - Personality Adaptive Chatbot

Raffi is a Python application for a personality adaptive conversation.
It uses Slack, Dialogflow and [MiPinG](https://github.com/mclgoerg/MiningPersonalityInGerman). It is forked from the
[repo](https://github.com/iUssel/MiningPersonalityInGerman) and improved to analyse any string message.

## Installation

Install python3.8, virtual environment and pip

```bash
sudo apt install python3.8
sudo apt update
sudo apt install python3.8-venv
sudo apt install python3-pip
pip install pip --upgrade
```

Create the virtual environment and activate it
```bash
python3.8 -m venv tutorial-env
source tutorial-env/bin/activate
```
Clone this repo on the same VM as MiPinG

```bash
git clone https://github.com/mclgoerg/Raffi-Personality_Chatbot.git
```

Navigate in the directory and install the requirements
```bash
cd Raffi-Personality_Chatbot/
pip install .
```

Rename .env.example to .env  
Fill the .env  
Below is an example with explanation

```bash
# Slack
SLACK_SIGNING_SECRET=
SLACK_BOT_TOKEN=

#ngrok
PORT=3000

#BigFive Dimension
## agreeableness, conscientiousness, extraversion, neuroticism, openness
BIG_FIVE=
# decimal between 0 and 1
HIGH_VALUE=0.6

#Dialogflow
DIALOGFLOW_PROJECT_ID=
## e.g.: de/en
DIALOGFLOW_LANGUAGE_CODE=
# Intent - GetToKnow
GETTOKNOW=
AGENT_TALK=
#Google
GOOGLE_APPLICATION_CREDENTIALS=private_key.json

#MiPing
URL=http://localhost:8000/slackpost

```

SLACK_SIGNING_SECRET and SLACK_BOT_TOKEN are both from the slack API  

PORT 3000 is default for ngrok  

BIG_FIVE choose one value, the bot is low or high agreeable - this has to be changed in the code  

HIGH_VALUE can be any decimal (float) between 0 and 1

DIALOGFLOW_PROJECT_ID is the ID of the mega agent  

DIALOGFLOW_LANGUAGE_CODE de for german, en for english  

GETTOKNOW is the event for getting the user to know if the messages are below the limit




To run the application
```bash
python3 main.py
```
