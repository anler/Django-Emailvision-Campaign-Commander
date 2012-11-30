import datetime

from django.db import transaction
from django.db import models
from django.utils.translation import ugettext, ugettext_lazy as _
from django.utils import timezone

from ccommander.fields import StringListField
from ccommander.remotes import (MemberRemote, MessageRemote, LinkRemote,
                                MirrorLinkRemote, UnsubscribeLinkRemote,
                                SegmentRemote, CriteriaRemote,
                                NumericCriteriaRemote, CampaignRemote, DELETE)

def five_minutes_ahead():
    return datetime.datetime.now() + datetime.timedelta(minutes=5)


class RemoteAtomic(object):
    """Mixin for transactional operations with both, models and remotes"""

    def save(self, *args, **kwargs):
        with transaction.commit_on_success(using='ccommander_app'):
            _save = super(RemoteAtomic, self).save
            _save(*args, **kwargs)
            result = self._remote.save(self)
            if hasattr(self, "remote_id"):
                self.remote_id = result
                kwargs.update({'force_insert': False})
                _save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        with transaction.commit_on_success():
            self._remote.delete(self)
            super(RemoteAtomic, self).delete(*args, **kwargs)


class Message(RemoteAtomic, models.Model):
    """Campaign Commander Message

    Message -< Campaign

    The message is the definition of what will be sent. It contains all
    email information such as subject, body, etc.
    A message may contain links you would like to track or specific links
    like online preview, unsubscribe, etc. These links are parte of the
    message and managed in the same object.

    >>> message = Message(
    ...     name="Name",
    ...     subject="Subject",
    ...     description="Description",
    ...     from_name="My site",
    ...     from_email="mysite@mail.com",
    ...     reply_to_name="My site",
    ...     reply_to_email="mysite.contact@mail.com",
    ...     to="[EMV FIELD]EMAIL[EMV /FIELD]",
    ...     body="[EMV TEXTPART] Message body"
    ... )

    """

    EMAIL = 'email'
    SMS = 'sms'
    TYPE_CHOICES = [(EMAIL, _('Email')),
                    (SMS, _('Sms'))]

    remote_id = models.IntegerField(_('Remote ID'), db_index=True, null=True)
    remote_id.remote_name = 'id'
    remote_id.remote_default_value = DELETE

    name = models.CharField(_('Name'), max_length=45)
    subject = models.CharField(_('Subject'), max_length=85)
    description = models.CharField(_('Description'), max_length=255, blank=True)
    encoding = models.CharField(_('Encoding'), max_length=25, default='UTF-8',
                                help_text=_('Message encoding (default UTF-8)'))
    from_name = models.CharField(_('From (Name)'), max_length=45, blank=True)
    from_name.remote_name = 'from'

    from_email = models.CharField(_('From (Email)'), max_length=45, blank=True)
    from_email.remote_name = 'fromEmail'

    reply_to_name = models.CharField(_('Reply To (Name)'), max_length=45, blank=True)
    reply_to_name.remote_name = 'replyTo'

    reply_to_email = models.CharField(_('Reply To (Email)'), max_length=45, blank=True)
    reply_to_email.remote_name = 'replyToEmail'

    to = models.CharField(_('To'), max_length=85,
                          help_text=_('Accepts dynamic values, ex: '
                                      '[EMV FIELD]FIRSTNAME[EMV /FIELD]'))
    type = models.CharField(_('Type'), max_length=25, choices=TYPE_CHOICES,
                            default=EMAIL)
    hotmail_unsub_flag = models.BooleanField(_('Hotmail Unsub Flag'), default=True)
    hotmail_unsub_flag.remote_name = 'hotmailUnsubUrl'

    is_bounceback = models.BooleanField(_('Is bounceback?'), default=False,
                                        help_text=_('Check it if you want to use '
                                                   'this message as a bounce back '
                                                   'message (update, unsubscribe)'))
    is_bounceback.remote_name = 'isBounceback'

    body = models.TextField(_('Body'))
    created_at = models.DateTimeField(auto_now_add=True)
    created_at.remote_name = 'createDate'

    _remote = MessageRemote()

    class Meta:
        verbose_name = _('Message')
        verbose_name_plural = _('Messages')
        ordering = ['-created_at']

    def __unicode__(self):
        return self.name



