from rpc import Server, Client
import gevent
import random
import string
import time

@Server.register
def foo(name):
    return "hello %s" % name


@Server.register
def echo(name):
    return name


@Server.register
def blah(sec, char):
    gevent.sleep(sec)
    return "%s:%d" % (char, sec)


gevent.spawn(Server("localhost:2786").serve)

gevent.sleep(0.5)

c = Client("localhost:2786")

def run_blah():
  s = time.time()
  args =  (random.randint(1, 10), random.choice(string.ascii_uppercase))
  print(c.blah(*args), time.time() - s )

gevent.spawn(run_blah)
gevent.spawn(run_blah)
gevent.spawn(run_blah)
gevent.spawn(run_blah)
gevent.spawn(run_blah)
gevent.spawn(run_blah)
gevent.spawn(run_blah)
gevent.spawn(run_blah)
gevent.spawn(run_blah)
gevent.sleep(1)
gevent.spawn(run_blah)
gevent.spawn(run_blah)
gevent.spawn(run_blah)
gevent.spawn(run_blah)

gevent.get_hub().join()