from github_webhook import Webhook
from flask import Flask, make_response, request
from json import JSONDecodeError
from protected_repo import ProtectedRepository
from threading import Thread
from mail import Email, FakeEmail
import json
import os

basepath = os.path.dirname(__file__)
CONFIG_FILE = "config.json"

def load_config(filename):
	config = {
		"secret": "",
		"repos": [],
		"commit_user": {
			"name": "Branch Protection",
			"email": "branch_protection@noreply.com"	
		},
		"smtp": {
			"enabled": False,
		},
		"notify_emails": []
	}
	try:
		user_config = json.load(open(os.path.join(basepath, filename), mode='r'))
		config.update(user_config)
		return config
	except JSONDecodeError as e:
		print("cannot properly parse config file.\n", e)
		exit(1)
	except FileNotFoundError as e:
		print("cannot find config file. create one in config.json\n", e)
		exit(1)

def is_github_merge(config, commit):
	committer = commit['committer']
	bot_user = config['commit_user']
	return ((committer['name'] == bot_user['name'] and committer['email'] == bot_user['email']) or
					(committer['name'] == "GitHub" and committer['email'] == "noreply@github.com" and committer['username'] == "web-flow"))

def handle_bad_commit(config, request_id, commit, protected_repo, mail):
	print("{:s}: Performing corrective actions...".format(request_id))
	protected_repo.pull()
	protected_repo.push(protected_repo.last_good_commit())

	email_addresses = config['notify_emails']
	subject = 'Branch Protection Notification'
	body = """
		Repo `{:s}` with Protected Branch `{:s}` was pushed to. The action has been automagically reverted.

		Commit details
		==============
		SHA:     \t{:s}
		User:    \t{:s}
		Email:   \t{:s}
		Message: \t{:s}
	""".format(protected_repo.name, protected_repo.branch, commit["id"], commit["author"]["name"], commit["author"]["email"], commit["message"])

	mail.send_notification(email_addresses, subject, body)

config = load_config(CONFIG_FILE)
app = Flask(__name__)
webhook = Webhook(app, secret='' if 'secret' not in config else config['secret'])
repository_maps = [] if 'repos' not in config else config['repos']
mail = FakeEmail()
if config['smtp'] != {} and config['smtp']['enabled']:
	host = config['smtp']['host']
	port = config['smtp']['port']
	username = config['smtp']['username']
	password = config['smtp']['password']
	use_tls = False if 'use_tls' not in config['smtp'] else config['smtp']['use_tls']
	use_ssl = False if 'use_ssl' not in config['smtp'] else config['smtp']['use_ssl']

	mail = Email(host, port, username, password, smtp_tls=use_tls, smtp_ssl=use_ssl)

# Protected Repository object per repository_map
for repository_map in repository_maps:
	name = repository_map['name']
	path = os.path.join(basepath, '.cache/', name.lower().replace('/', '_'))
	branch = repository_map['branch']
	url = repository_map['url']
	commit_user_name = config['commit_user']['name']
	commit_user_email = config['commit_user']['email']

	repo = ProtectedRepository(name, path, url, branch)
	repo.set_committer(commit_user_name, commit_user_email)
	repo.set_author(commit_user_name, commit_user_email)

	repository_map['repo'] = repo

@webhook.hook()
def on_push(data):
	# get the request id. if we can't get it, don't bother serving the request
	request_id = request.headers.get('X-GitHub-Delivery')
	if not request_id:
		print("Request with no request ID")
		return make_response("No request ID. Ignored.", 302)

	try:
		# Find a matching repository
		repo = {}
		for known_repo in repository_maps:
			if data['repository']['full_name'] == known_repo['name']:
				repo = known_repo
				break

		if repo == {}:
			print("{:s} Remote repository {:s} not configured".format(request_id, data['repository']['full_name']))
			return make_response("Unconfigured repository, no action taken", 400)

		# Match the branches
		ref = data['ref']	
		branch = ref.split(sep='/')[-1]
		if branch != repo['branch']:
			return make_response("Unaffected branch", 204)

		# Get latest commit from webhook
		if 'head_commit' not in data:
			print("{:s}: request does not have head commit".format(request_id))
			return make_response("No head commit", 400)
		commit = data['head_commit']

		# If the latest commit is a Github merge, we're good
		if is_github_merge(config, commit):
			print("Latest commit is a merge request. All good.")
			return make_response("Is merge. All good.", 204)

		# Oh no, it's not a Gitub merge?
		Thread(target=handle_bad_commit, args=(config, request_id, commit, repo['repo'], mail)).start()

	except KeyError as e:
		print("KeyError when processing hooks\n", e)
		return make_response("Can't get the required fields from the data", 400)

if __name__ == "__main__":
	app.run(host="0.0.0.0", port=8080)
