from contextlib import contextmanager

import suds
from django.conf import settings


# Just an special attribute to detect when you want to remove attributes
# from the object sent through SOAP, ex: the id attribute in an apiMessage
# that is being created is meaningless, so you want to delete it if it's None
# del apimessage.id
DELETE = '_delete_'


class Remote(object):
    """Manages communication with the remote database through a SOAP
    webservice
    """
    @contextmanager
    def get_connection(self):
        client = suds.client.Client(self.wsdl)
        con = client.service.openApiConnection(settings.CCOMMANDER_API_USER,
                                               settings.CCOMMANDER_API_PASSWORD,
                                               settings.CCOMMANDER_API_KEY)
        try:
            yield client, con
        finally:
            client.service.closeApiConnection(con)


class MemberRemote(Remote):
    """Remote for Member model"""

    wsdl = settings.CCOMMANDER_API_MEMBER_UPDATE_WSDL

    def rejoin(self, member):
        with self.get_connection() as (client, con):
            client.service.rejoinMemberByEmail(con, member.email)

    def unjoin(self, member):
        with self.get_connection() as (client, con):
            client.service.unjoinMemberByEmail(con, member.email)

    def save(self, member):
        with self.get_connection() as (client, con):
            s = client.factory.create('synchroMember')
            s.email = member.email
            s.memberUID = 'email:%s' % member.email
            entries = []
            for field in member._meta.fields:
                if field.primary_key: continue
                value = getattr(member, field.name)
                if value is True:
                    value = 1
                if value is False:
                    value = 0
                if value is None:
                    value = ''
                entries.append({'key': field.name.upper(), 'value': value})
            s.dynContent.entry.extend(entries)

            client.service.insertOrUpdateMemberByObj(con, s)


class MessageRemote(Remote):
    """Remote for Message model"""

    wsdl = settings.CCOMMANDER_API_CAMPAIGN_MANAGEMENT_WSDL

    def save(self, message):
        with self.get_connection() as (client, con):
            m = client.factory.create('apiMessage')
            for field in message._meta.fields:
                if field.primary_key:
                    continue

                field_name = field.name
                if hasattr(field, 'remote_name'):
                    remote_field_name = field.remote_name
                else:
                    remote_field_name = field_name

                value = getattr(message, field_name)
                # if model's field value is None, check for a default value in
                # field.remote_default_value which it can be:
                # a value (primitive python value)
                # a callable which receives the api_message and the Message instance
                # an special value DELETE to delete it
                if value is None:
                    if hasattr(field, 'remote_default_value'):
                        value = field.remote_default_value
                        if callable(value):
                            value = value(m, message)
                    else:
                        value = ''

                if value == DELETE:
                    delattr(m, remote_field_name)
                else:
                    setattr(m, remote_field_name, value)
            return client.service.createEmailMessageByObj(con, m)

    def delete(self, message):
        assert False, _('Right now messages cannot be deleted')


class SegmentRemote(Remote):
    """Remote for Segment model"""

    wsdl = settings.CCOMMANDER_API_CAMPAIGN_MANAGEMENT_WSDL

    def save(self, segment):
        with self.get_connection() as (client, con):
            m = client.factory.create('apiSegmentation')
            for field in segment._meta.fields:
                if field.primary_key:
                    continue

                field_name = field.name
                if hasattr(field, 'remote_name'):
                    remote_field_name = field.remote_name
                else:
                    remote_field_name = field_name

                value = getattr(segment, field_name)
                # if model's field value is None, check for a default value in
                # field.remote_default_value which it can be:
                # a value (primitive python value)
                # a callable which receives the api_message and the Segment instance
                # an special value DELETE to delete it
                if value is None:
                    if hasattr(field, 'remote_default_value'):
                        value = field.remote_default_value
                        if callable(value):
                            value = value(m, segment)
                    else:
                        value = ''

                if value == DELETE:
                    delattr(m, remote_field_name)
                else:
                    setattr(m, remote_field_name, value)
            return client.service.segmentationCreateSegment(con, m)

    def delete(self, segment):
        assert False, _('Right now segments cannot be deleted')


