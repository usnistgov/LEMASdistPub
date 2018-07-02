"""
Variables for setting up sending of messages through SMTP server
"""
#defines the IP address and port of the SMTP server for sending messages through. E.g. google is smtp.gmail.com on port 465
SMTPaddress = '129.6.16.94'
#SMTPaddress = 'smtp.gmail.com'                                                  #for gmail
SMTPport = 25
#SMTPport = 587                                                                  #gmail SMTP server port
#the email address to send logs to
logaddress = 'dmgalert@nist.gov'
#the email address to send messages from
fromaddress = 'dmgalert@nist.gov'
#the username and password of the email address. leave the string blank if login to the smtp server is not needed to send messages.
username = ''
password = ''
