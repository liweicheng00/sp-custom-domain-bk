import requests
from app.config import settings


class SlackNotification:

    def __init__(self, url: str):
        self.slack_webhook = url

    @staticmethod
    def error_info(text, error_msg):
        return {
            "username": "O2meta-backend-bot",
            "icon_emoji": ":boom:",
            "attachments": [
                {
                    "blocks": [
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": f"Error !!!!![{settings.runtime_env}]",
                                "emoji": True
                            }
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "plain_text",
                                "text": f"{text}"
                            }
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "plain_text",
                                "text": f"error msg: {error_msg}"
                            }
                        }
                    ]
                }
            ]
        }

    @staticmethod
    def system_info(text):
        return {
            "username": "O2meta-backend-bot",
            "icon_emoji": ":white_check_mark:",
            "attachments": [
                {
                    "blocks": [
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": f"Info[{settings.runtime_env}]",
                                "emoji": True
                            }
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "plain_text",
                                "text": f"{text}"
                            }
                        }
                    ]
                }
            ]
        }

    def system_error(self, text, e):
        data = self.error_info(text, str(e))
        requests.post(self.slack_webhook, json=data)

    def system_notify(self, text):
        data = self.system_info(text)
        requests.post(self.slack_webhook, json=data)


slack = SlackNotification(settings.slack_notification_webhook)
