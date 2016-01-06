# -*- coding: utf-8 -*-
'''
    trytonlls_party_access_control_isonas.py

    :copyright: The file COPYRIGHT at the top level of this
    :repository contains the full copyright notices.
    :license: , see LICENSE for more details.

'''
from trytond.pool import PoolMeta, Pool
from trytond.config import config
from isonasacs import Isonasacs

__all__ = ['Badge']

__metaclass__ = PoolMeta


class Badge:
    "Isonas Badges/Pins"
    __name__ = 'access.control.badge'

    @classmethod
    def isonas_badge_sync(cls):
        """
        Method used with Cron to synchronise Tryton Badges with Isonas

        method used by cron to search for all badges and synchronise between
        Tryton and Isonas.
        Currently cron is set every 2 hours.
        isonas_
        - queryall -> create a set with all the IDS
        - create a set from Tryton badges
        - check for the difference of the sets ( authority is TRYTON set)
        - set of isonas - set of tryton = badges to delete from isonas
        - set of tryton - set of isonas = badges to create in isonas
        - what about badges to disable....
        """
        # get all badges from Tryton
        tryton_badges = {b.code: b for b in cls.search([])}

        Party = Pool().get('party.party')
        tryton_idfiles = {p.code: p
            for p in Party.search([('badges', '!=', None)])}

        isonas = Isonasacs(
            config.get('Isonas', 'host'), config.get('Isonas', 'port'))
        isonas.logon(
            config.get('Isonas', 'clientid'), config.get('Isonas', 'password'))
        groupname = config.get('Isonas', 'groupname')

        # get all 'IDFILES' of the groupname
        isonas_idfiles = {}
        for group, idstring in isonas.query('GROUP', groupname):
            isonas_idfiles[idstring] = isonas.query('IDFILE', idstring)

        # get all the badges from ISONAS controller
        isonas_badges = {b[0]: b for b in isonas.query_all('BADGES')}

        tryton_idfiles_codes = set(tryton_idfiles.keys())
        tryton_badges_codes = set(tryton_badges.keys())
        isonas_idfiles_codes = set(isonas_idfiles.keys())
        isonas_badges_codes = set(isonas_badges.keys())

        idfiles_to_delete = isonas_idfiles_codes - tryton_idfiles_codes
        idfiles_to_create = tryton_idfiles_codes - isonas_idfiles_codes
        idfiles_to_update = tryton_idfiles_codes - idfiles_to_create
        badges_to_create = tryton_badges_codes - isonas_badges_codes
        badges_to_update = tryton_badges_codes - badges_to_create

        # XXX Can I delete idfiles that have badges?
        # yes - it will delete the badges too
        for idstring in idfiles_to_delete:
            isonas.delete('IDFILE', idstring)

        # CREATE
        for code in idfiles_to_create:
            party = tryton_idfiles[code]
            name = party.name.encode('ascii', 'replace')
            isonas.add('IDFILE', name, '', '', code)
            isonas.add('GROUPS', code, groupname)

        for code in badges_to_create:
            badge = tryton_badges[code]
            if badge.disabled:
                isonas.add('BADGES', badge.party.code, code, 0, 0, '', '', 2)
            else:
                isonas.add('BADGES', badge.party.code, code, 0, 0, 0, '', 2)

        # UPDATE idfiles'
        for code in idfiles_to_update:
            idfile = isonas_idfiles[code]
            party = tryton_idfiles[code]
            party_name = party.name.encode('ascii', 'replace')
            if idfile[0] != party_name:
                isonas.update('IDFILE', party_name, '', '', code)

        for code in badges_to_update:
            badge = tryton_badges[code]
            if badge.disabled:
                isonas.update('BADGES', code, 0, '')
            else:
                isonas.update('BADGES', code, 0, '')
