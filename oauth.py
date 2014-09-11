#!/usr/bin/env python
import cgi
import cgitb
cgitb.enable()

try:
	from hashlib import md5 as getMD5
except:
	from md5 import md5 as getMD5
	
import random, datetime, os
import mysql.connector

try:
	import simplejson as json
except:
	import json

from credentials.cred import DATABASE, USER, PASSWORD

def formatString(string,**kwargs):
	for k,v in kwargs.items():
		string = string.replace('{%s}' % k,v)
	return string
		


def base32encode(number, alphabet='23456789ABCDEFGHJKLMNPQRSTUVWXYZ'):
	"""Converts an integer to a base32 string without 0,O,I,1"""
	if not isinstance(number, (int, long)):
		raise TypeError('number must be an integer')
	base32 = ''
	if 0 <= number < len(alphabet):
		return alphabet[number]
	while number != 0:
		number, i = divmod(number, len(alphabet))
		base32 = alphabet[i] + base32
	return base32

def generateLookup():
	from damm32 import damm32Encode
	base = base32encode(random.randint(32**6,(32**7)-1)) #Genereate a random number that will be converted into 7 digits
	return base + damm32Encode(base)
	#return ('00000000' + str(random.randint(0,99999999)))[-8:]

def checkLookup(lookup):
	from damm32 import damm32Check
	return damm32Check(lookup)

def generateMD5():
	return getMD5(str(random.randint(0,9999999999999999))).hexdigest()
	
def getTimestamp():
	return datetime.datetime.now()

def getServiceInfo(source):
	cnx = mysql.connector.connect(user=USER, password=PASSWORD, database=DATABASE)
	cursor = cnx.cursor()
	
	try:
		query = ('SELECT source,id,secret,code_var,token_var,token_resp,auth_url,code_url,code_data,exchange_url,use_state,icon FROM oauth_sources WHERE source = %s')
		cursor.execute(query, (source,))
		for row in cursor:
			return dict(zip(cursor.column_names,row))
		return None
	finally:
		cursor.close()
		cnx.close()

def getServiceInfoFromLookup(lookup):
	cnx = mysql.connector.connect(user=USER, password=PASSWORD, database=DATABASE)
	cursor = cnx.cursor()
	try:
		query = ('SELECT source FROM oauth WHERE lookup = %s')
		
		cursor.execute(query, (lookup,))
		source = None
		for (source,) in cursor:
			break
				
		if not source: return None
		return getServiceInfo(source)
			
	finally:
		cursor.close()
		cnx.close()

def handleAuth1(not_found=False,bad_lookup=False,arguments=None):
	print "Content-Type: text/html"
	print
	html = '''
		<html>
			<head>
				<style>
					input.rounded {
						border: 1px solid #333;
						-moz-border-radius: 10px;
						-webkit-border-radius: 10px;
						border-radius: 10px;
						-moz-box-shadow: 0px 0px 8px #999;
						-webkit-box-shadow: 0px 0px 8px #999;
						box-shadow: 0px 0px 8px #999;
						font-size: 100px;
						padding: 4px 7px;
						outline: 0;
						-webkit-appearance: none;
					}
					input.rounded:focus {
						border-color: #CC99CC;
					}
					body {
						background-color: black;
					}
				</style>
			</head>
			</body>
				<div style="width:100%;text-align:center;">
					<form action="oauth.py">
						<span style="font-family:Arial;font-size:100px;color:white;">ENTER CODE</span><br><br>
						<input type="text" maxlength="9" size="9" name="lookup" value="@VALUE@" class="rounded" style="text-transform:uppercase;font-family:monospace;">
						<input type="hidden" name="request" value="auth2">
					</form>
					<NOTFOUND />
				</div>
			</body>
		</html>
	'''

	if bad_lookup:
		lookup = ''
		if arguments and 'lookup' in arguments: lookup = arguments['lookup'].value
		print html.replace('<NOTFOUND />','<br><br><span style="font-family:Arial;font-size:50px;color:red;">CODE NOT ENTERED CORRECTLY</span>').replace('@VALUE@',lookup)
	elif not_found:
		lookup = ''
		if arguments and 'lookup' in arguments: lookup = arguments['lookup'].value
		print html.replace('<NOTFOUND />','<br><br><span style="font-family:Arial;font-size:50px;color:red;">CODE NOT FOUND</span>').replace('@VALUE@',lookup)
	else:
		print html.replace('<NOTFOUND />','').replace('@VALUE@','')

