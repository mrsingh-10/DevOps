# This code sample uses the 'requests' library:
# http://docs.python-requests.org
import json
from logging.config import dictConfig

import requests
from flask import Flask, request
from requests.auth import HTTPBasicAuth

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})
app = Flask(__name__)

# Define a route that handles GET requests
@app.route('/createJira', methods=['POST'])
def createJira():
    data = request.get_json()

    if "action" not in data or data["action"] != "created":
        app.logger.info(f"NOOP, not a new comment!")
        res = noop()
        return res

    if "comment" not in data:
        app.logger.info("No comment key in the payload")
        return wrong_payload()
    
    if "issue" not in data:
        app.logger.info("No issue key in the payload")
        return wrong_payload()
    
    if "sender" not in data:
        app.logger.info("No sender key in the payload")
        return wrong_payload()
    
    comment = data["comment"]["body"]

    issue_title = data["issue"]["title"]
    html_url = data["issue"]["html_url"]
    
    sender = data["sender"]["login"]
    
        
    app.logger.info(f"Comment: {comment}")
    app.logger.info(f"Issue: {issue_title} @ {html_url}")
    app.logger.info(f"Sender: {sender}")

    #app.logger.info(json.dumps(data))
    if "/jira" not in comment:
        app.logger.info(f"NOOP")
        return noop()
        
    app.logger.info(f"Creating new Jira Story...")
    response = post_to_jira(sender, issue_title, html_url, comment)
    formated = json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": "))
    app.logger.info(f"Response from Jira API with Status:{response.status_code} and Text:{formated}")
    

    return formated

def post_to_jira(sender, issue_title, issue_link, comment):
    auth = HTTPBasicAuth(AUTH_EMAIL, API_TOKEN)

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    #app.logger.info(f"Before payload...")
    payload = json.dumps({
        "fields": {
            "description": {
                "content": [
                    {
                        "content": [
                            {
                            "text": "Issue [",
                            "type": "text"
                            },
                            {
                            "marks": [
                                {
                                "attrs": {
                                    "href": issue_link
                                },
                                "type": "link"
                                }
                            ],
                            "text": "GitHub-Link",
                            "type": "text"
                            },
                            {
                            "text": "]: "+str(issue_title),
                            "type": "text"
                            }
                        ],
                        "type": "paragraph"
                    },
                    {
                        "content": [
                            {
                            "text": "Comment: "+str(comment),
                            "type": "text"
                            }
                        ],
                        "type": "paragraph"
                        },
                    ],
                "type": "doc",
                "version": 1
            },
            "project": {
            "key": JIRA_PROJECT_KEY
            },
            "issuetype": {
                "id": "10006"
            },
            "summary": f"{sender} pointed an Issue",
        },
        "update": {}
    })

    #app.logger.info(f"---Payload\n{payload}\n")
    
    response = requests.request(
        "POST",
        JIRA_PROJECT_URL,
        data=payload,
        headers=headers,
        auth=auth
    )

    return response

def noop():
    response = app.response_class(
        response=json.dumps("Nothing to do."),
        status=200,
        mimetype='application/json'
    )
    
    return response

def wrong_payload():
    response = app.response_class(
        response=json.dumps("Wrong Payload."),
        status=400,
        mimetype='application/json'
    )
    return response


JIRA_PROJECT_URL=""
JIRA_PROJECT_KEY=""

# [TODO: add to env vars]
API_TOKEN=""
AUTH_EMAIL=""

if __name__ == '__main__':
    if JIRA_PROJECT_URL == "" or JIRA_PROJECT_KEY=="" or API_TOKEN=="" or AUTH_EMAIL =="":
        print("ERROR: Update the global jira variables in the file.")
        exit(1)
    app.run(host='0.0.0.0', port=5000, debug=True)