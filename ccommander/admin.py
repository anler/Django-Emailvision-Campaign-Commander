from django.conf.urls import patterns, url
from django import http
from django.core.urlresolvers import reverse
from django.template.response import TemplateResponse
from django.contrib import admin
from django.contrib import messages
from django.utils.translation import ugettext, ugettext_lazy as _

from ccommander import models, api
from ccommander.models import Message, Segment, Campaign


