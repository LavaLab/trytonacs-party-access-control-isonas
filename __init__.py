# -*- coding: utf-8 -*-
"""
    trytonlls_party_access_control_isonas

    :copyright: (c) The file COPYRIGHT at the top level of this
    :repository contains the full copyright notices.
    :license: BSD, see LICENSE for more details.
"""
from trytond.pool import Pool

from .party import Badge, Party

def register():
    Pool.register(
        Party,
        Badge,
        module='party_access_control_isonas', type_='model'
    )
