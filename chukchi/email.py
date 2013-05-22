# This file is part of Chukchi, the free web-based RSS aggregator
#
#   Copyright (C) 2013 Edward Toroshchin <chukchi-project@hades.name>
#
# Chukchi is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Chukchi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# Please see the file COPYING in the root directory of this project.
# If you are unable to locate this file, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import

import logging
import smtplib

from email.mime.text import MIMEText

from .config import config

LOG = logging.getLogger(__name__)

def send_email(from_, to, subject, text):
    to_email = None
    if isinstance(to, (str, unicode)):
        to_email = to
    elif hasattr(to, 'email'):
        to_email = to.email

    if isinstance(to_email, unicode):
        to_email = to_email.encode('utf-8')
    if isinstance(subject, unicode):
        subject = subject.encode('utf-8')

    if not to_email:
        LOG.error("no address specified for recipient %s", to)
        return
    msg = MIMEText(text)
    msg.set_charset('utf-8')
    msg['Subject'] = subject
    msg['From'] = from_
    msg['To'] = to_email

    try:
        s = smtplib.SMTP(config.EMAIL_HOST)
        s.sendmail(from_, [to_email], msg.as_string())
        s.quit()
        return True
    except smtplib.SMTPException:
        LOG.exception("error sending email to %s", to)
        return False

# vi: sw=4:ts=4:et
