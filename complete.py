#!/usr/bin/env python
import cgi
import cgitb
cgitb.enable()

import mysql.connector

from credentials.cred import DATABASE, USER, PASSWORD
iconDir = 'http://auth.2ndmind.com/icons/'

def getIcon(source):
	if not source: return None
	cnx = mysql.connector.connect(user=USER, password=PASSWORD, database=DATABASE)
	cursor = cnx.cursor()
	
	try:
		query = ('SELECT icon FROM oauth_sources WHERE source = %s')
		cursor.execute(query, (source,))
		for (icon,) in cursor:
			return icon
		return None
	finally:
		cursor.close()
		cnx.close()

html = '''
<html>
	<head>
		<style>
			div.rounded {
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
			body {
				background-color: black;
				color: white;
			}
			.large {
				font-size: 100px;
				font-family:Arial;
			}
			.go_small {
				font-size: 25px;
				font-family:Arial;
				color: green;
			}
		</style>
	</head>
	</body>
		<div style="width:100%;text-align:center;">
			<span class="large">AUTHORIZATION<br>COMPLETE</span>
			<br><br>
			<ICON>
			<br><br>
			<span class="go_small">YOU MAY NOW CLICK OK IN THE ADDON DIALOG</span>
		</div>
	</body>
</html>
'''

arguments = cgi.FieldStorage()
source = None
if 'source' in arguments: source = arguments['source'].value

img = ''
icon = getIcon(source)
if icon:
	if not icon.startswith('http'): icon = iconDir + icon
	img = '<img src="%s" /><img src="%s" /><img src="%s" />' % (icon,iconDir+'arrow.png',iconDir+'xbmc.png')

print "Content-Type: text/html"
print
print html.replace('<ICON>',img)