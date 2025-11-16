# conf-chat
A basic P2P CLI messaging program made in python

## Set-Up / Running
Requirments: Python 3.12 or higher

To run execute the conf_chat.py file, the following flags must be set:
--port ( defines port number the instance will listen on )
--username ( defines the username the instance is logging in on )
--password ( password must match the username's correct password, see user_data.py )

## Runtime Commands
/q : exits the program
/users : lists all connected users
/dm {username} {message} : sends a message to a specified user 