class Link(RemoteAtomic, models.Model):
    """Campaign Commander Url

    An url may be inserted in a message and can be (the default) tracked

    >>> link = Link(name="CC Mirror", url="http://url")
    """
    name = models.CharField(_('Name'), max_length=255)
    url = models.URLField(_('URL'), null=True, blank=True)
    message = models.ForeignKey(Message)

    _remote = LinkRemote()

    class Meta:
        verbose_name = _('Link')
        verbose_name_plural = _('Links')

    def __unicode__(self):
        return self.url


class MirrorLink(Link):
    """Campaign Commander Mirror Url

    An special url used to view the message in the browser

    >>> mirror = MirrorLink(name="CC Mirror")
    """

    class Meta:
        proxy = True
        verbose_name = _('Mirror Link')
        verbose_name_plural = _('Mirror Links')

    _remote = MirrorLinkRemote()

    def __unicode__(self):
        return "Mirror: %s" % self.url


class UnsubscribeLink(Link):
    """Campaign Commander Unsubscribe Url

    An special url which have only a name an two urls, OK URL and FAIL URL
    used by Campaign Commander to redirect the user when it has been
    unsubscribed

    >>> unsubscribe = UnsubscribeLink(name="Unsubscribe Link",
    ...                               url="...",
    ...                               error_url="...")
    """
    error_url = models.URLField(_('Error URL'))

    class Meta:
        verbose_name = _('Unsubscribe Link')
        verbose_name_plural = _('Unsubscribe Links')

    _remote = UnsubscribeLinkRemote()

    def __unicode__(self):
        return "OK: %s, FAIL: %s" % (self.url, self.error_url)


class Segment(RemoteAtomic, models.Model):
    """Campaign Commander Segment

    Segment -< Campaign

    A segment is a set of criteria used to make a selection of records in the
    user database - the target recipients of the campaign.

    >>> segment = Segment(name="My segment", description="My description")
    """

    ALL = 'ALL'
    PERCENT = 'PERCENT'
    FIX = 'FIX'

    TYPE_CHOICES = [(ALL, 'All'),
                    (PERCENT, 'Percent'),
                    (FIX, 'Fix')]

    remote_id = models.IntegerField(_('Remote ID'), db_index=True, null=True)
    remote_id.remote_name = 'id'
    remote_id.remote_default_value = DELETE

    name = models.CharField(_('Name'), max_length=45)
    description = models.CharField(_('Description'), max_length=255, blank=True)

    sample_rate = models.DecimalField(_('Sample rate'), max_digits=3,
                                      null=True, blank=True, decimal_places=1,
                                      help_text=_('The percentage or number '
                                                  'of members from the segment'))
    sample_rate.remote_name = 'sampleRate'
    sample_rate.remote_default_value = DELETE

    sample_type = models.CharField(_('Sample type'), max_length=45,
                                   default=ALL,
                                   choices=TYPE_CHOICES)
    sample_type.remote_name = 'sampleType'

    created_at = models.DateTimeField(_('Modified'), auto_now_add=True)
    created_at.remote_name = 'dateCreate'

    modified_at = models.DateTimeField(_('Modified'), auto_now=True)
    modified_at.remote_name = 'dateModif'

    class Meta:
        verbose_name = _('Segment')
        verbose_name_plural = _('Segments')
        ordering = ['-created_at']

    _remote = SegmentRemote()

    def __unicode__(self):
        return self.name


