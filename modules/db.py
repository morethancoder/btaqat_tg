# use redis database
import json
import asyncio
import math
import os
from redis import Redis
from dotenv import load_dotenv

# ? init enviroment variables
load_dotenv()
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_ID = os.getenv('DB_ID')

redis_store = Redis(host=DB_HOST, port=DB_PORT, db=DB_ID)

#! LIST
def add_to_list(id: int,list_id) -> bool:
    """
    add user id to database
    --
    - if user id exists return `False`
    - if not exists add it & return `True`
    """
    users = redis_store.lrange(list_id, 0, -1) or []
    if str(id).encode() in users:
        return False
    else:
        redis_store.rpush(list_id, id)
        return True


def get_list_count(list_id) -> int:
    if redis_store.exists(list_id):
        return redis_store.scard(list_id)
    else:
        return 0


def delete_from_list(id: int,list_id):
    """
    delete user if exists in db
    --
    return `True` on success delete
    """
    users = redis_store.lrange(list_id, 0, -1) or []
    for user_id in users:
        if int(user_id.decode()) == id:
            redis_store.lrem(list_id, 0, user_id)
            return True

    return False


def get_list(list_id) -> list:
    """
    get available user_ids from db
    --
    to be used in broadcasting
    """
    users_list = []
    result = redis_store.lrange(list_id, 0, -1) or []
    for item in result:
        user_id = int(item.decode())
        users_list.append(user_id)

    return users_list


#! SET
# ? users set functions

def add_user_id(id: int,list_id='users') -> bool:
    """
    add user id to database
    --
    - if user id exists return `False`
    - if not exists add it & return `True`
    """
    if redis_store.sismember(list_id, id):
        return False
    else:
        redis_store.sadd(list_id, id)
        return True

def get_set_items_count(list_id) -> int:
    return redis_store.scard(list_id)

def get_users_count() -> int:
    return redis_store.scard('users')


def delete_user(id: int,list_id='users'):
    """
    delete user if exists in db
    --
    return `True` on success delete
    """
    if redis_store.srem(list_id, id) == 1:
        return True
    else:
        return False


def get_users_list(list_id = 'users') -> list:
    """
    get available user_ids from db
    --
    to be used in broadcasting
    """
    users_list = []
    cursor = 0
    while True:
        # Retrieve the next batch of elements from the set
        response = redis_store.sscan(list_id, cursor=cursor)
        cursor, elements = response

        # Process the elements
        for element in elements:
            user_id = int(element.decode())
            users_list.append(user_id)

        # If there are no more elements, break the loop
        if cursor == 0:
            break

    return users_list

# ? user state functions


def set_user_state(id: int, state: str, expire=60,key=None):
    """
    set the state for a user in the database
    """
    if not key:
        key = f"user:{id}:state"
    return redis_store.set(key, state, expire)

def set_key(key,value,expire=None,same_ttl=False):
    return redis_store.set(key, value, expire,xx=same_ttl)

def get_key(key):
    result = redis_store.get(key)
    if result:
        state = result.decode()
        return state
    else:
        return result


def get_user_state(id: int,key=None):
    """
    get the available user state
    """
    if not key:
        key = f"user:{id}:state"

    result = redis_store.get(key)
    if result:
        state = result.decode()
        return state
    else:
        return result


def delete_user_state(id: int , key=None) -> bool:
    """
    Delete the state of a user from the database
    """
    if not key:
        key = f"user:{id}:state"

    if redis_store.delete(key) == 1:
        return True
    else:
        return False

def get_expire_time_in_minutes(chat_id):
    key = f"user:{chat_id}:state"
    ttl_seconds = redis_store.ttl(key)
    if ttl_seconds > 0:
        ttl_minutes = math.floor(ttl_seconds / 60)
    else:
        ttl_minutes = None

    return ttl_minutes

# def reset_invalid_list(list_id):
#     for item in get_list(list_id):
#         user_state = get_user_state(item)
#         if user_state:
#             if list_id not in user_state:

if __name__ == "__main__":
    print(len(redis_store.keys()))
    def backup(path):
        users =  get_users_list()
        with open(path,'w') as f:
            json.dump(users,f,indent=2)

    # print(redis_store.flushdb())

    def format():
        keys_count = 0
        for key in redis_store.keys():
            if 'state' in key.decode():
                keys_count += 1
                redis_store.delete(key)
        return keys_count

    def cleanup():

        for item in  get_users_list('ready'):
            user_state = get_user_state(item)
            if user_state:
                # print(user_state)
                if 'ready' not in user_state:
                    print(user_state)
                    print(delete_user(item,'ready'))
                    print( delete_user_state(item))
                    print(os.unlink(f'{item}.png'))
                    print(os.unlink(f'{item}.mov'))

        index =0 
        for filename in os.listdir():
            if filename[-3:] == 'mov' or filename[-3:] == 'png':
                user_id = filename[:-4]
                if int(user_id) in get_users_list('ready') or int(user_id) in get_list('wait'):
                    pass
                else:
                    index += 1  
                    print(filename,index)
                    print(delete_user_state(int(user_id)))
                    os.unlink(filename)

    def main():
        print('active users',  get_users_count())
        print('active states',len(redis_store.keys()) - 1)
        
        print(f"count ready states ({get_set_items_count('ready')})")
        print(f"count wait states ({get_list_count('wait')})")

        print('Ahmed ali state -->',get_user_state(449968222))
        # print(delete_user_state(449968222))

        print('17707 state -->',get_user_state(5444750825))
        # print(delete_from_list(5392248913,'wait'))
        
        # for item in get_users_list('ready'):
        #     if os.path.exists(f'{item}.mov'):
        #         pass
        #     else:
        #         print(delete_user(item,'ready'))
        #         print(delete_user_state(item,'ready'))
        # # print(redis_store.delete('wait'))
        # for item in get_list('wait'):
        #     if os.path.exists(f'{item}.mov') :
        #         user_state = get_user_state(item)
        #         print('yes')
        #         print(get_user_state(item))
        #         print(user_state)
        #     # print(delete_from_list(item,'wait'))
        

    main()
    cleanup()
    # users = get_users_list()
    # with open('chat.json','w') as f:
    #     json.dump(users,f,indent=2)
    # with open('chat.json','r') as f:
    #     users=json.load(f)
    #     for user in users:
    #         add_user_id(user)

 