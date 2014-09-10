xbmc.oauth
==========

OAuth handling server for XBMC/Kodi

How it works
-------------

The addon sends a request for a code providing the source name (ex. facebook) 
and receives a unique random 8 digit base 32 lookup code (7 + 1 check digit) 
and a unique random md5 hex value.

The client then polls the server with the lookup and md5.

The user is directed to the server where they enter the lookup code.

The server uses this code to retrieve the source name and then uses the stored 
authentication data to handle the authentication process, and then stores the 
token with the lookup code.

The polling client receives the token.

Is it safe
----------

As long as the user correctly enters the lookup code (barring external factors) yes.

The presence of the check digit helps ensure correct entry of the lookup code.

There are 33,285,996,544 possible code combinations and at least 2 characters 
would have to be entered incorrectly to erroneously pass the check digit test, and 
in most of these cases it will still not pass the test. The likelihood of the 
incorrect code matching another code is multiplied by the number of users currently 
authenticating which is minimized as codes are only valid for 5 minutes.
