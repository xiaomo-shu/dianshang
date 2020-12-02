from yzy_terminal_agent.extensions import _redis


class RedisMessageCenter:

    def __init__(self, channel="terminal_task"):
        self.__conn = _redis
        self.chan_sub = channel
        self.chan_pub = channel

    def public(self, msg):
        # self.__conn.publish(self.chan_pub, msg)
        # self.__conn.lpush()
        self.__conn.lpush(self.chan_pub, msg)
        return True

    def subscribe(self):
        pub = self.__conn.pubsub()
        pub.subscribe(self.chan_sub)
        pub.parse_response()
        return pub

    def clear_queue(self):
        self.__conn.ltrim(self.chan_pub, 1, 0)

    def clear_value(self, value, num=0):
        self.__conn.lrem(self.chan_pub, num, value)

    def get_llen(self):
        return self.__conn.llen(self.chan_pub)

    def get_item(self):
        return self.__conn.rpop(self.chan_pub)

    def get_all_items(self):
        return self.__conn.lrange(self.chan_pub, 0, -1)