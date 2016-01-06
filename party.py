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
        isonas_idfile_groupname = config.get('Isonas', 'groupname')

        # get all 'IDFILES' of the tryton_user group
        isonas_tryton_group_idfiles = isonas.query('GROUP',
            isonas_idfile_groupname)
        # get all 'IDFILES' for updating
        isonas_idfiles_codes = set()
        isonas_idfiles_dict = {}
        for idfile_code in isonas_tryton_group_idfiles:
            isonas_idfiles_codes.add(idfile_code[1])
            isonas_idfiles_dict[idfile_code[1]] = isonas.query(
                'IDFILE', idfile_code[1])

        # get all the badges from ISONAS controller
        isonas_badges = isonas.query_all('BADGES')
        isonas_badges_codes = set(badge[0] for badge in isonas_badges)

        tryton_codes = set(tryton_badges.keys())
        tryton_idfiles_codes = set(tryton_idfiles.keys())

        idfiles_to_delete = isonas_idfiles_codes - tryton_idfiles_codes
        idfiles_to_create = tryton_idfiles_codes - isonas_idfiles_codes
        idfiles_to_update = tryton_idfiles_codes - idfiles_to_create
        badges_to_create = tryton_codes - isonas_badges_codes
        badges_to_update = tryton_codes - badges_to_create

        # XXX Can I delete idfiles that have badges?
        # yes - it will delete the badges too
        for idfile_idstring in idfiles_to_delete:
            isonas.delete('IDFILE', idfile_idstring)

        # CREATE
        for idfile_code in idfiles_to_create:
            isonas.add('IDFILE',
                tryton_idfiles[idfile_code].name.encode('ascii'),
                '', '', idfile_code.encode('ascii'))
            isonas.add('GROUPS', idfile_code.encode('ascii'),
                isonas_idfile_groupname.encode('ascii'))

        for badge in badges_to_create:
            if tryton_badges[badge].disabled:
                isonas.add('BADGES',
                    tryton_badges[badge].party.code.encode('ascii'),
                    badge.encode('ascii'), 0, 0, '', '', 2)
            else:
                isonas.add('BADGES',
                    tryton_badges[badge].party.code.encode('ascii'),
                    badge.encode('ascii'), 0, 0, 0, '', 2)

        # UPDATE idfiles'
        for idfile_code in idfiles_to_update:
            isonasidfile = isonas.query(
                'IDFILE', idfile_code.encode('ascii'))
            if isonasidfile[0] != tryton_idfiles[idfile_code].name:
                isonas.update('IDFILE',
                    tryton_idfiles[idfile_code].name.encode('ascii'),
                    '', '', idfile_code.encode('ascii'))

        for badge in badges_to_update:
            if tryton_badges[badge].disabled:
                isonas.update('BADGES', badge.encode('ascii'), 0, '')
            else:
                isonas.update('BADGES', badge.encode('ascii'), 0, '')