def checkForLookup(lookup):
	cnx = mysql.connector.connect(user=USER, password=PASSWORD, database=DATABASE)
	cursor = cnx.cursor()
	
	try:
		check = ("SELECT lookup FROM oauth WHERE lookup = %s LIMIT 1") 	
		cursor.execute(check, (lookup.upper(),))
		for c in cursor:
			return True
		return False
	finally:
		cursor.close()
		cnx.close()
		
def getRedirect(lookup,use_state=False):
	if use_state:
		return 'http://auth.2ndmind.com/cgi-bin/oauth.py'
	else:
		return 'http://auth.2ndmind.com/cgi-bin/oauth.py?request=processcode&lookup=%s' % lookup
	
def handleAuth2(arguments):
	if not 'lookup' in arguments:
		return show404()
	lookup = arguments['lookup'].value.replace('-','')
	if not checkLookup(lookup):
		return handleAuth1(bad_lookup=True,arguments=arguments)
	elif not checkForLookup(lookup):
		return handleAuth1(not_found=True,arguments=arguments)

	import urllib
	
	info = getServiceInfoFromLookup(lookup)
	redirect = getRedirect(lookup,info['use_state'])
	state = urllib.quote('request=processcode&lookup=%s' % lookup)
	url = formatString(info['auth_url'],redirect=urllib.quote(redirect,safe=''),cid=info['id'],state=state)
	
	print("Location:%s" % url)
	print # to end the CGI response headers.
	
def handleGetLookup(arguments):
	if not 'source' in arguments:
		return show404()
		
	source = arguments['source'].value
	key = arguments['key'].value
	lookup = generateLookup()
	md5 = generateMD5()
	timestamp = getTimestamp()

	cnx = mysql.connector.connect(user=USER, password=PASSWORD, database=DATABASE)
	cursor = cnx.cursor()
	
	try:

		addTokenEntry = (	
							"INSERT INTO oauth "
							"(lookup, md5, token, source, timestamp) "
							"VALUES (%s, %s, %s, %s, %s)"
		)
		
		data = (lookup, md5, '', source, timestamp)
	
		cursor.execute(addTokenEntry, data)
		
		cnx.commit()
	finally:
		cursor.close()
		cnx.close()
	
	import encryption
	
	print "Content-Type: application/json"
	print
	print encryption.encrypt(json.dumps({'lookup':lookup,'md5':md5}),key)
	
def handleSaveToken():
	print "Content-Type: text/plain"
	print
	print os.environ["REQUEST_URI"]

def handleProcessCode(arguments):
	if not 'lookup' in arguments:
		return show404()
	lookup = arguments['lookup'].value
	
	info = getServiceInfoFromLookup(lookup)
	
	code = arguments[info['code_var']].value
	
	import urllib

	redirect = getRedirect(lookup,info['use_state'])
	
	data = formatString(info['code_data'],cid=info['id'],csecret=info['secret'],code=code,redirect=redirect)
	req = urllib.urlopen(info['code_url'],data)

	token = extractToken(info,req)
	
	if token:
		token = exchangeToken(info,token)
		saveToken(lookup,token)
	elif token == None:
		print "Content-Type: text/plain"
		print
		print req.read()
		return
	else:
		return show500()
	
	print("Location:http://auth.2ndmind.com/cgi-bin/complete.py?source=%s" % info['source'])
	print # to end the CGI response headers.

