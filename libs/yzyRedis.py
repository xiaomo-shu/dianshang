import redis


class yzyRedis:
    def __init__(self):
        self.rds = None
        self._host = "127.0.0.1"
        self._password = ""
        self._port = 6379
        self._db = 0

    def init_app(self, app=None):
        if app:
            self._host = app.config.get("REDIS_HOST", "127.0.0.1")
            self._password = app.config.get("REDIS_PASSWOR", "")
            self._port = app.config.get("REDIS_PORT", 6379)
            self._db = app.config.get("REDIS_DB", 0)

        self.rds = redis.StrictRedis(host=self._host, password=self._password, port=self._port, db=self._db)
        self.rds.ping()

    def publish(self, channel, msg):
        return self.rds.publish(channel, msg)

    def pubsub(self):
        return self.rds.pubsub()

    def get(self, key):
        return self.rds.get(key)

    def set(self, key, value, ex=None):
        self.rds.set(key, value, ex)

    def delete(self, k):
        tag = self.rds.exists(k)
        if tag: self.rds.delete(k)

    def hash_get(self, name, k):
        return self.rds.hget(name, k)
        # if res: return res.decode()

    def hash_set(self, name, k, v):
        self.rds.hset(name, k, v)

    def hash_getall(self, name):
        return self.rds.hgetall(name)

    def hash_incr(self, name, k, increment):
        return self.rds.hincrby(name, k, increment)

    def hash_del(self, name, k):
        res = self.rds.hdel(name, k)
        if res:
            return 1
        else:
            return 0

    def incr(self, name):
        res = self.rds.incr(name)
        return res

    def decr(self, name):
        res = self.rds.decr(name)
        return res

    def lpush(self, name, item):
        res = self.rds.lpush(name, item)
        return res

    def lpop(self, name):
        res = self.rds.lpop(name)
        return res

    def rpop(self, name):
        res = self.rds.rpop(name)
        return res

    def llen(self, name):
        res = self.rds.llen(name)
        return res

    def ltrim(self, name, start, end):
        return self.rds.ltrim(name, start, end)

    def lrange(self, name, start, stop):
        return self.rds.lrange(name, start, stop)

    def lrem(self, name, num, value):
        return self.rds.lrem(name, num, value)

    @property
    def clean_redis(self):
        self.rds.flushdb()
        return 0


if __name__ == "__main__":
    rd = yzyRedis()
    rd.init_app()
    rd.set("hello", "world")
    print(rd.get("hello"))
