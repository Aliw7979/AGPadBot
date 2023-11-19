import redis

# Connect to Redis
r = redis.Redis(host='localhost', port=6379, db=0)

def add_client(telegram_id, token):
    # Store the clientOfAd details as a hash in Redis
    client_data = {
        'token': token,
    }
    r.hmset(f'clientOfAd:{telegram_id}', client_data)
    print(f"clientOfAd by id : {telegram_id} , token : {token}")


def update_client(telegram_id, token=None):
    # Check if either token or API key is provided
    if token is None:
        return  # No updates to perform

    # Update the clientOfAd details in Redis
    with r.pipeline() as pipe:
        pipe.multi()
        if token is not None:
            pipe.hset(f'clientOfAd:{telegram_id}', 'token', token)
        pipe.execute()
        
def get_clients_by_id(telegram_id):
    # Retrieve the clientOfAd details by ID from Redis
    client_data = r.hgetall(f'clientOfAd:{telegram_id}')
    if client_data:
        clientOfAd = {}
        for key, value in client_data.items():
            clientOfAd[key.decode()] = value.decode()
        return clientOfAd
    else:
        return None

def remove_client(telegram_id):
    # Remove the clientOfAd details from Redis
    r.delete(f'clientOfAd:{telegram_id}')

def get_all_clients():
    # Retrieve all clientOfAd keys
    client_keys = r.keys('clientOfAd:*')

    # Retrieve clientOfAd details for each key
    clients = []
    for key in client_keys:


        telegram_id = key.decode().split(':')[1]
        client_data = r.hgetall(key)
        clientOfAd = {field.decode(): value.decode() for field, value in client_data.items()}
        clients.append(clientOfAd)

    return clients

def delete_all_clients():
    # Retrieve all clientOfAd keys
    client_keys = r.keys('clientOfAd:*')

    # Delete clientOfAd hashes
    for key in client_keys:
        r.delete(key)



