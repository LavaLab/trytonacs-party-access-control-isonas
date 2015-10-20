# -*- coding: utf-8 -*-
'''
    trytonlls_party_access_control_isonas.py

    :copyright: The file COPYRIGHT at the top level of this
    :repository contains the full copyright notices.
    :license: , see LICENSE for more details.

'''
from trytond.pool import PoolMeta
from trytond.model import ModelView, ModelSQL, fields
from trytond.config import config
from isonasacs import Isonasacs

__all__ = []

__metaclass__ = PoolMeta

In tryton.cfg create a section called [Isonas]
add "hostname"
add "port"

Class Badge():
    "Isonas Badges/Pins"
    __name__ = 'party.access.control.isonas'


tryton config has 2 utilities - get host name and get port
I can import utilities from tryton.config such as get or gethostname or getport
also getint and getfloat

    @classmethod
    def isonas_badge_sync(cls):
        """
        Method used with Cron to synchronise Tryton Badges with Isonas
        """

        tryton_badges = cls.search([ ]) # get all badges from Tryton
        tryton_badge_numbers = set(b.number for b in tryton_badges) # set of all badge numbers
        tryton_idfiles = set(b.code for b in tryton_badges)


        Isonas_connection = Isonasacs(config.get('Isonas', 'host'), \
            config.get('Isonas', 'port'))
        Isonas_connection.logon(config.get('Isonas', 'clientid'), \
            config.get('Isonas', 'password'))
        #get all 'IDFILES' - these reprensent people in the ISONAS Controller
        idfiles = Isonas_connection.query_all('IDFILES')
        #get all the badges from ISONAS controller
        isonas_badges = Isonas_connection.query_all('BADGES')

        idfiles_to_create = idfiles - 

        badges_to_create = tryton_badge_numbers - isonas_badges
        badges_to_delete = isonas_badges - tryton_badge_numbers

method used by cron to search for all badges and synchronise between Tryton and Isonas
only every 2 or 3 hours.
isonas_
- queryall -> create a set with all the IDS
- create a set from Tryton badges
- check for the difference of the sets ( authority is TRYTON set)
- set of isonas - set of tryton = badges to delete from isonas
- set of tryton - set of isonas = badges to create in isonas
- what about badges to disable....

create a wizard to create a single badge once off

ir.model.data has a method getid(<modulename>,<xmlid>) return id in db

ir.cron( needs id )
nextcall = now or now
