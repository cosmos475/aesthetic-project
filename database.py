import motor.motor_asyncio
from config import Config

class Db:

    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.bot = self.db.bots
        self.userbot = self.db.userbot 
        self.col = self.db.users
        self.nfy = self.db.notify
        self.bcfg = self.db.bot_config
        self.src = self.db.source
        self.dest = self.db.destination
        self.capture = self.db.capture_mode

    def new_user(self, id, name):
        return dict(
            id = id,
            name = name,
            ban_status=dict(
                is_banned=False,
                ban_reason="",
            ),
        )

    async def add_user(self, id, name):
        user = self.new_user(id, name)
        await self.col.insert_one(user)

    async def is_user_exist(self, id):
        user = await self.col.find_one({'id':int(id)})
        return bool(user)

    async def total_users_count(self):
        count = await self.col.count_documents({})
        return count

    async def total_users_bots_count(self):
        bcount = await self.bot.count_documents({})
        count = await self.col.count_documents({})
        return count, bcount

    async def remove_ban(self, id):
        ban_status = dict(
            is_banned=False,
            ban_reason=''
        )
        await self.col.update_one({'id': id}, {'$set': {'ban_status': ban_status}})

    async def ban_user(self, user_id, ban_reason="No Reason"):
        ban_status = dict(
            is_banned=True,
            ban_reason=ban_reason
        )
        await self.col.update_one({'id': user_id}, {'$set': {'ban_status': ban_status}})

    async def get_ban_status(self, id):
        default = dict(
            is_banned=False,
            ban_reason=''
        )
        user = await self.col.find_one({'id':int(id)})
        if not user:
            return default
        return user.get('ban_status', default)

    async def get_all_users(self):
        return self.col.find({})

    async def delete_user(self, user_id):
        await self.col.delete_many({'id': int(user_id)})

    async def get_banned(self):
        users = self.col.find({'ban_status.is_banned': True})
        b_users = [user['id'] async for user in users]
        return b_users

    async def update_configs(self, id, configs):
        await self.col.update_one({'id': int(id)}, {'$set': {'configs': configs}})

    async def get_configs(self, id):
        default = {
            'caption': None,
            'duplicate': True,
            'forward_tag': False,
            'min_size': 0,
            'max_size': 0,
            'extension': None,
            'keywords': None,
            'protect': None,
            'button': None,
            'db_uri': None,
            'filters': {
               'poll': True,
               'text': True,
               'audio': True,
               'voice': True,
               'video': True,
               'photo': True,
               'document': True,
               'animation': True,
               'sticker': True
            }
        }
        user = await self.col.find_one({'id':int(id)})
        if user:
            return user.get('configs', default)
        return default 

    async def add_bot(self, datas):
       if not await self.is_bot_exist(datas['user_id']):
          await self.bot.insert_one(datas)

    async def remove_bot(self, user_id):
       await self.bot.delete_many({'user_id': int(user_id)})

    async def get_bot(self, user_id: int):
       bot = await self.bot.find_one({'user_id': user_id})
       return bot if bot else None

    async def is_bot_exist(self, user_id):
       bot = await self.bot.find_one({'user_id': user_id})
       return bool(bot)
   
    async def add_userbot(self, datas):
       if not await self.is_userbot_exist(datas['user_id']):
          await self.userbot.insert_one(datas)

    async def remove_userbot(self, user_id):
       await self.userbot.delete_many({'user_id': int(user_id)})

    async def get_userbot(self, user_id: int):
       bot = await self.userbot.find_one({'user_id': user_id})
       return bot if bot else None

    async def is_userbot_exist(self, user_id):
       bot = await self.userbot.find_one({'user_id': user_id})
       return bool(bot)
    
    async def set_destination(self, user_id, chat_id, title, username, type="channel", thread_id=None):
       await self.dest.update_one(
          {"user_id": int(user_id)},
          {"$set": {"chat_id": chat_id, "title": title, "username": username, "type": type, "thread_id": thread_id}},
          upsert=True
       )

    async def get_destination(self, user_id: int):
       destination = await self.dest.find_one({"user_id": int(user_id)})
       if destination:
          destination.setdefault("type", "channel")
          destination.setdefault("thread_id", None)
       return destination

    async def remove_destination(self, user_id: int):
       await self.dest.delete_many({"user_id": int(user_id)})

    async def set_capture_mode(self, user_id, enabled, expiry_seconds=600):
       import time as _time
       if enabled:
          await self.capture.update_one(
             {"user_id": int(user_id)},
             {"$set": {"active": True, "expires": _time.time() + expiry_seconds}},
             upsert=True
          )
       else:
          await self.capture.update_one(
             {"user_id": int(user_id)},
             {"$set": {"active": False, "expires": None}},
             upsert=True
          )

    async def is_capture_active(self, user_id) -> bool:
       import time as _time
       doc = await self.capture.find_one({"user_id": int(user_id)})
       if not doc or not doc.get("active"):
          return False
       expires = doc.get("expires")
       if expires is None or _time.time() > expires:
          return False
       return True

    async def get_filters(self, user_id):
       filters = []
       filter = (await self.get_configs(user_id))['filters']
       for k, v in filter.items():
          if v == False:
            filters.append(str(k))
       return filters

    async def add_frwd(self, user_id):
       return await self.nfy.insert_one({'user_id': int(user_id)})

    async def rmve_frwd(self, user_id=0, all=False):
       data = {} if all else {'user_id': int(user_id)}
       return await self.nfy.delete_many(data)

    async def get_all_frwd(self):
       return self.nfy.find({})
  
    async def forwad_count(self):
        c = await self.nfy.count_documents({})
        return c
        
    async def is_forwad_exit(self, user):
        u = await self.nfy.find_one({'user_id': user})
        return bool(u)
        
    async def get_forward_details(self, user_id):
        defult = {
            'chat_id': None,
            'forward_id': None,
            'toid': None,
            'last_id': None,
            'limit': None,
            'msg_id': None,
            'start_time': None,
            'fetched': 0,
            'offset': 0,
            'deleted': 0,
            'total': 0,
            'duplicate': 0,
            'skip': 0,
            'filtered' :0,
            'thread_id': None
        }
        user = await self.nfy.find_one({'user_id': int(user_id)})
        if user:
            details = user.get('details', defult)
            details.setdefault('thread_id', None)
            return details
        return defult
   
    async def update_forward(self, user_id, details):
        await self.nfy.update_one({'user_id': user_id}, {'$set': {'details': details}})

    async def get_branding(self):
        default = {'enabled': False, 'url': None}
        cfg = await self.bcfg.find_one({'_id': 'branding'})
        if cfg:
            return {'enabled': cfg.get('enabled', False), 'url': cfg.get('url')}
        return default

    async def set_branding(self, enabled=None, url=None):
        current = await self.get_branding()
        if enabled is not None:
            current['enabled'] = enabled
        if url is not None:
            current['url'] = url
        await self.bcfg.update_one(
            {'_id': 'branding'},
            {'$set': {'enabled': current['enabled'], 'url': current['url']}},
            upsert=True
        )

    async def set_source(self, user_id, chat_id, title, username):
        await self.src.update_one(
            {'user_id': int(user_id)},
            {'$set': {'chat_id': chat_id, 'title': title, 'username': username,
                      'last_verified': None, 'last_status': None}},
            upsert=True
        )

    async def get_source(self, user_id):
        return await self.src.find_one({'user_id': int(user_id)})

    async def remove_source(self, user_id):
        await self.src.delete_many({'user_id': int(user_id)})

    async def update_source_status(self, user_id, status, verified_at):
        await self.src.update_one(
            {'user_id': int(user_id)},
            {'$set': {'last_status': status, 'last_verified': verified_at}}
        )

db = Db(Config.DATABASE_URI, Config.DATABASE_NAME)