class Criteria(RemoteAtomic, models.Model):
    """Campaign Commander Segment Criteria

    SegmentCriteria >- Segment

    Set of criteria to make a selection of records in the user database

    >>> segment = Segment.objects.create(name="My segment")
    >>> criteria = Criteria(column_name="EMAIL",
    ...                     operator="EQUALS",
    ...                     segment=segment,
    ...                     values=["email1", "email2"])
    """

    group_name = models.CharField(_('Group name'), max_length=45,
                                  null=True, blank=True,
                                  help_text=_('The name of the group (less '
                                            'than 20). Only necessary if you '
                                            'want to add the criteria to a '
                                            'group and you want to name it'))
    group_name.remote_name = 'groupName'
    group_name.remote_default_value = DELETE

    order_frag = models.IntegerField(_('Order frag'), null=True)
    order_frag.remote_name = 'orderFrag'
    order_frag.remote_default_value = DELETE

    group_number = models.IntegerField(_('Group number'), null=True, blank=True,
                                help_text=_('The ID of the group. Takes '
                                            'priority over Group name'))
    group_number.remote_name = 'groupNumber'
    group_number.remote_default_value = DELETE

    column_name = models.CharField(_('Column name'), max_length=45, blank=True,
                                help_text=_('Demographic criteria: Name of '
                                            'the column in the database'))
    column_name.remote_name = 'columnName'

    operator = models.CharField(_('Operator'), max_length=45, blank=True,
                                help_text=_('Demographic, action, trackable '
                                            'link, recency, and social criteria: '
                                            'Operator'))
    values = StringListField(_('Values'), blank=True, internal_type='TextField',
                            help_text=_('Demographic aphanumeric (string) '
                                        'and date criteria parameter: '
                                        'The values to which the operator '
                                        'will compare the data in the '
                                        'database field'))
    segment = models.ForeignKey(Segment)
    segment.remote_name = 'id'
    segment.remote_value = lambda remote, criteria: criteria.segment.remote_id

    class Meta:
        verbose_name = _('Criteria')
        verbose_name_plural = _('Criterias')

    _remote = CriteriaRemote()

    def __unicode__(self):
        return "%s %s %s" % (self.column_name, self.operator, self.values)


class NumericCriteria(RemoteAtomic, models.Model):
    """Campaign Commander Segment Numeric Criteria

    SegmentCriteria >- Segment

    Set of criteria to make a selection of records in the user database

    >>> segment = Segment.objects.create(name="My segment")
    >>> criteria = NumericCriteria(column_name="IS_ACTIVE",
    ...                            operator="EQUALS",
    ...                            segment=segment,
    ...                            first_value=1)
    """

    group_name = models.CharField(_('Group name'), max_length=45,
                                  null=True, blank=True,
                                  help_text=_('The name of the group (less '
                                            'than 20). Only necessary if you '
                                            'want to add the criteria to a '
                                            'group and you want to name it'))
    group_name.remote_name = 'groupName'
    group_name.remote_default_value = DELETE

    order_frag = models.IntegerField(_('Order frag'), null=True)
    order_frag.remote_name = 'orderFrag'
    order_frag.remote_default_value = DELETE

    group_number = models.IntegerField(_('Group number'), null=True, blank=True,
                                help_text=_('The ID of the group. Takes '
                                            'priority over Group name'))
    group_number.remote_name = 'groupNumber'
    group_number.remote_default_value = DELETE

    column_name = models.CharField(_('Column name'), max_length=45, blank=True,
                                help_text=_('Demographic criteria: Name of '
                                            'the column in the database'))
    column_name.remote_name = 'columnName'

    operator = models.CharField(_('Operator'), max_length=45, blank=True,
                                help_text=_('Demographic, action, trackable '
                                            'link, recency, and social criteria: '
                                            'Operator'))

    first_value = models.IntegerField()
    first_value.remote_name = 'firstValue'

    second_value = models.IntegerField(null=True, blank=True)
    second_value.remote_name = 'secondValue'
    second_value.remote_default_value = DELETE

    segment = models.ForeignKey(Segment)
    segment.remote_name = 'id'
    segment.remote_value = lambda remote, criteria: criteria.segment.remote_id

    class Meta:
        verbose_name = _('Numeric Criteria')
        verbose_name_plural = _('Numeric Criterias')

    _remote = NumericCriteriaRemote()

    def __unicode__(self):
        return "%s %s %s" % (self.column_name, self.operator, self.values)


