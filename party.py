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
        tryton_badges = cls.search([])
        tryton_badges_dict = {}
        for badge in tryton_badges:
            tryton_badges_dict[badge.code] = badge

        # set of all badge numbers
        tryton_badges_codes = set(b.code for b in tryton_badges)

        Party = Pool().get('party.party')
        tryton_idfiles = Party.search([('badges', '!=', None)])
        tryton_idfiles_dict = {}
        # Create a dictionary of parties
        for idfile in tryton_idfiles:
            tryton_idfiles_dict[idfile.code] = idfile
        tryton_idfiles_codes = set(p.code for p in tryton_idfiles)

        Isonas_connection = Isonasacs(config.get('Isonas', 'host'),
            config.get('Isonas', 'port'))
        Isonas_connection.logon(config.get('Isonas', 'clientid'),
            config.get('Isonas', 'password'))
        isonas_idfile_groupname = config.get('Isonas', 'groupname')

        # get all 'IDFILES' of the tryton_user group
        isonas_tryton_group_idfiles = Isonas_connection.query('GROUP',
            isonas_idfile_groupname)
        # get all 'IDFILES' for updating
        isonas_idfiles_codes = set()
        isonas_idfiles_dict = {}
        for idfile_code in isonas_tryton_group_idfiles:
            isonas_idfiles_codes.add(idfile_code[1])
            isonas_idfiles_dict[idfile_code[1]] = Isonas_connection.query(
                'IDFILE', idfile_code[1])

        # get all the badges from ISONAS controller
        isonas_badges = Isonas_connection.query_all('BADGES')
        isonas_badges_codes = set(badge[0] for badge in isonas_badges)

        idfiles_to_delete = isonas_idfiles_codes - tryton_idfiles_codes
        # XXX Can I delete idfiles that have badges?
        # yes - it will delete the badges too
        for idfile_idstring in idfiles_to_delete:
            Isonas_connection.delete('IDFILE', idfile_idstring)

        idfiles_to_create = tryton_idfiles_codes - isonas_idfiles_codes
        idfiles_to_update = tryton_idfiles_codes - idfiles_to_create
        badges_to_create = tryton_badges_codes - isonas_badges_codes
        badges_to_update = tryton_badges_codes - badges_to_create

        # CREATE
        for idfile_code in idfiles_to_create:
            Isonas_connection.add('IDFILE',
                tryton_idfiles_dict[idfile_code].name.encode('ascii'),
                '', '', idfile_code.encode('ascii'))
            Isonas_connection.add('GROUPS', idfile_code.encode('ascii'),
                isonas_idfile_groupname.encode('ascii'))

        for badge in badges_to_create:
            if tryton_badges_dict[badge].disabled:
                Isonas_connection.add('BADGES',
                    tryton_badges_dict[badge].party.code.encode('ascii'),
                    badge.encode('ascii'), 0, 0, '', '', 2)
            else:
                Isonas_connection.add('BADGES',
                    tryton_badges_dict[badge].party.code.encode('ascii'),
                    badge.encode('ascii'), 0, 0, 0, '', 2)

        # UPDATE idfiles'
        for idfile_code in idfiles_to_update:
            isonasidfile = Isonas_connection.query(
                'IDFILE', idfile_code.encode('ascii'))
            if isonasidfile[0] != tryton_idfiles_dict[idfile_code].name:
                Isonas_connection.update('IDFILE',
                    tryton_idfiles_dict[idfile_code].name.encode('ascii'),
                    '', '', idfile_code.encode('ascii'))

        for badge in badges_to_update:
            if tryton_badges_dict[badge].disabled:
                Isonas_connection.update('BADGES', badge.encode('ascii'), 0, '')
            else:
                Isonas_connection.update('BADGES', badge.encode('ascii'), 0, '')
