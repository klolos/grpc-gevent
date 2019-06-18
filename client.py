from __future__ import print_function

import gevent.monkey
gevent.monkey.patch_all()

import argparse
from datetime import datetime

import pb.echoserver_pb2 as echoserver
import pb.echoserver_pb2_grpc as echoserver_grpc

import logging
logging.basicConfig(level=logging.DEBUG)

import grpc.experimental.gevent as _grpc_gevent
_grpc_gevent.init_gevent()

import grpc
import gevent.pool
import gevent.threadpool
import gevent.event
from gevent import Timeout

def log(id, msg, *args):
        print(str(datetime.now()), '[%2d]' % id, msg % args)

def request_plain(client, id, msg, sleep_secs):
    """
    Each request blocks gevent in normal operation.
    """
    req = echoserver.Request(id=id, message=msg, sleep_seconds=sleep_secs)
    log(req.id, "Started")
    try:
        with Timeout(1):
            resp = client.Echo(req)
    except Timeout:
        log(req.id, "Successfully raised a timeout")
        return None
    else:
        log(req.id, "Failed to raise a timeout")
        return resp

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-p', '--port', type=int, default=12345)

    args = parser.parse_args()
    request_func = request_plain

    channel = grpc.insecure_channel('localhost:%d' % args.port)
    stub = echoserver_grpc.EchoerStub(channel)

    requests = [(1, "30 secs", 30)]

    map_func = lambda (i, m, s): request_func(stub, i, m, s)

    start = datetime.now()
    pool = gevent.pool.Pool()
    mapped = pool.imap_unordered(map_func, requests)

    gevent.sleep(3)

    try:
        for rsp in mapped:
            pass
    except Exception as e:
        print("Exception while running:", e)

    end = datetime.now()
    print("Finished in", end - start)

if __name__ == '__main__':
    main()
