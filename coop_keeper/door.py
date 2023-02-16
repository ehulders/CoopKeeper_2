from __future__ import annotations
from abc import ABC, abstractmethod

from .logger import logger


class Door:
    
    _state = None       # idle, opening, or closing
    _mode = None        # auto or manual
    _position = None    # open or closed

    def __init__(self, state: State, mode: Mode, position: Position) -> None:
        self.set_state(state)
        self.set_mode(mode)
        self.set_position(position)

    def set_state(self, state: State):
        self._state = state
        self._state.door = self
    
    def set_mode(self, mode: Mode):
        self._mode = mode
        self._mode.door = self

    def set_position(self, position: Position):
        self._position = position
        self._position.door = self

    def present_state(self):
        #logger.info(f"CoopKeeper door is {type(self._state).__name__}")
        return type(self._state).__name__

    def present_mode(self):
        #logger.info(f"CoopKeeper mode is {type(self._mode).__name__}")
        return type(self._mode).__name__

    def present_position(self):
        #logger.info(f"CoopKeeper position is {type(self._position).__name__}")
        return type(self._position).__name__

    def push_open_button(self):
        self._state.push_open_button()

    def push_close_button(self):
        self._state.push_close_button()
    
    def hold_open_button(self):
        self._mode.hold_open_button()

    def hold_close_button(self):
        self._mode.hold_close_button()

    def push_both_buttons(self) -> None:
        logger.warning("Oops.. you should press one button at a time")

    def no_button_pushed(self) -> None:
        logger.info("Press any button. Open or close")
    
    def open_trigger(self):
        self._position.open_trigger()
    
    def closed_trigger(self):
        self._position.closed_trigger()

 
class State(ABC):
    @property
    def door(self) -> Door:
        return self._door

    @door.setter
    def door(self, door: Door):
        self._door = door

    @abstractmethod
    def push_open_button(self):
        pass

    @abstractmethod
    def push_close_button(self):
        pass


class Closing(State):
    def push_close_button(self):
        logger.warning(f"CoopKeeper door is already {type(self.door._state).__name__}")
        return f"CoopKeeper door is already {type(self.door._state).__name__}"

    def push_open_button(self):
        logger.info("Door is opening.")
        self.door.set_state(Opening())
        return "Door is opening."


class Opening(State):
    def push_close_button(self):
        logger.info("Door is closing")
        self.door.set_state(Closing())
        return "Door is closing"

    def push_open_button(self):
        logger.warning(f"CoopKeeper door is already {type(self.door._state).__name__}")
        return f"CoopKeeper door is already {type(self.door._state).__name__}"


class Idle(State):
    def push_close_button(self):
        logger.info("Door is closing")
        self.door.set_state(Closing())
        return "Door is closing"

    def push_open_button(self):
        logger.info("Door is opening.")
        self.door.set_state(Opening())
        return "Door is opening."


class Mode(ABC):
    @property
    def door(self) -> Door:
        return self._door

    @door.setter
    def door(self, door: Door):
        self._door = door

    @abstractmethod
    def hold_open_button(self):
        pass

    @abstractmethod
    def hold_close_button(self):
        pass


class Auto(Mode):
    def hold_close_button(self):
        logger.info("CoopKeeper switching to manual.")
        self.door.set_mode(Manual())
        return "CoopKeeper switching to manual."

    def hold_open_button(self):
        logger.info("CoopKeeper switching to manual.")
        self.door.set_mode(Manual())
        return "CoopKeeper switching to manual."


class Manual(Mode):
    def hold_close_button(self):
        logger.info("CoopKeeper switching to auto.")
        self.door.set_mode(Auto())
        return "CoopKeeper switching to auto."

    def hold_open_button(self):
        logger.info("CoopKeeper switching to auto.")
        self.door.set_mode(Auto())
        return "CoopKeeper switching to auto."


class Position(ABC):
    @property
    def door(self) -> Door:
        return self._door

    @door.setter
    def door(self, door: Door):
        self._door = door

    @abstractmethod
    def open_trigger(self):
        pass

    @abstractmethod
    def closed_trigger(self):
        pass


class Open(Position):
    def open_trigger(self):
        logger.warning(f"CoopKeeper door is already {type(self.door._position).__name__}")
        return f"CoopKeeper door is already {type(self.door._position).__name__}"

    def closed_trigger(self):
        logger.info("Door is now closed.")
        self.door.set_position(Closed())
        return "Door is now closed."


class Closed(Position):
    def open_trigger(self):
        logger.info("Door is now open.")
        self.door.set_position(Open())
        return "Door is now open."

    def closed_trigger(self):
        logger.warning(f"CoopKeeper door is already {type(self.door._position).__name__}")
        self.door.set_position(Closed())
        return f"CoopKeeper door is already {type(self.door._position).__name__}"


class Neutral(Position):
    def open_trigger(self):
        logger.info("Door is now open.")
        self.door.set_position(Open())
        return "Door is now open."

    def closed_trigger(self):
        logger.info("Door is now closed.")
        self.door.set_position(Closed())
        return "Door is now closed."