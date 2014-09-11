# -*- coding: utf-8 -*-
import rsa
from rsa import bigfile
from StringIO import StringIO
import binascii

from credentials.cred import PRIVATE_KEY
PRIVATE_KEY = rsa.PrivateKey.load_pkcs1(PRIVATE_KEY)

def encrypt(data,key):
	pub = rsa.PublicKey.load_pkcs1(key)
	out = StringIO()
	try:
		bigfile.encrypt_bigfile(StringIO(data),out,pub)
		return binascii.hexlify(out.getvalue())
	finally:
		out.close()
	
def decrypt(data):
	out = StringIO()
	try:
		bigfile.decrypt_bigfile(StringIO(binascii.unhexlify(data.strip())),out,PRIVATE_KEY)
		return out.getvalue()
	finally:
		out.close()