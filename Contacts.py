# Assign all lab contacts
#A mostly complete list of SMS (text only) and MMS (text and image) carrier gateways is available at www.kossboss.com/?p=121
#Alternatively, use a search engine to find SMS and MMS carrier gateways
#storing contacts this way allows grabbing a list containing all of a user's contact information
#to add a user, add below the last line and use the following format
#allcontacts['user1'] = ['<number>@<carrier gateway>', '<email>@<domain>']
allcontacts = {}                                                                #initialize empty dictionary
#allcontacts['user1'] = ['<number>@<carrier>', '<email>@<domain>']

#Dictionary list of users, one lab per line, multiple users of a lab go on the same line
#Add new lab users below the last line. Names must be spelled exactly as
#The format for additional labs and lab users using a dictionary is:
#labusers['<labID>'] = ['user1', 'user2']
labusers = {}                                                                   #initialize empty dictionary
#labusers['<labID>'] = ['user1', 'user2']