def extractToken(info,req):
	if info['token_resp'] == 'json':
		json_str = req.read()
		json_dict = json.loads(json_str)
		return json_dict.get(info['token_var'])
	elif info['token_resp'] == 'urlencode':
		encoded = req.read()
		data = dict(cgi.parse_qsl(encoded))
		return data.get(info['token_var'])
	elif info['token_resp'] == 'url':
		return None
	else:
		return False

def exchangeToken(info,token):
	exchange_url = info.get('exchange_url')
	if not exchange_url:
		return token
	url = formatString(exchange_url,cid=info['id'],secret=info['secret'],token=token)
	
	import urllib
	req = urllib.urlopen(url)
	exchanged = extractToken(info,req)
	if not exchanged:
		return token
	return exchanged

def saveToken(lookup,token):
	cnx = mysql.connector.connect(user=USER, password=PASSWORD, database=DATABASE)
	cursor = cnx.cursor()
	
	try:
		addToken = (	"UPDATE oauth SET token = %s WHERE lookup = %s")
		
		data = (token,lookup)
	
		cursor.execute(addToken, data)
		
		cnx.commit()
	finally:
		cursor.close()
		cnx.close()

def handleGetToken(arguments):
	if not 'lookup' in arguments or not 'md5' in arguments:
		return show404()
	
	import encryption
	
	key = arguments['key'].value
	lookup = encryption.decrypt(arguments['lookup'].value)
	md5 = encryption.decrypt(arguments['md5'].value)
 
	cnx = mysql.connector.connect(user=USER, password=PASSWORD, database=DATABASE)
	cursor = cnx.cursor()
	try:
		query = ('SELECT token FROM oauth WHERE lookup = %s AND md5 = %s')
		
		cursor.execute(query, (lookup, md5))
		token = None
		for token in cursor:
			break
		
		if token: token = token[0]
		
		print "Content-Type: application/json"
		print
		if token == None:
			print encryption.encrypt(json.dumps({'status':'error'}),key)
		elif token:
			print encryption.encrypt(json.dumps({'status':'ready','token':token}),key)
			query = ("DELETE FROM "+DATABASE+".oauth WHERE oauth.lookup = %s")
			cursor.execute(query, (lookup,))
			_clearStaleEntries(cursor)
		else:
			print encryption.encrypt(json.dumps({'status':'waiting'}),key)
			
	finally:
		cursor.close()
		cnx.close()

def clearStaleEntries(cursor):
	cnx = mysql.connector.connect(user=USER, password=PASSWORD, database=DATABASE)
	cursor = cnx.cursor()
	try:
		_clearStaleEntries(cursor)
	finally:
		cursor.close()
		cnx.close()

def _clearStaleEntries(cursor):
	query = ("DELETE FROM "+DATABASE+".oauth WHERE oauth.timestamp < NOW() - INTERVAL 5 MINUTE")
	cursor.execute(query)
	
def show404():
	print("Status:401")
	print # to end the CGI response headers.
	
def show500():
	print("Status:500")
	print # to end the CGI response headers.

def main():
	arguments = cgi.FieldStorage()
	request = None
	if 'request' in arguments: request = arguments['request'].value
	
	if not request or not request in ('auth1','auth2','getlookup','savetoken','processcode','gettoken'):
		if 'state' in arguments:
			import urllib
			state = urllib.unquote(arguments['state'].value)
			arguments2 = dict(cgi.parse_qsl(state))
			
			class FakeFS(object):
				def __init__(self,val):
					self.value = val
					
			for k in arguments2.keys():
				v = arguments2[k]
				arguments2[k] = FakeFS(v)
			request = arguments2['request'].value
			for k in arguments:
				arguments2[k] = arguments[k]
			arguments = arguments2
		else:
			return show404()

	if request == 'auth1':
		handleAuth1()
	if request == 'auth2':
		handleAuth2(arguments)
	elif request == 'getlookup':
		handleGetLookup(arguments)
	elif request == 'savetoken':
		handleSaveToken()
	elif request == 'processcode':
		handleProcessCode(arguments)
	elif request == 'gettoken':
		handleGetToken(arguments)
	
main()