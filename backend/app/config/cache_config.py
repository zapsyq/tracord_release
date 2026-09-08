import redis.asyncio as redis

#定义连接端口，后续移到其他服务器直接修改变量即可
redis_host = "localhost"
redis_port = 6379
redis_db = 0


#创建Redis的连接对象
redis_client = redis.Redis(
    #Redis服务器主机地址
    host=redis_host,
    #Redis端口号
    port=redis_port,
    #Redis数据库编号，默认为0
    db=redis_db,
    #是否将字节数据解码为字符串
    decode_responses=True
)



