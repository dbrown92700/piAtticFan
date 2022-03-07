#!/usr/bin/python3

import pigpio

print('Content-type: text/html\n')

html = '''
  <html>
	<head>
		<meta name='viewport' content='width=400'>
		<meta name="apple-mobile-web-app-capable" content="yes">
		<link rel="apple-touch-icon" sizes="192X192" href="android.png">
  </head>
  <body style="width:400px;">
  <div align="center" fontsize=30>
	<p style="font-size:40px"><br><br>Attic Fan<br></p>
	<p style="font-size:30px">Garage Door is<br>{0}</p>
	<a href="buttonpush.py">
		<input type="image" src="/apple-touch-icon.png" name="submit" value="On" width=150 height=150>
  	</a>
  </div>
  </body>
  </html>
  '''

#button = Button(24)

pi = pigpio.pi()

gopen = pi.read(24)

if gopen == 0:
  gstatus = 'Closed'
else:
  gstatus = 'Open'

print(html.format(gstatus))