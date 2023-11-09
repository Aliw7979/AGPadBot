import redis

# Connect to Redis
r = redis.Redis(host='localhost', port=6379, db=0)

def add_client(telegram_id, token, api_key):
    # Store the client details as a hash in Redis
    client_data = {
        'token': token,
        'api_key': api_key,
    }
    r.hmset(f'client:{telegram_id}', client_data)
    print(f"client by id : {telegram_id} , token : {token} and api_key: {api_key} created.")


def update_client(telegram_id, token=None, api_key=None):
    # Check if either token or API key is provided
    if token is None and api_key is None:
        return  # No updates to perform

    # Update the client details in Redis
    with r.pipeline() as pipe:
        pipe.multi()
        if token is not None:
            pipe.hset(f'client:{telegram_id}', 'token', token)
        if api_key is not None:
            pipe.hset(f'client:{telegram_id}', 'api_key', api_key)
        pipe.execute()
        
def get_clients_by_id(telegram_id):
    # Retrieve the client details by ID from Redis
    client_data = r.hgetall(f'client:{telegram_id}')
    if client_data:
        client = {}
        for key, value in client_data.items():
            client[key.decode()] = value.decode()
        return client
    else:
        return None

def remove_client(telegram_id):
    # Remove the client details from Redis
    r.delete(f'client:{telegram_id}')

def get_all_clients():
    # Retrieve all client keys
    client_keys = r.keys('client:*')

    # Retrieve client details for each key
    clients = []
    for key in client_keys:


        telegram_id = key.decode().split(':')[1]
        client_data = r.hgetall(key)
        client = {field.decode(): value.decode() for field, value in client_data.items()}
        clients.append(client)

    return clients

def delete_all_clients():
    # Retrieve all client keys
    client_keys = r.keys('client:*')

    # Delete client hashes
    for key in client_keys:
        r.delete(key)



