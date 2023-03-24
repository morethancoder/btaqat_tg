# use redis database
import json
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
# def add_user_id(id: int) -> bool:
#     """
#     add user id to database
#     --
#     - if user id exists return `False`
#     - if not exists add it & return `True`
#     """
#     users = redis_store.lrange('users', 0, -1) or []
#     if str(id).encode() in users:
#         return False
#     else:
#         redis_store.lpush('users', id)
#         return True


# def get_users_count() -> int:
#     return redis_store.llen('users')


# def delete_user(id: int):
#     """
#     delete user if exists in db
#     --
#     return `True` on success delete
#     """
#     users = redis_store.lrange('users', 0, -1) or []
#     for user_id in users:
#         if int(user_id.decode()) == id:
#             redis_store.lrem('users', 0, user_id)
#             return True

#     return False


# def get_users_list() -> list:
#     """
#     get available user_ids from db
#     --
#     to be used in broadcasting
#     """
#     users_list = []
#     result = redis_store.lrange('users', 0, -1) or []
#     for item in result:
#         user_id = int(item.decode())
#         users_list.append(user_id)

#     return users_list


#! SET
# ? users set functions

def add_user_id(id: int) -> bool:
    """
    add user id to database
    --
    - if user id exists return `False`
    - if not exists add it & return `True`
    """
    if redis_store.sismember('users', id):
        return False
    else:
        redis_store.sadd('users', id)
        return True


def get_users_count() -> int:
    return redis_store.scard('users')


def delete_user(id: int):
    """
    delete user if exists in db
    --
    return `True` on success delete
    """
    if redis_store.srem('users', id) == 1:
        return True
    else:
        return False


def get_users_list() -> list:
    """
    get available user_ids from db
    --
    to be used in broadcasting
    """
    users_list = []
    cursor = 0
    while True:
        # Retrieve the next batch of elements from the set
        response = redis_store.sscan('users', cursor=cursor)
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


def set_user_state(id: int, state: str, expire=60):
    """
    set the state for a user in the database
    """
    key = f"user:{id}:state"
    return redis_store.set(key, state, expire)


def get_user_state(id: int):
    """
    get the available user state
    """
    key = f"user:{id}:state"
    result = redis_store.get(key)
    if result:
        state = result.decode()
        return state
    else:
        return result


def delete_user_state(id: int) -> bool:
    """
    Delete the state of a user from the database
    """
    key = f"user:{id}:state"
    if redis_store.delete(key) == 1:
        return True
    else:
        return False


if __name__ == "__main__":
    print('active users',get_users_count())
    print('active states',len(redis_store.keys()) - 1)
