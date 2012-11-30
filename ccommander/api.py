"""
Move ccommander/management to addbuyer_admin/management since this is not
app agnostic
"""
import datetime
import time

import suds
from django.conf import settings
from django.utils.log import getLogger, NullHandler

from addbuyer_admin.models import User, Demand, Wish
# from addbuyer_admin.shortcuts import send_campaign_to_offerers


logger = getLogger('ccommander.rpcserver')
if not logger.handlers:
    logger.addHandler(NullHandler())


def send_transactional_email(email, id, random, encrypt, dyn=None, content=None):
    """Sends an email using the Campaign Commander Transactional API

    email is the email address
    template is the template to use
    """
    client = suds.client.Client(settings.CCOMMANDER_API_NOTIFICATION_WSDL)
    request = client.factory.create('sendRequest')
    request.email = email
    request.notificationId = id
    request.random = random
    request.encrypt = encrypt
    request.synchrotype = 'NOTHING'
    request.uidkey = 'email'
    request.senddate = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

    if dyn:
        for key, value in dyn.items():
            request.dyn.entry.append({'key': key, 'value': value})
    else:
        del request.dyn

    if content:
        for key, value in content.items():
            request.content.entry.append({'key': key, 'value': value})
    else:
        del request.content

    client.service.sendObject(request)


def sync_user(email):
    """Syncs an user with Campaign Commander"""
    # time.sleep(10)
    user = User.objects.filter(email=email).get()
    # trigger callbacks
    user.save()


def send_campaign_to_demand(demand_id):
    """Creates a campaign and send it to all the offertants of the demand with
    ID demand_id
    """
    # demand = Wish.objects.filter(pk=demand_id).get()
    # logger.debug('>>>>>>>>' + unicode(ws).encode('utf-8'))
    # for w in ws:
    #     logger.debug('Wish:' + str(w.id) + 'commercial type:' + str(w.commercial_type))
    # time.sleep(10)
    # demand = Demand.objects.filter(pk=demand_id).get()
    # send_campaign_to_offerers(demand)


