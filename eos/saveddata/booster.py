# ===============================================================================
# Copyright (C) 2010 Diego Duclos
#
# This file is part of eos.
#
# eos is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# eos is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with eos.  If not, see <http://www.gnu.org/licenses/>.
# ===============================================================================

from logbook import Logger

from sqlalchemy.orm import reconstructor, validates

import eos.db
from eos.effectHandlerHelpers import HandledItem
from eos.modifiedAttributeDict import ModifiedAttributeDict, ItemAttrShortcut

pyfalog = Logger(__name__)


class Booster(HandledItem, ItemAttrShortcut):
    def __init__(self, item):
        self.__item = item

        if self.isInvalid:
            raise ValueError("Passed item is not a Booster")

        self.itemID = item.ID if item is not None else None
        self.active = True
        self.build()

    @reconstructor
    def init(self):
        """Initialize a booster from the database and validate"""
        self.__item = None

        if self.itemID:
            self.__item = eos.db.getItem(self.itemID)
            if self.__item is None:
                pyfalog.error("Item (id: {0}) does not exist", self.itemID)
                return

        if self.isInvalid:
            pyfalog.error("Item (id: {0}) is not a Booster", self.itemID)
            return

        self.build()

    def build(self):
        """ Build object. Assumes proper and valid item already set """
        self.__sideEffects = []
        self.__itemModifiedAttributes = ModifiedAttributeDict()
        self.__itemModifiedAttributes.original = self.__item.attributes
        self.__itemModifiedAttributes.overrides = self.__item.overrides
        self.__slot = self.__calculateSlot(self.__item)

        # Legacy booster side effect code, disabling as not currently implemented
        '''
        for effect in self.__item.effects.itervalues():
            if effect.isType("boosterSideEffect"):
                s = SideEffect(self)
                s.effect = effect
                s.active = effect.ID in self.__activeSideEffectIDs
                self.__sideEffects.append(s)
        '''

    # Legacy booster side effect code, disabling as not currently implemented
    '''
    def iterSideEffects(self):
        return self.__sideEffects.__iter__()

    def getSideEffect(self, name):
        for sideEffect in self.iterSideEffects():
            if sideEffect.effect.name == name:
                return sideEffect

        raise KeyError("SideEffect with %s as name not found" % name)
    '''

    @property
    def itemModifiedAttributes(self):
        return self.__itemModifiedAttributes

    @property
    def isInvalid(self):
        return self.__item is None or self.__item.group.name != "Booster"

    @property
    def slot(self):
        return self.__slot

    @property
    def item(self):
        return self.__item

    @staticmethod
    def __calculateSlot(item):
        if "boosterness" not in item.attributes:
            raise ValueError("Passed item is not a booster")

        return int(item.attributes["boosterness"].value)

    def clear(self):
        self.itemModifiedAttributes.clear()

    def calculateModifiedAttributes(self, fit, runTime, forceProjected=False):
        if forceProjected:
            return
        if not self.active:
            return
        for effect in self.item.effects.itervalues():
            if effect.runTime == runTime and \
                    (effect.isType("passive") or effect.isType("boosterSideEffect")) and \
                    effect.activeByDefault:
                effect.handler(fit, self, ("booster",))

        # Legacy booster code, not fully implemented
        '''
        for sideEffect in self.iterSideEffects():
            if sideEffect.active and sideEffect.effect.runTime == runTime:
                sideEffect.effect.handler(fit, self, ("boosterSideEffect",))
        '''

    @validates("ID", "itemID", "ammoID", "active")
    def validator(self, key, val):
        map = {"ID": lambda _val: isinstance(_val, int),
               "itemID": lambda _val: isinstance(_val, int),
               "ammoID": lambda _val: isinstance(_val, int),
               "active": lambda _val: isinstance(_val, bool),
               "slot": lambda _val: isinstance(_val, int) and 1 <= _val <= 3}

        if not map[key](val):
            raise ValueError(str(val) + " is not a valid value for " + key)
        else:
            return val

    def __deepcopy__(self, memo):
        copy = Booster(self.item)
        copy.active = self.active

        # Legacy booster side effect code, disabling as not currently implemented
        '''
        origSideEffects = list(self.iterSideEffects())
        copySideEffects = list(copy.iterSideEffects())
        i = 0
        while i < len(origSideEffects):
            copySideEffects[i].active = origSideEffects[i].active
            i += 1
        '''

        return copy


# Legacy booster side effect code, disabling as not currently implemented
'''
    class SideEffect(object):
        def __init__(self, owner):
            self.__owner = owner
            self.__active = False
            self.__effect = None

        @property
        def active(self):
            return self.__active

        @active.setter
        def active(self, active):
            if not isinstance(active, bool):
                raise TypeError("Expecting a bool, not a " + type(active))

            if active != self.__active:
                if active:
                    self.__owner._Booster__activeSideEffectIDs.append(self.effect.ID)
                else:
                    self.__owner._Booster__activeSideEffectIDs.remove(self.effect.ID)

                self.__active = active

        @property
        def effect(self):
            return self.__effect

        @effect.setter
        def effect(self, effect):
            if not hasattr(effect, "handler"):
                raise TypeError("Need an effect with a handler")

            self.__effect = effect
'''
