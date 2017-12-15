# Distributed-File-System
Implementation of Distributed File System Using REST Service.

> Name : Aditya Bhati<br>
Student_id : 16343086<br>
Email: bhatia@tcd.ie

-> Dependencies
>Python 2.7

>Flask 0.12.2 - For REST API

>Mongodb

>diskcache

>pymongo 3.5.1

>
# Installation 
> cmd terminal mongod

> run authentication.py

> Run Directorysv.py

> Run user.py

# authentication.py( Authentication and Transparent file access)
```
This is the most important part of this project as when an user is added, it must have authentication in order
to interact with the system. U_id ,u_password , p_key(public Key) are the variable that will be used for user authentication.
User will be required to write their username and password which is encrypted we will decrypt it, If a match is found in the database 
period_id gets updated.
Once the autherization is done successfully a ticket is generated in json and is hashed using p_key. This is the stage where authentication is done successfully.
```
# directorysv.py ( Directory Service)
```
This file manages the location of directories and subdir. file_uploader() , file_delete(), file_download() are the functions 
which are used for data manipulation depending on the RESTful system actions will be take for the according to the user.
```

# Caching 
```
This makes a program efficient by reducing lockup time, Disk Cache is used for system caching, when a user uploads it is
immediately pushed in the cache, If the file is present in the cache it is easily extracted, server_instance() is used to return 
the current server.
It is used for asychronous Transaction.
```

# Transaction








