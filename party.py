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
from time import time

__all__ = ['Party', 'Badge']

__metaclass__ = PoolMeta


class Party:
    __name__ = 'party.party'

    @classmethod
    def create(cls, vlist):
        parties = super(Party, cls).create(vlist)

        #pool = Pool()
        #Badge = pool.get('access.control.badge')
        #Badge.isonas_badge_sync([], parties)

        isonas = Isonasacs(
            config.get('Isonas', 'host'), config.get('Isonas', 'port'))
        isonas.logon(
            config.get('Isonas', 'clientid'), config.get('Isonas', 'password'))
        groupname = config.get('Isonas', 'groupname')

        # need to check if parties have badges
        # partiestocreatebadges

        for party in parties:
            if party.badges:
                name = party.name.encode('ascii', 'replace')[:20]
                try:
                    isonas.add('IDFILE', name, '', '', party.code.encode('ascii'))
                    isonas.add('GROUPS', party.code.encode('ascii'), groupname.encode('ascii'))
                except IsonasacsError:
                    print 'Party Create IsonasacsError exception'
                    pass

        return parties

    @classmethod
    def write(cls, *args):
        super(Party, cls).write(*args)
        parties = sum(args[0:None:2], [])

        #pool = Pool()
        #Badge = pool.get('access.control.badge')
        #Badge.isonas_badge_sync([], parties)
        isonas = Isonasacs(
            config.get('Isonas', 'host'), config.get('Isonas', 'port'))
        isonas.logon(
            config.get('Isonas', 'clientid'), config.get('Isonas', 'password'))

        for party in parties:
            if party.badges:
                try:
                    idfile = isonas.query('IDFILE', party.code.encode('ascii'))
                except IsonasacsError:
                    pass
                else:
                    party_name = party.name.encode('ascii', 'replace')
                    if idfile[0] != party_name:
                        isonas.update('IDFILE', party_name, '', '', party.code.encode('ascii'))


