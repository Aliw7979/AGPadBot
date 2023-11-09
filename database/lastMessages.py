import redis

# Connect to Redis
r = redis.Redis(host='localhost', port=6379, db=0)

def add_message(telegram_id, token):
    # Store the message details as a hash in Redis
    message_data = {
        'message': token,
    }
    r.hmset(f'message:{telegram_id}', message_data)

def update_message(telegram_id, token=None):
    # Check if either token or API key is provided
    if token is None:
        return  # No updates to perform

    # Update the message details in Redis
    with r.pipeline() as pipe:
        pipe.multi()
        if token is not None:
            pipe.hset(f'message:{telegram_id}', 'token', token)
        pipe.execute()
        
def get_message_by_id(telegram_id):
    # Retrieve the message details by ID from Redis
    message_data = r.hgetall(f'message:{telegram_id}')
    if message_data:
        message = {}
        for key, value in message_data.items():
            message[key.decode()] = value.decode()
        return message
    else:
        return None

def remove_message(telegram_id):
    # Remove the message details from Redis
    r.delete(f'message:{telegram_id}')

def get_all_messages():
    # Retrieve all message keys
    message_keys = r.keys('message:*')

    # Retrieve message details for each key
    messages = []
    for key in message_keys:


        telegram_id = key.decode().split(':')[1]
        message_data = r.hgetall(key)
        message = {field.decode(): value.decode() for field, value in message_data.items()}
        messages.append(message)

    return messages

def delete_all_messages():
    # Retrieve all message keys
    message_keys = r.keys('message:*')

    # Delete message hashes
    for key in message_keys:
        r.delete(key)



