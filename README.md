# Project 8: User interface for uthenticated brevet time calculator service

In addition to creating UI for basic authentication and token
generation, I have added three additional functionalities in my UI: (a) remember me, (b) logout, 
and (c) CSRF protection. Note: Sessions are not maintained.

Written and maintained by: Andrew Werderman (amwerderman@gmail.com)

## Functionality

To register as a user, visit the register page at `http://<host>:5000/register`. Once registered,
the user will be redirected to the login page `http://<host>:5000/login`. ***If the user is not 
redirected to the login page, that means the username is already in use.*** From here the user
may login and visit the user interface to expose the API! 

Make sure the data base is not empty by visiting `http://<host>:5002/` to populate the 
Brevet with controls. 