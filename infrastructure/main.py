import json


def handler(event, context):
    """Placeholder Lambda function"""
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
        },
        "body": json.dumps(
            {
                "message": "Fitlog API placeholder - deploy your FastAPI code here",
                "event": event,
            }
        ),
    }
