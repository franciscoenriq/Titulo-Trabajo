from flask import current_app as app
from datetime import datetime
from bson.objectid import ObjectId

def insert_message(room_id, user_id, content):
    message = {
        "room_id": room_id,
        "user_id": user_id,
        "content": content,
        "timestamp": datetime.now(),
        "quality": None,
        "intervention_triggered": False
    }
    result = app.mongo.db.messages.insert_one(message)
    return str(result.inserted_id)

def get_messages_by_room(room_id):
    return list(app.mongo.db.messages.find({"room_id": room_id}).sort("timestamp", 1))

def update_message_quality(message_id, quality, intervention=False):
    app.mongo.db.messages.update_one(
        {"_id": ObjectId(message_id)},
        {"$set": {"quality": quality, "intervention_triggered": intervention}}
    )
