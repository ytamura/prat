from flask import Blueprint, request, g, current_app, render_template
import datetime
import geventwebsocket
from gevent_zeromq import zmq
import json
from chat.datastore import db
from chat.markdown import markdown_renderer
from chat.tardis import datetime_to_unix
from chat.zmq_context import zmq_context

eventhub = Blueprint("eventhub", __name__)

@eventhub.route('')
def eventhub_client():
  if not request.environ.get('wsgi.websocket'):
    return ""
  websocket = request.environ['wsgi.websocket']
  push_socket = zmq_context.socket(zmq.PUSH)
  push_socket.connect(current_app.config["PUSH_ADDRESS"])
  subscribe_socket = zmq_context.socket(zmq.SUB)
  user_channels = {}

  # only listen for messages the user is subscribed to
  for channel in g.user["channels"]:
    channel_id = str(db.channels.find_one({"name": channel})["_id"])
    user_channels[channel] = channel_id
    subscribe_socket.setsockopt(zmq.SUBSCRIBE, channel_id)

  subscribe_socket.connect(current_app.config["SUBSCRIBE_ADDRESS"])

  poller = zmq.Poller()
  poller.register(subscribe_socket, zmq.POLLIN)
  poller.register(websocket.socket, zmq.POLLIN)

  try:
    message = None
    while True:
      events = dict(poller.poll())

      # Server -> Client
      if subscribe_socket in events:
        message = subscribe_socket.recv()
        channel_id, packed = message.split(" ", 1)
        g.msg_unpacker.feed(packed)
        unpacked = g.msg_unpacker.unpack()
        action = unpacked["action"]
        data = unpacked["data"]
        if action == "message":
          channel = data["channel"]
          if channel in g.user["channels"]:
            websocket.send(json.dumps(unpacked))

      # Client -> Server
      if websocket.socket.fileno() in events:
        socket_data = websocket.receive()
        if socket_data is None:
          break
        socket_data = json.loads(socket_data)
        action = socket_data["action"]
        data = socket_data["data"]
        if action == "switch_channel":
          # Update channel logged in user is subscribed to
          g.user['last_selected_channel'] = data["channel"]
          db.users.save(g.user)
        if action == "publish_message":
          message = data["message"]
          channel = data["channel"]
          # we use isoformat in msgpack because it cant handle datetime objects
          time_now = datetime.datetime.utcnow()
          mongo_event_object = { "author": g.user["name"],
                                 "message": message,
                                 "email": g.user["email"],
                                 "channel": channel,
                                 "gravatar": g.user["gravatar"],
                                 "datetime": time_now }
          message_id = db.events.insert(mongo_event_object)
          rendered_message = render_template("chat_message.htmljinja",
                                             render_template=render_template,
                                             message=markdown_renderer.render(message),
                                             author=g.user["name"],
                                             email=g.user["email"],
                                             message_id=message_id,
                                             gravatar=g.user["gravatar"],
                                             time=datetime_to_unix(time_now),
                                             merged_messages=False)
          msgpack_event_object = {"action":"message",
                                  "data":{
                                    "author": g.user["name"],
                                    "message": rendered_message,
                                    "channel": channel,
                                    "datetime": time_now.isoformat() }}
          packed = g.msg_packer.pack(msgpack_event_object)

          # -> Everyone
          # prepend an identifier showing which channel the event happened on for PUB/SUB
          push_socket.send(" ".join([user_channels[channel], packed]))
  except geventwebsocket.WebSocketError, e:
    print "{0} {1}".format(e.__class__.__name__, e)

  # TODO(kle): figure out how to clean up websockets left in a CLOSE_WAIT state
  push_socket.close()
  subscribe_socket.close()
  websocket.close()
  return ""
