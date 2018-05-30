## /////////////////////////LABORATORY USER LIST\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# Assign all lab contacts
#storing this way allows grabbing of list all of a users contact information
#to add a user, add below the last line and use the following format
#allcontacts['user1'] = ['<number>@<carrier>', '<email>@<domain>']
allcontacts = {}
#allcontacts['user1'] = ['<number>@<carrier>', '<email>@<domain>']

#See above header text for more complete list and examples of SMS gateways
#Dictionary list of users, one lab per line, multiple users of a lab go on the same line
#Add new lab users below the last line. Names must be spelled exactly as
#The format for additional labs and lab users using a dictionary is:
#labusers['<building>/<room>'] = ['user1', 'user2']
labusers = {}                                                                   #initialize empty dictionary
#labusers['<labID>'] = ['user1', 'user2']
