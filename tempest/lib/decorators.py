# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import functools
import uuid

import debtcollector.removals
from oslo_log import log as logging
import six
import testtools

LOG = logging.getLogger(__name__)


def skip_because(*args, **kwargs):
    """A decorator useful to skip tests hitting known bugs

    @param bug: bug number causing the test to skip
    @param condition: optional condition to be True for the skip to have place
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapper(self, *func_args, **func_kwargs):
            skip = False
            if "condition" in kwargs:
                if kwargs["condition"] is True:
                    skip = True
            else:
                skip = True
            if "bug" in kwargs and skip is True:
                if not kwargs['bug'].isdigit():
                    raise ValueError('bug must be a valid bug number')
                msg = "Skipped until Bug: %s is resolved." % kwargs["bug"]
                raise testtools.TestCase.skipException(msg)
            return f(self, *func_args, **func_kwargs)
        return wrapper
    return decorator


def related_bug(bug, status_code=None):
    """A decorator useful to know solutions from launchpad bug reports

    @param bug: The launchpad bug number causing the test
    @param status_code: The status code related to the bug report
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapper(self, *func_args, **func_kwargs):
            try:
                return f(self, *func_args, **func_kwargs)
            except Exception as exc:
                exc_status_code = getattr(exc, 'status_code', None)
                if status_code is None or status_code == exc_status_code:
                    LOG.error('Hints: This test was made for the bug %s. '
                              'The failure could be related to '
                              'https://launchpad.net/bugs/%s', bug, bug)
                raise exc
        return wrapper
    return decorator


def idempotent_id(id):
    """Stub for metadata decorator"""
    if not isinstance(id, six.string_types):
        raise TypeError('Test idempotent_id must be string not %s'
                        '' % type(id).__name__)
    uuid.UUID(id)

    def decorator(f):
        f = testtools.testcase.attr('id-%s' % id)(f)
        if f.__doc__:
            f.__doc__ = 'Test idempotent id: %s\n%s' % (id, f.__doc__)
        else:
            f.__doc__ = 'Test idempotent id: %s' % id
        return f
    return decorator


@debtcollector.removals.remove(removal_version='Queen')
class skip_unless_attr(object):
    """Decorator to skip tests if a specified attr does not exists or False"""
    def __init__(self, attr, msg=None):
        self.attr = attr
        self.message = msg or ("Test case attribute %s not found "
                               "or False") % attr

    def __call__(self, func):
        @functools.wraps(func)
        def _skipper(*args, **kw):
            """Wrapped skipper function."""
            testobj = args[0]
            if not getattr(testobj, self.attr, False):
                raise testtools.TestCase.skipException(self.message)
            func(*args, **kw)
        return _skipper


def attr(**kwargs):
    """A decorator which applies the testtools attr decorator

    This decorator applies the testtools.testcase.attr if it is in the list of
    attributes to testtools we want to apply.
    """

    def decorator(f):
        if 'type' in kwargs and isinstance(kwargs['type'], str):
            f = testtools.testcase.attr(kwargs['type'])(f)
        elif 'type' in kwargs and isinstance(kwargs['type'], list):
            for attr in kwargs['type']:
                f = testtools.testcase.attr(attr)(f)
        return f

    return decorator
