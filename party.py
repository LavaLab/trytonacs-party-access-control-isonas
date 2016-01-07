# -*- coding: utf-8 -*-
'''
    trytonlls_party_access_control_isonas.py

    :copyright: The file COPYRIGHT at the top level of this
    :repository contains the full copyright notices.
    :license: , see LICENSE for more details.

'''
from trytond.pool import PoolMeta, Pool
from trytond.model import ModelView, ModelSQL, fields
from trytond.config import config
from isonasacs import Isonasacs
from time import time

__all__ = ['Badge']

__metaclass__ = PoolMeta


class Badge:
    "Isonas Badges/Pins"
    __name__ = 'access.control.badge'

    recent_events = fields.Function(
        fields.text('Recent Events'),
        getter="get_recent_isonas_events",
    )

    def get_recent_isonas_events(self):
        """
        Method used by function field to return a list of 
        recent events for a particular party.
        """
        print 'connect to ISONAS'
        Isonas_connection = Isonasacs(config.get('Isonas', 'host'), \
             config.get('Isonas', 'port'))
        Isonas_connection.logon(config.get('Isonas', 'clientid'), \
            config.get('Isonas', 'password'))
        startdate = 
        starttime = 
        enddate = 
        endtime = 

        Isonas_connection.query('HISTORY',startdate,starttime,enddate,endtime,'FILTERIDFILE',self.party.code)



    @classmethod
    def isonas_badge_sync(cls):
        """
        Method used with Cron to synchronise Tryton Badges with Isonas

        method used by cron to search for all badges and synchronise between Tryton and Isonas.
        Currently cron is set every 2 hours.
        isonas_
        - queryall -> create a set with all the IDS
        - create a set from Tryton badges
        - check for the difference of the sets ( authority is TRYTON set)
        - set of isonas - set of tryton = badges to delete from isonas
        - set of tryton - set of isonas = badges to create in isonas
        - what about badges to disable....
        """
        start_time = time()
        tryton_badges = cls.search([ ]) # get all badges from Tryton
        tryton_badges_dict = {}
        print '#### CREATE badge dictionary'
        for badge in tryton_badges:
            tryton_badges_dict[badge.code] = badge

        tryton_badges_codes = set(b.code for b in tryton_badges) # set of all badge numbers

        Party = Pool().get('party.party')
        tryton_idfiles = Party.search([('badges', '!=', None)])
        tryton_idfiles_dict = {}
        ## Create a dictionary of parties
        for idfile in tryton_idfiles:
            tryton_idfiles_dict[idfile.code] = idfile
        tryton_idfiles_codes = set(p.code for p in tryton_idfiles)
        #print 'tryton_idfiles_codes %s' % tryton_idfiles_codes

        print 'connect to ISONAS'
        Isonas_connection = Isonasacs(config.get('Isonas', 'host'), \
             config.get('Isonas', 'port'))
        Isonas_connection.logon(config.get('Isonas', 'clientid'), \
            config.get('Isonas', 'password'))
        isonas_idfile_groupname = config.get('Isonas','groupname')

        # get all 'IDFILES' of the tryton_user group
        isonas_tryton_group_idfiles = Isonas_connection.query('GROUP', \
            isonas_idfile_groupname)
        # get al 'IDFILES' for updating
        isonas_all_idfiles = Isonas_connection.query_all('IDFILE')
        isonas_idfiles_codes = set()
        isonas_idfiles_dict = {}
        for idfile_code in isonas_tryton_group_idfiles:
            isonas_idfiles_codes.add(idfile_code[1])
            isonas_idfiles_dict[idfile_code[1]] = Isonas_connection.query('IDFILE',idfile_code[1])

        # get all the badges from ISONAS controller
        isonas_badges = Isonas_connection.query_all('BADGES')
        isonas_badges_codes = set(badge[0] for badge in isonas_badges)

        idfiles_to_delete = isonas_idfiles_codes - tryton_idfiles_codes
        # !!!! Can I delete idfiles that have badges? yes - it will delete the badges too
        for idfile_idstring in idfiles_to_delete:
            #print 'idfile_idstring %s ' % idfile_idstring
            Isonas_connection.delete('IDFILE', idfile_idstring)

        # print '#### badges to delete'
        # for badge in badges_to_delete:
        #    print 'badge %s' % badge
        #     Isonas_connection.delete('BADGES', badge)

        idfiles_to_create = tryton_idfiles_codes - isonas_idfiles_codes
        idfiles_to_update = tryton_idfiles_codes - idfiles_to_create
        badges_to_create = tryton_badges_codes - isonas_badges_codes
        badges_to_update = tryton_badges_codes - badges_to_create

        ##### CREATE ######
        print '#### CREATE IDFILES'
        for idfile_code in idfiles_to_create:
            Isonas_connection.add('IDFILE', tryton_idfiles_dict[idfile_code].name.encode('ascii'),'','',idfile_code.encode('ascii'))
            Isonas_connection.add('GROUPS', idfile_code.encode('ascii'), isonas_idfile_groupname.encode('ascii'))
        
        print '--- %s seconds ---' % (time() - start_time)

        print '#### CREATE BADGES'
        for badge in badges_to_create:
            badgestatus = tryton_badges_dict[badge].disabled
            if tryton_badges_dict[badge].disabled:
                Isonas_connection.add('BADGES', tryton_badges_dict[badge].party.code.encode('ascii'), badge.encode('ascii'), 0, 0,'','',2 )
            else:
                Isonas_connection.add('BADGES', tryton_badges_dict[badge].party.code.encode('ascii'), badge.encode('ascii'), 0, 0,0,'',2)
        
        print '--- %s seconds ---' % (time() - start_time)
        
        #### UPDATE idfiles'
        print '#### UPDATE IDFILES'
        for idfile_code in idfiles_to_update:
            isonasidfile = Isonas_connection.query('IDFILE', idfile_code.encode('ascii') )
            if isonasidfile[0] != tryton_idfiles_dict[idfile_code].name:
                Isonas_connection.update('IDFILE',tryton_idfiles_dict[idfile_code].name.encode('ascii'),'','', idfile_code.encode('ascii') )

        print '--- %s seconds ---' % (time() - start_time)

        print '#### UPDATE badges'
        for badge in badges_to_update:
            if tryton_badges_dict[badge].disabled:
                Isonas_connection.update('BADGES',badge.encode('ascii'),0,'',)
            else:
               Isonas_connection.update('BADGES',badge.encode('ascii'),0,'',)

        print '--- %s seconds ---' % (time() - start_time)

    # @classmethod
    # def create(cls, vlist):
    #     """
    #     ir.cron( needs id )
    #     nextcall = now or now
    #     ir.model.data has a method getid(<modulename>,<xmlid>) return id in db
    #     """
    #     Sequence = Pool().get('ir.sequence')
    #     Configuration = Pool().get('party.access.control.isonas.configuration')

    #     vlist = [x.copy() for x in vlist]
    #     for values in vlist:
    #         if not values.get('code'):
    #             config = Configuration(1)
    #             values['code'] = Sequence.get_id(config.party_sequence.id)
    #         values.setdefault('addresses', None)
    #     return super(Party, cls).create(vlist)