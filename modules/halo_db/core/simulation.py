import datetime

import numpy as np
from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime, LargeBinary
from sqlalchemy.orm import relationship, backref

from . import Base
from .creator import Creator
from .dictionary import DictionaryItem, get_dict_id, get_or_create_dictionary_item
from .. import data_attribute_mapper
from . import current_creator


class Simulation(Base):
    __tablename__ = 'simulations'
    # __table_args__ = {'useexisting': True}

    id = Column(Integer, primary_key=True)
    basename = Column(String)
    creator = relationship(
        Creator, backref=backref('simulations', cascade='all'), cascade='save-update')
    creator_id = Column(Integer, ForeignKey('creators.id'))

    def __init__(self, basename):
        self.basename = basename
        self.creator = current_creator

    def __repr__(self):
        return "<Simulation(\"" + self.basename + "\")>"

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __getitem__(self, i):
        from . import Session
        if isinstance(i, int):
            return self.timesteps[i]
        else:
            session = Session.object_session(self)
            did = get_dict_id(i, session=session)
            try:
                return session.query(SimulationProperty).filter_by(name_id=did,
                                                                   simulation_id=self.id).first().data
            except AttributeError:
                pass

        raise KeyError, i

    def __setitem__(self, st, data):
        from . import Session
        assert isinstance(st, str)
        session = Session.object_session(self)
        name = get_or_create_dictionary_item(session, st)
        propobj = self.properties.filter_by(name_id=name.id).first()
        if propobj is None:
            propobj = session.merge(SimulationProperty(self, name, data))

        propobj.data = data
        session.commit()

    @property
    def path(self):
        return self.basename


class SimulationProperty(Base):
    __tablename__ = 'simulationproperties'

    id = Column(Integer, primary_key=True)
    name_id = Column(Integer, ForeignKey('dictionary.id'))
    name = relationship(DictionaryItem)

    simulation_id = Column(Integer, ForeignKey('simulations.id'))
    simulation = relationship(Simulation, backref=backref('properties', cascade='all, delete-orphan',
                                                          lazy='dynamic', order_by=name_id), cascade='save-update')

    creator_id = Column(Integer, ForeignKey('creators.id'))
    creator = relationship(Creator, backref=backref(
        'simproperties', cascade='all, delete', lazy='dynamic'), cascade='save-update')

    data_float = Column(Float)
    data_int = Column(Integer)
    data_time = Column(DateTime)
    data_string = Column(String)
    data_array = Column(LargeBinary)


    def __init__(self, sim, name, data):
        self.simulation = sim
        self.name = name
        self.data = data
        self.creator = current_creator

    def data_repr(self):
        f = self.data
        if type(f) is float:
            x = "%.2g" % f
        elif type(f) is datetime.datetime:
            x = f.strftime('%H:%M %d/%m/%y')
        elif type(f) is str or type(f) is unicode:
            x = "'%s'" % f
        elif f is None:
            x = "None"
        elif isinstance(f, np.ndarray):
            x = str(f)
        else:
            x = "%d" % f

        return x

    def __repr__(self):
        x = "<SimulationProperty " + self.name.text + \
            " of " + self.simulation.__repr__()
        x += " = " + self.data_repr()
        x += ">"
        return x

    @property
    def data(self):
        return data_attribute_mapper.get_data_of_unknown_type(self)

    @data.setter
    def data(self, data):
        data_attribute_mapper.set_data_of_unknown_type(self, data)