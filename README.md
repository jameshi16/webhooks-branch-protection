# Branch Protection

Too poor to afford Pro? Still need some sort of branch protection found in the Pro plan? If you've got [`ngrok`](https://ngrok.com/), and a cheap computer like a Raspberry Pi, this project _might_ be for you.

This project is built on Python 3.6.8, with the explicitly defined package versions in `requirements.txt`. Try to use a WCGI server instead of the development server (i.e. `python main.py`) in production.

## Pre-requisites

Please ensure you have `git` installed and linked on your system. In the deployment site, run `pip -r requirements.txt`.

## Configuration

The config file, `config.json` generally looks like this:
```json
{
	"secret": "you share this secret with Github's Webhook page, value is whatever you want",
	"repos": [
		{
			"name": "<org/personal name>/<repo>, like jameshi16/PTRPG",
			"branch": "branch name to protect. typically master or production or release",
			"url": "the HTTPS clone URL, or the SSH clone URL. e.g. git@github.com:jameshi16/PTRPG",
		}
	],
	"commit_user": {
		"name": "name of the user to commit the reverting changes to. does not have to be a real user",
		"email": "email of the user to commit the reverting changes to. does not have to be a real email"
	},
	"smtp": {
		"enabled": true,
		"host": "smtp server host",
		"port": 587,
		"username": "username@email.com",
		"password": "insert password here",
		"use_tls": true,
		"use_ssl": false
	},
	"notify_emails": ["list@email.com", "of@email.com", "emails@email.com", "to@email.com", "notify@email.com"]
}
```

### SMTP

The SMTP settings `use_tls` and `use_ssl` are used for STARTTLS or SSL SMTP server connections respectively. Consult your email provider's manuals to figure out which one is being used. To disable notifications, set `enabled` to `false`, which ignores the existence of the other SMTP settings.

```json
	...
	"smtp": {
		"enabled": false
	},
	...
```

#### Gmail

1. Disable secure app access through this [link](https://myaccount.google.com/lesssecureapps).
2. Use the following SMTP configuration:
    ```json
    "smtp": {
			"enabled": true,
			"host": "smtp.google.com",
			"port": 587,
			"username": "googleaccount@gmail.com",
			"password": "putpasswordhere",
			"use_tls": true
    }
		```

## Private Repositories

It is highly recommended that you setup cloning of private repositories over Deploy Keys rather than using a user's own SSH key, or personal access token.

### Using a Deploy key

Generate a SSH key and paste the public key portion in the deploy key setting within the repository of your choice. Remember to check the `Write access` checkbox so that the webhook can automatically revert the errornous commits.

1. On the server where this script will be run, place the private key in to the `~/.ssh` folder.
2. Test if you can clone a repository using the normal `git clone` command.
3. If Step 2 is successful, the "URL" field in the configuration should be: `git@github.com:<username/org name>/<repo>.git`

### Using a personal access token

Generate a personal access token through your personal account, or through a [machine user](https://developer.github.com/v3/guides/managing-deploy-keys/#deploy-keys).

1. This [shortcut](https://github.com/settings/tokens) should bring you to the personal access tokens page
2. The "URL" field in the configuration should be: `https://<username>:<access token>@github.com/<username/org name>/<repo>.git` 
