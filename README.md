![HoneyPress](https://raw.githubusercontent.com/dustyfresh/HoneyPress/master/branding/bee-small.png)
# WordPress honeypot
[HoneyPress](http://honeypress.org/), a WordPress honeypot in a docker container.

## Payloads
- [https://gist.github.com/dustyfresh/42551964a91e2cac4c0f39a2a3e2e372](https://gist.github.com/dustyfresh/42551964a91e2cac4c0f39a2a3e2e372)

## Update:
I have began a complete re-write / re-implementation of this idea. Decided it would be best to go with good ol' Flask and python for creating a "WordPress" install. Because of Flask's flexibility and Python's modularity there are all kinds of fun to be had.


## Clone and build Docker image
```
$ git clone https://github.com/dustyfresh/HoneyPress.git
$ cd HoneyPress && docker-compose up -d
```

## Nginx Logs
You can view access logs easily:
```
$ docker exec honeypress bash -c 'tail /var/log/nginx/access.log'

192.168.99.1 - - [06/Jun/2016 03:21:41] "GET /wp-login.php?__debugger__=yes&cmd=resource&f=style.css HTTP/1.1" 200 -
192.168.99.1 - - [06/Jun/2016 03:21:41] "GET /wp-login.php?__debugger__=yes&cmd=resource&f=jquery.js HTTP/1.1" 200 -
192.168.99.1 - - [06/Jun/2016 03:21:41] "GET /wp-login.php?__debugger__=yes&cmd=resource&f=debugger.js HTTP/1.1" 200 -
192.168.99.1 - - [06/Jun/2016 03:21:41] "GET /wp-login.php?__debugger__=yes&cmd=resource&f=console.png HTTP/1.1" 200 -
192.168.99.1 - - [06/Jun/2016 03:21:41] "GET /wp-login.php?__debugger__=yes&cmd=resource&f=ubuntu.ttf HTTP/1.1" 200 -
192.168.99.1 - - [06/Jun/2016 03:21:41] "GET /wp-login.php?__debugger__=yes&cmd=resource&f=console.png HTTP/1.1" 200 -
192.168.99.1 - - [06/Jun/2016 03:21:44] "GET /wp-login.php HTTP/1.1" 200 -
192.168.99.1 - - [06/Jun/2016 03:21:46] "POST /wp-login.php HTTP/1.1" 200 -
```

## Database queries
More documentation coming soon!

### Custom MongoDB database with authentication
```
$ docker run -d --name honeypress -p 80:80 -e 'MONGO_HOST=127.0.0.1' -e 'MONGO_PORT=27017' -e 'MONGO_USER=honeypress' -e 'MONGO_PASS=somethingsecure' honeypress
```

### Accessing the data
```
$ docker exec -it honeyDB mongo
> use honey
> db.payloads.count()
```

#### Finding payloads that are not equal to the hashes in this list (deprecated, more docs coming soon):
#### Finding payloads by codename:
```javascript
db.payloads.find({'codename': 'proud-water'}, {'_id': 0}).pretty()
```

#### Finding payloads by IP address:
```javascript
db.payloads.find({'ip': '187.161.157.180'}, {'payload.data': 1}).pretty()
```

#### Finding payloads by user-agent:
```javascript
db.payloads.find({'user-agent': 'Wget(linux)'}, {'payload.data': 1}).pretty()
```

#### Finding payloads by user-agent with regex:
```javascript
db.payloads.find({'user-agent': {$regex: /.*mozilla.*/, $options: 'si'}}, {'payload.data': 1}).pretty()
```

#### Finding payload commands with regex:
```javascript
db.payloads.find({'payload.data.cmd': {$regex: /.*ping.*/, $options: 'si'}}, {'payload.data': 1}).pretty()
```