class Campaign(RemoteAtomic, models.Model):
    """Campaign Commander Campaign

               / - Segment
    Campaign >-
               \ - Message

    The campaign is the assembly of what will be sent: the message,
    to recipients, the segment, and some extra information like delivery speed,
    etc.
    When the campaign is configured you can test it and post it to start the
    processing.

    >>> message = Message(name="Message",
    ...                   subject="Subject",
    ...                   from_name="MyApp",
    ...                   from_email="contact@myapp.com",
    ...                   reply_to_name="MyApp",
    ...                   reply_to_email="info@myapp.com",
    ...                   to="[EMV FIELD]EMAIL[EMV /FIELD]",
    ...                   body="Body"
    ... )
    >>> segment = Segment.objects.create(name="My Segment")
    >>> criteria = Criteria.objects.create(column_name="EMAIL",
    ...                         operator="EQUALS",
    ...                         values=['email1@email.com', 'email2@mail.com'],
    ...                         segment=segment
    ... )
    >>> campaign = Campaign(
    ...     name="My Campaign",
    ...     url_end_campaign="some url",
    ...     message=message,
    ...     segment=segment
    ... )
    """

    TRACKING = 'TRACKING'
    COMPLETED = 'COMPLETED'
    OTHER = 'OTHER'
    ARCHIVED = 'ARCHIVED'

    LIFE_CHOICES = [(TRACKING, _('Tracking'))]
    STATUS_CHOICES = [(COMPLETED, _('Completed'))]
    STRATEGY_CHOICES = [(OTHER, _('Other'))]
    TARGET_CHOICES = [(OTHER, _('Other'))]
    VALID_CHOICES = [(ARCHIVED, _('Archived'))]

    remote_id = models.IntegerField(_('Remote ID'), db_index=True, null=True,
                                    blank=True)
    remote_id.remote_name = 'id'
    remote_id.remote_default_value = DELETE

    name = models.CharField(_('Name'), max_length=45)
    description = models.CharField(_('Description'), max_length=255,
                                   null=True, blank=True)
    analytics = models.BooleanField(_('Analytics?'), default=False)

    deliver_speed = models.PositiveSmallIntegerField(_('Delivery speed'), default=0)
    deliver_speed.remote_name = 'deliverySpeed'

    dedup_email = models.BooleanField(_('Deduplicate emails when send'), default=True)
    dedup_email.remote_name = 'emaildedupflg'

    life_status = models.CharField(_('Life status'), max_length=45, null=True,
                                   blank=True) # choices=LIFE_CHOICES
    life_status.remote_name = 'lifeStatus'
    life_status.remote_default_value = DELETE

    notify_progress = models.BooleanField(_('Notify progress?'), default=True)
    notify_progress.remote_name = 'notification'

    post_click_tracking = models.BooleanField(_('Post-click tracking?'), default=False)
    post_click_tracking.remote_name = 'postClickTracking'

    send_at = models.DateTimeField(_('Send at'), default=five_minutes_ahead)
    send_at.remote_name = 'sendDate'

    status = models.CharField(_('Status'), max_length=45, null=True, blank=True)
    status.remote_default_value = DELETE

    strategy = models.CharField(_('Strategy'), max_length=45, null=True, blank=True)
    strategy.remote_default_value = DELETE

    target = models.CharField(_('Target'), max_length=45, null=True, blank=True)
    target.remote_default_value = DELETE

    url_end_campaign = models.URLField(_('Url end campaign'),
                                        help_text=_('Where to redirect when '
                                                    'the campaign expires'))
    url_end_campaign.remote_name = 'urlEndCampaign'

    valid = models.CharField(_('Valid'), max_length=45, null=True, blank=True)
    valid.remote_default_value = DELETE

    format = models.CharField(_('Valid'), max_length=45, null=True, blank=True)
    format.remote_default_value = DELETE

    url_host = models.URLField(_('URL host'), null=True, blank=True)
    url_host.remote_name = 'urlHost'
    url_host.remote_default_value = DELETE

    segment_ids = models.CharField(_('Segment IDs'), max_length=250,
                                   null=True, blank=True)
    segment_ids.remote_name = 'segmentIds'
    segment_ids.remote_default_value = DELETE

    segment = models.ForeignKey(Segment)
    segment.remote_name = 'mailinglistId'
    segment.remote_value = lambda remote, camp: camp.segment.remote_id

    message = models.ForeignKey(Message)
    message.remote_name = 'messageId'
    message.remote_value = lambda remote, camp: camp.message.remote_id

    class Meta:
        verbose_name = _('Campaign')
        verbose_name_plural = _('Campaigns')
        ordering = ['-send_at']

    _remote = CampaignRemote()

    def __unicode__(self):
        return self.name

    def post(self):
        self._remote.post(self)