class Badge:
    "Isonas Badges/Pins"
    __name__ = 'access.control.badge'

    @classmethod
    def isonas_badge_sync(cls, badges=None, parties=None):
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
        pool = Pool()
        Party = pool.get('party.party')

        start_time = time()

        # get all badges from Tryton
        if badges is None and parties is None:
            tryton_badges = {b.code: b for b in cls.search([])}
        else:
            tryton_badges = {b.code: b for b in badges}

        if badges is None and parties is None:
            tryton_idfiles = {p.code: p
                for p in Party.search([('badges', '!=', None)])}
        else:
            tryton_idfiles = {p.code: p for p in parties}

        isonas = Isonasacs(
            config.get('Isonas', 'host'), config.get('Isonas', 'port'))
        isonas.logon(
            config.get('Isonas', 'clientid'), config.get('Isonas', 'password'))
        groupname = config.get('Isonas', 'groupname')

        print '--- BEFORE IDFILE QUERY %s seconds ---' % (time() - start_time)

        # get all 'IDFILES' of the groupname
        isonas_group_idfiles_codes = set(idfile[1] for idfile in isonas.query('GROUP', groupname))

        print '--- AFTER GROUP QUERY %s seconds ---' % (time() - start_time)

        # get all 'IDFILES' from ISONAS
        isonas_all_idfiles_codes = set(idfile[0] for idfile in isonas.query_all('IDFILE'))

        print '--- AFTER IDFILE QUERY %s seconds ---' % (time() - start_time)

        # get all the badges from ISONAS controller
        isonas_badges = {b[0]: b for b in isonas.query_all('BADGES')}

        print '--- AFTER BADGES QUERY %s seconds ---' % (time() - start_time)

        tryton_idfiles_codes = set(tryton_idfiles.keys())
        tryton_badges_codes = set(tryton_badges.keys())
        isonas_badges_codes = set(isonas_badges.keys())

        # uncomment following section to allow deletion
        # if badges is None and parties is None:
            # idfiles_to_delete = isonas_all_idfiles_codes - tryton_idfiles_codes
        # else:
            # Partial synchronisation so nothing to delete
            #idfiles_to_delete = []

        idfiles_to_create = tryton_idfiles_codes - isonas_all_idfiles_codes
        idfiles_to_update = tryton_idfiles_codes.intersection(isonas_all_idfiles_codes)
        idfiles_to_add_to_group = tryton_idfiles_codes - isonas_group_idfiles_codes
        # idfiles_to_add_to_group = idfiles_to_add_to_group - idfiles_to_create
        badges_to_create = tryton_badges_codes - isonas_badges_codes
        badges_to_update = tryton_badges_codes.intersection(isonas_badges_codes)

        ### DELETE
        # uncomment following section to allow deletion
        # XXX Can I delete idfiles that have badges?
        # yes - it will delete the badges too
        # for idstring in idfiles_to_delete:
            # print '** delete idfile %s' % idstring
            # isonas.delete('IDFILE', idstring)

        ### CREATE
        for code in idfiles_to_create:
            party = tryton_idfiles[code]
            name = party.name.encode('ascii', 'replace')
            isonas.add('IDFILE', name, '', '', code.encode('ascii'))
            # isonas.add('GROUPS', code.encode('ascii'), groupname.encode('ascii'))

        print '--- FINISHED creating idfiles %s seconds ---' % (time() - start_time)

        for code in badges_to_create:
            badge = tryton_badges[code]
            if badge.disabled:
                isonas.add('BADGES', badge.party.code.encode('ascii'), code.encode('ascii'), 0, 0, '', '', 2)
            else:
                isonas.add('BADGES', badge.party.code.encode('ascii'), code.encode('ascii'), 0, 0, 0, '', 2)

        print '--- FINISHED creating badges %s seconds ---' % (time() - start_time)

        #### UPDATE GROUP
        for code in idfiles_to_add_to_group:
            isonas.add('GROUPS', code.encode('ascii'), groupname.encode('ascii'))

        print '--- FINISHED updating groups %s seconds ---' % (time() - start_time)

        ### UPDATE idfiles'
        # get the details of all the IDFILES'
        isonas_idfiles_details = {}
        for idstring in idfiles_to_update:
            isonas_idfiles_details[idstring] = isonas.query('IDFILE', idstring.encode('ascii'))

        for code in idfiles_to_update:
            idfile = isonas_idfiles_details[code]
            party = tryton_idfiles[code]
            party_name = party.name.encode('ascii', 'replace')[:20]
            if idfile[0] != party_name:
                isonas.update('IDFILE', party_name, '', '', code.encode('ascii'))

        for code in badges_to_update:
            badge = tryton_badges[code]
            if badge.disabled:
                isonas.update('BADGES', code.encode('ascii'), 0, 0, '', '')
            else:
                isonas.update('BADGES', code.encode('ascii'), 0, 0, 0, '')

    @classmethod
    def create(cls, vlist):
        badges = super(Badge, cls).create(vlist)
        
        #cls.isonas_badge_sync(badges, [])
        
        isonas = Isonasacs(
            config.get('Isonas', 'host'), config.get('Isonas', 'port'))
        isonas.logon(
            config.get('Isonas', 'clientid'), config.get('Isonas', 'password'))

        for badge in badges:
            if badge.disabled:
                isonas.add('BADGES', badge.party.code.encode('ascii'), badge.code.encode('asci'), 0, 0, '', '', 2)
            else:
                isonas.add('BADGES', badge.party.code.encode('ascii'), badge.code.encode('ascii'), 0, 0, 0, '', 2)

        return badges

    @classmethod
    def write(cls, *args):
        super(Badge, cls).write(*args)
        badges = sum(args[0:None:2], [])
        cls.isonas_badge_sync(badges, [])

        isonas = Isonasacs(
            config.get('Isonas', 'host'), config.get('Isonas', 'port'))
        isonas.logon(
            config.get('Isonas', 'clientid'), config.get('Isonas', 'password'))
        for badge in badges:
            if badge.disabled:
                isonas.update('BADGES', badge.code.encode('ascii'), 0, 0, '', '')
            else:
                isonas.update('BADGES', badge.code.encode('ascii'), 0, 0, 0, '')
