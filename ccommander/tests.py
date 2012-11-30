"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

import datetime

from django.test import TestCase

from pyDoubles.framework import spy, stub, mock
from pyDoubles.framework import when, expect_call, assert_that_method
from pyDoubles.framework import method_returning, method_raising

from ccommander.models import *


class MessageTest(TestCase):

    def setUp(self):
        Message._remote = spy(MessageRemote())
        when(Message._remote.save).then_return(1234)
        m = Message(
            name="Test message",
            subject="Message subject",
            description="Message description",
            from_name="Test server",
            from_email="email@from.com",
            reply_to_name="Test server",
            reply_to_email="email@reply.com",
            to="[EMV FIELD]FIRSTNAME[EMV /FIELD]",
            body="Message body"
        )
        self.message = m

    def test_creation(self):
        """
        Tests that when a message is created, is also created remotely
        """
        self.message.save()
        assert_that_method(Message._remote.save).was_called()\
                                                .with_args(self.message)
        self.assertIsNotNone(self.message.remote_id, "remote ID was not set")

    def test_deletion(self):
        """
        Tests that when a message is deleted, is also deleted remotely.
        A remote message cannot be removed if it has been used.
        """
        self.message.save()
        self.message.delete()
        assert_that_method(Message._remote.delete).was_called()\
                                                  .with_args(self.message)


class UrlTest(TestCase):

    fixtures = ["url_test.json"]
    multi_db = True

    def test_link_creation(self):
        """
        Tests that when an url is created, is also created remotely and
        added to its associated message
        """
        Link._remote = spy(LinkRemote())
        message = Message.objects.get(pk=1)
        link = Link(name="My url", url="http://url.to.site/", message=message)
        link.save()

        assert_that_method(Link._remote.save).was_called().with_args(link)

    def test_mirror_link_creation(self):
        """
        Tests that when a mirror url is created, is also created remotely and
        added to its associated message
        """
        MirrorLink._remote = spy(MirrorLinkRemote())
        message = Message.objects.get(pk=1)
        link = MirrorLink(name="My url", url="http://url.to.site/", message=message)
        link.save()

        assert_that_method(MirrorLink._remote.save).was_called().with_args(link)

    def test_unsubscribe_link_creation(self):
        """
        Tests that when an unsubscribe url is created, is also created remotely
        and added to its associated message
        """
        UnsubscribeLink._remote = spy(UnsubscribeLinkRemote())
        message = Message.objects.get(pk=1)
        link = UnsubscribeLink(name="My url", url="http://url.to.site/",
                               message=message)
        link.save()

        assert_that_method(UnsubscribeLink._remote.save).was_called().with_args(link)


class SegmentTest(TestCase):

    def setUp(self):
        Segment._remote = spy(SegmentRemote())
        self.segment = Segment(name="Test segment")

    def test_creation(self):
        """
        Tests that when a segment is created, is also created remotely
        """
        self.segment.save()
        assert_that_method(Segment._remote.save).was_called().with_args(self.segment)

    def test_deletion(self):
        """
        Tests that when a segment is deleted, is also deleted remotely
        """
        self.segment.save()
        self.segment.delete()
        assert_that_method(Segment._remote.delete).was_called().with_args(
                                                                self.segment)


class CriteriaTest(TestCase):

    fixtures = ["segment_test.json"]
    multi_db = True

    def test_creation(self):
        """
        Test that when criterias are created, they are correctly added to the
        segment (in local and remote)
        """
        Criteria._remote = spy(CriteriaRemote)
        segment = Segment.objects.get(pk=1)
        criteria = Criteria(column_name='EMAIL', operator='EQUALS',
                            values=['email1@mail.com', 'email2@mail.com'],
                            segment=segment)
        criteria.save()

        assert_that_method(Criteria._remote.save).was_called().with_args(criteria)
        self.assertEqual(1, segment.criteria_set.count())


class CampaignTest(TestCase):

    fixtures = ["campaign_test.json"]
    multi_db = True

    def setUp(self):
        Campaign._remote = spy(CampaignRemote())

    def test_creation(self):
        """
        Tests that when a campaign is created, the are also created remotely
        """
        campaign = Campaign(
            name='Test campaign',
            url_end_campaign='http://url',
            send_at=datetime.datetime.now() + datetime.timedelta(minutes=5),
            message=Message.objects.get(pk=1),
            segment=Segment.objects.get(pk=1)
        )
        campaign.save()

        assert_that_method(Campaign._remote.save).was_called().with_args(campaign)

