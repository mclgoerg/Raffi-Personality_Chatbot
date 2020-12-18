class User:
    userId: str
    messages: [str]
    dialogMessages: [str]
    bigFive: str
    lastSessionId: int

    def __init__(self, userId, messages, dialogMessages, bigFive, lastSessionId):
        self.userId = userId
        self.messages = messages
        self.dialogMessages = dialogMessages
        self.bigFive = bigFive
        self.lastSessionId = lastSessionId