import json
import pika
import time
import sys
import traceback

from django.utils.log import getLogger, NullHandler
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.mail import mail_admins

from ccommander import api

logger = getLogger('ccommander.rpcserver')
if not logger.handlers:
    logger.addHandler(NullHandler())


class Command(BaseCommand):
    """RPC Server to manage Emailvision's Campaign Commander through its
    management API

    It starts a rpc server listening from incomming request in the RabbitMQ
    queue specied as RABITMQ_RPC_QUEUE in django settings
    """
    help = __doc__

    def handle(self, *args, **options):
        self.verbosity = options['verbosity']

        connection = pika.BlockingConnection(pika.ConnectionParameters(
            **settings.RABITMQ_CONNECTION_PARAMS))
        channel = connection.channel()
        queue = settings.RABITMQ_RPC_QUEUE
        channel.queue_declare(queue=queue)
        channel.basic_consume(self.on_request, queue=queue, no_ack=False)
        try:
            if self.verbosity:
                print "[x] Awaiting RPC requests"
            channel.start_consuming()
        except KeyboardInterrupt:
            if self.verbosity:
                print "[x] Shutting down...",
        finally:
            connection.close()
            if self.verbosity:
                print "connection closed",

    def on_request(self, ch, method, props, body):
        """
        Expected body:
        {
            "method": ...,
            "args": ...,
            "kwargs": ...
        }
        """
        data = json.loads(body)
        try:
            action = data['method']
            args = data.get('args', ())
            kwargs = data.get('kwargs', {})
            if self.verbosity:
                print "[.] Received request to %s(%s, %s)" % (action, args, kwargs)
            getattr(api, action)(*args, **kwargs)
        except Exception, e:
            logger.error(e)
            type, value, tb = sys.exc_info()
            message = 'RPC-SERVER has crashed:\n%s\n%s: %s\n\n%s\nargs:%r' % \
                    (e, type, value, '\n'.join(traceback.format_tb(tb)), data)
            mail_admins('RPC-SERVER ERROR', message)
        else:
            ch.basic_ack(delivery_tag=method.delivery_tag)

