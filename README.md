to install python requirements (i recommend use of virtualenv)

`pip install -r requirements.txt`

to install nodejs requirements (using local package.json file)

`npm install`

to create mongo capped collection (while mongod is running)

`mongo oochat schema_create.js`

running the servers:

`python run_server.py`
`python eventhub_server/event_server.py`
and make sure mongod is running