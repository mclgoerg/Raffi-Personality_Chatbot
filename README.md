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

To run the application
```bash
python3 main.py
```