class CriteriaRemote(Remote):
    """Remote for Criteria model"""

    wsdl = settings.CCOMMANDER_API_CAMPAIGN_MANAGEMENT_WSDL

    def save(self, criteria):
        with self.get_connection() as (client, con):
            m = client.factory.create('apiStringDemographicCriteria')
            for field in criteria._meta.fields:
                if field.primary_key:
                    continue

                field_name = field.name
                if hasattr(field, 'remote_name'):
                    remote_field_name = field.remote_name
                else:
                    remote_field_name = field_name

                value = getattr(criteria, field_name)
                # if model's field value is None, check for a default value in
                # field.remote_default_value which it can be:
                # a value (primitive python value)
                # a callable which receives the api_message and the criteria instance
                # an special value DELETE to delete it
                if value is None:
                    if hasattr(field, 'remote_default_value'):
                        value = field.remote_default_value
                        if callable(value):
                            value = value(m, criteria)
                    else:
                        value = ''
                elif hasattr(field, 'remote_value'):
                    value = field.remote_value
                    if callable(value):
                        value = value(m, criteria)

                if value == DELETE:
                    delattr(m, remote_field_name)
                else:
                    setattr(m, remote_field_name, value)

            client.service.segmentationAddStringDemographicCriteriaByObj(con, m)

    def delete(self, criteria):
        assert False, _('Right now criterias cannot be deleted')


class NumericCriteriaRemote(Remote):
    """Remote for Criteria model"""

    wsdl = settings.CCOMMANDER_API_CAMPAIGN_MANAGEMENT_WSDL

    def save(self, criteria):
        with self.get_connection() as (client, con):
            m = client.factory.create('apiNumericDemographicCriteria')
            for field in criteria._meta.fields:
                if field.primary_key:
                    continue

                field_name = field.name
                if hasattr(field, 'remote_name'):
                    remote_field_name = field.remote_name
                else:
                    remote_field_name = field_name

                value = getattr(criteria, field_name)
                # if model's field value is None, check for a default value in
                # field.remote_default_value which it can be:
                # a value (primitive python value)
                # a callable which receives the api_message and the criteria instance
                # an special value DELETE to delete it
                if value is None:
                    if hasattr(field, 'remote_default_value'):
                        value = field.remote_default_value
                        if callable(value):
                            value = value(m, criteria)
                    else:
                        value = ''
                elif hasattr(field, 'remote_value'):
                    value = field.remote_value
                    if callable(value):
                        value = value(m, criteria)

                if value == DELETE:
                    delattr(m, remote_field_name)
                else:
                    setattr(m, remote_field_name, value)

            client.service.segmentationAddNumericDemographicCriteriaByObj(con, m)

    def delete(self, criteria):
        assert False, _('Right now criterias cannot be deleted')


class CampaignRemote(Remote):
    """Remote for Campaign model"""

    class PostingError(Exception): pass

    wsdl = settings.CCOMMANDER_API_CAMPAIGN_MANAGEMENT_WSDL

    def save(self, campaign):
        with self.get_connection() as (client, con):
            m = client.factory.create('apiCampaign')
            for field in campaign._meta.fields:
                if field.primary_key:
                    continue

                field_name = field.name
                if hasattr(field, 'remote_name'):
                    remote_field_name = field.remote_name
                else:
                    remote_field_name = field_name

                value = getattr(campaign, field_name)
                # if model's field value is None, check for a default value in
                # field.remote_default_value which it can be:
                # a value (primitive python value)
                # a callable which receives the api_message and the campaign instance
                # an special value DELETE to delete it
                if value is None:
                    if hasattr(field, 'remote_default_value'):
                        value = field.remote_default_value
                        if callable(value):
                            value = value(m, campaign)
                    else:
                        value = ''
                elif hasattr(field, 'remote_value'):
                    value = field.remote_value
                    if callable(value):
                        value = value(m, campaign)

                if value == DELETE:
                    delattr(m, remote_field_name)
                else:
                    setattr(m, remote_field_name, value)

            return client.service.createCampaignByObj(con, m)

    def post(self, campaign):
        with self.get_connection() as (client, con):
            if not client.service.postCampaign(con, campaign.remote_id):
                raise CampaignRemote.PostingError()


class LinkRemote(Remote):
    """Remote for Link model"""

    wsdl = settings.CCOMMANDER_API_CAMPAIGN_MANAGEMENT_WSDL

    def save(self, link):
        with self.get_connection() as (client, con):
            client.service.createAndAddStandardUrl(con, link.message.remote_id,
                                                   link.name, link.url)


class UnsubscribeLinkRemote(Remote):
    """Remote for UnsubscribeLink model"""

    wsdl = settings.CCOMMANDER_API_CAMPAIGN_MANAGEMENT_WSDL

    def save(self, link):
        with self.get_connection() as (client, con):
            message_id = link.message.remote_id
            client.service.createAndAddUnsubscribeUrl(
                con,
                message_id,
                link.name,
                link.url,
                message_id,
                link.error_url,
                message_id
            )


class MirrorLinkRemote(Remote):
    """Remote for MirrorLink model"""

    wsdl = settings.CCOMMANDER_API_CAMPAIGN_MANAGEMENT_WSDL

    def save(self, link):
        with self.get_connection() as (client, con):
            client.service.createAndAddMirrorUrl(con, link.message.remote_id,
                                                 link.name)