class Member(models.Model):
    """Campaign Commander Member

    Users registered in the database
    """
    email = models.EmailField(_('Email'), db_index=True)
    firstname = models.CharField(_('First name'), max_length=45,
                                 null=True, blank=True)
    lastname = models.CharField(_('Last name'), max_length=45,
                                null=True, blank=True)
    phone = models.CharField(_('Phone'), max_length=25,
                             null=True, blank=True)
    zipcode = models.CharField(_('Zipcode'), max_length=25,
                               null=True, blank=True)
    address = models.CharField(_('Address'), max_length=255,
                               null=True, blank=True)

    company_trade_name = models.CharField(_('Company trade name'),
                                          max_length=255,
                                          null=True, blank=True)
    company_address = models.CharField(_('Company address'), max_length=255,
                                       null=True, blank=True)
    company_zipcode = models.CharField(_('Company zipcode'), max_length=25,
                                       null=True, blank=True)
    company_email = models.CharField(_('Company email'), max_length=255,
                                     db_index=True, null=True, blank=True)
    company_type = models.CharField(_('Company type'), max_length=20, null=True, blank=True)
    cif = models.CharField(_('Company cif'), max_length=12, null=True, blank=True)
    company_activities = models.CharField(_('Company activities'),
                                          max_length=255, null=True, blank=True)
    company_phone = models.CharField(_('Company phone'), max_length=255,
                                     null=True, blank=True)
    is_active = models.BooleanField(_('Active?'), default=False)
    province_id = models.IntegerField(_('Province ID'), null=True, blank=True)
    city_id = models.IntegerField(_('City ID'), null=True, blank=True)
    company_category_id = models.IntegerField(_('Company category ID'),
                                              null=True, blank=True)
    company_province_id = models.IntegerField(_('Company province ID'),
                                              null=True, blank=True)
    company_city_id = models.IntegerField(_('Company city ID'),
                                          null=True, blank=True)

    class Meta:
        verbose_name = _('Member')
        verbose_name_plural = _('Members')

    _remote = MemberRemote()

    def __unicode__(self):
        return self.email

    def rejoin(self):
        self._remote.rejoin(self)

    def unjoin(self):
        self._remote.unjoin(self)

    def save(self, *args, **kwargs):
        result = super(Member, self).save(*args, **kwargs)
        self._remote.save(self)
        return result

    def delete(self, *args, **kwargs):
        result = super(Member, self).delete(*args, **kwargs)
        # We don't remove the remote object (because we can't), we simple set it
        # as inactive
        self.is_active = False
        self._remote.save(self)
        return result

