# -*- coding: utf-8 -*-

import click
import datetime
import ckantoolkit as tk
import ckan.model as model
import ckanext.in_app_reporting.utils as utils


def get_commands():
    return [metabase]


@click.group()
def metabase():
    '''metabase commands
    '''
    pass


@metabase.command()
@click.argument(u"user_id", required=True)
@click.option(u'--group_ids', default=[], multiple=True, required=True, help=u'List of group IDs')
@click.option(u'--collection_ids', default=[], multiple=True, required=True, help=u'List of collection IDs')
def add(user_id, group_ids, collection_ids):
    '''
        Create new user metabase_mapping
    '''
    try:
        group_ids_list = group_ids.split(';;')
        collection_ids_list = collection_ids.split(';;')
        utils.metabase_mapping_create({
            'user_id': user_id,
            'group_ids': group_ids_list,
            'collection_ids': collection_ids_list
        })
        click.echo('Metabase mapping created successfully for user_id: {}'.format(user_id))
    except Exception as e:
        tk.error_shout(e)
        raise click.Abort()


@metabase.command()
@click.argument(u"user_id", required=True)
@click.option(u'--group_ids', required=True, help=u'List of group IDs delimited by ";;"')
@click.option(u'--collection_ids', required=True, help=u'List of collection IDs delimited by ";;"')
def update(user_id, group_ids, collection_ids):
    '''
        Update user metabase_mapping
    '''
    try:
        group_ids_list = group_ids.split(';;')
        collection_ids_list = collection_ids.split(';;')
        utils.metabase_mapping_update({
            'user_id': user_id,
            'group_ids': group_ids_list,
            'collection_ids': collection_ids_list
        })
        click.echo('Metabase mapping updated successfully for user_id: {}'.format(user_id))
    except Exception as e:
        tk.error_shout(e)
        raise click.Abort()


@metabase.command()
@click.argument(u"user_id", required=True)
def remove(user_id):
    '''
        Remove user metabase_mapping
    '''
    try:
        utils.metabase_mapping_delete({'user_id': user_id})
        click.echo('Metabase mapping removed successfully for user_id: {}'.format(user_id))
    except Exception as e:
        tk.error_shout(e)
        raise click.Abort()
