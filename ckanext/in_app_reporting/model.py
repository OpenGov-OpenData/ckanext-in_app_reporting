import datetime
import json

from six import text_type
from sqlalchemy import Column, types, ForeignKey
from sqlalchemy.orm import class_mapper

try:
    from sqlalchemy.engine import Row
except ImportError:
    try:
        from sqlalchemy.engine.result import RowProxy as Row
    except ImportError:
        from sqlalchemy.engine.base import RowProxy as Row

from ckan import model
from ckan.model.domain_object import DomainObject

try:
    from ckan.plugins.toolkit import BaseModel
except ImportError:
    # CKAN <= 2.9
    from ckan.model.meta import metadata
    from sqlalchemy.ext.declarative import declarative_base

    BaseModel = declarative_base(metadata=metadata)


metabase_mapping_table = None


class MetabaseMapping(DomainObject, BaseModel):
    __tablename__ = "metabase_mapping"

    user_id = Column('user_id', ForeignKey("user.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key = True)
    platform_uuid = Column(types.UnicodeText, nullable=False)
    email = Column(types.UnicodeText, nullable=False)
    group_ids = Column(types.UnicodeText)
    collection_ids = Column(types.UnicodeText)
    created = Column(types.DateTime, default=datetime.datetime.utcnow)
    modified = Column(types.DateTime, default=datetime.datetime.utcnow)

    @classmethod
    def get(cls, **kw):
        '''Finds a single entity in the register.'''
        query = model.Session.query(cls).autoflush(False)
        return query.filter_by(**kw).first()


def table_dictize(obj, context, **kw):
    '''Get any model object and represent it as a dict'''
    result_dict = {}

    if isinstance(obj, Row):
        fields = obj.keys()
    else:
        ModelClass = obj.__class__
        table = class_mapper(ModelClass).mapped_table
        fields = [field.name for field in table.c]

    for field in fields:
        name = field
        value = getattr(obj, name)
        if name == 'extras' and value:
            result_dict.update(json.loads(value))
        elif value is None:
            result_dict[name] = value
        elif isinstance(value, dict):
            result_dict[name] = value
        elif isinstance(value, int):
            result_dict[name] = value
        elif isinstance(value, datetime.datetime):
            result_dict[name] = value.isoformat()
        elif isinstance(value, list):
            result_dict[name] = value
        else:
            result_dict[name] = text_type(value)

    result_dict.update(kw)

    return result_dict
