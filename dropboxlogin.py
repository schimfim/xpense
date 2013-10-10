from dboxauth import app_key, app_secret, access_type

import webbrowser
from dropbox import client, rest, session
#import keychain
import pickle
#import console

def get_password():
	try:
		with open('dboxtoken.py') as f:
			pwd = pickle.load(f)
	except IOError:
		pwd = None
	return pwd

def set_password(token):
	with open('dboxtoken.py', 'w') as f:
		pickle.dump(token, f)

def get_request_token():
	#console.clear()
	print 'Getting request token...'
	sess = session.DropboxSession(app_key, app_secret, access_type)
	request_token = sess.obtain_request_token()
	url = sess.build_authorize_url(request_token)
	#console.clear()
	webbrowser.open(url)
	raw_input('Press return when done with browser')
	return request_token

def get_access_token():
	token_str = get_password()
	if token_str:
		key, secret = pickle.loads(token_str)
		return session.OAuthToken(key, secret)
	request_token = get_request_token()
	sess = session.DropboxSession(app_key, app_secret, access_type)
	access_token = sess.obtain_access_token(request_token)
	token_str = pickle.dumps((access_token.key, access_token.secret))
	set_password(token_str)
	return access_token

def get_client():
	access_token = get_access_token()
	sess = session.DropboxSession(app_key, app_secret, access_type)
	sess.set_token(access_token.key, access_token.secret)
	dropbox_client = client.DropboxClient(sess)
	return dropbox_client

def main():
	# Demo if started run as a script...
	# Just print the account info to verify that the authentication worked:
	print 'Getting account info...'
	dropbox_client = get_client()
	account_info = dropbox_client.account_info()
	print 'linked account:', account_info

if __name__ == '__main__':
    main()
