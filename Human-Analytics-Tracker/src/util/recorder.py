from colorama import Fore, Style
from abc import abstractmethod
from typing import List, Dict, Callable, Any, Tuple
from rlbot.utils.structures.game_data_struct import GameTickPacket 
from enum import IntEnum
import inputs

XBox360ControllerMapping = {
    'BTN_SOUTH': ('A',     0),
    'BTN_WEST':  ('X',     1),
    'BTN_NORTH': ('Y',     2),
    'BTN_EAST':  ('B',     3),
    'BTN_START': ('Start', 4)
}

class ButtonState(IntEnum):
    """A simple button state for use with the inputs module"""
    Up = 0
    Down = 1

class GenericCallbackState(IntEnum):
    """Determine what state a GenericCallback is in"""
    Begin = 0
    Update = 1
    End = 2
    Max = 2

    def __iadd__(self, value):
        next_value = self.value + value
        if next_value <= self.Max.value:
            next_state = GenericCallbackState(next_value)
        else:
            next_state = GenericCallbackState((next_value % self.Max.value) - 1)
        return next_state

class GenericCallback:
    """Generic callback base class that other callbacks inherit from.
    This allows for a guaranteed single call to begin() and end(), while update()
    can be called numerous times per second."""
    def __init__(self, name: str):
        self.name = name

    def begin(self, packet: GameTickPacket) -> None:
        """
        This function is guaranteed to get called once.
        """
        pass

    def update(self, packet: GameTickPacket) -> None:
        """
        This function may be called multiple times.
        """
        raise NotImplementedError()

    def end(self, packet: GameTickPacket) -> None:
        """
        This function is guaranteed to be called once at the end.
        """
        pass

class SimpleRecorder:
    """
    SimpleRecorder is designed to record human stats using the XBox360 controller.
    This recording can have multiple button configurations and multiple macros (GenericCallbacks).
    """
    def __init__(self, name: str):
        self.name = name
        self.record_hold = False
        self.buttons = [ButtonState.Up for i in range(len(XBox360ControllerMapping))]
        self.sequence: List[str] = []
        self.mapping: Dict[Tuple[str], GenericCallback] = {}
        self.states: Dict[Tuple[str], GenericCallbackState] = {}

    def register(self, sequence: List[str], callback: GenericCallback) -> bool:
        """
        Used for registering a sequence of button presses and a GenericCallback associated with those presses.
        All sequence events also assume the START_BTN is held down (left side of controller).

        Parameters
        ----------
        sequence : List[str]
            A list of button presses, i.e. ['A', 'A', 'B']
        callback : GenericCallback
            Instance of a GenericCallback to use with the associated sequence

        returns True if it registers it, False otherwise
        """
        sequence = tuple(sequence)
        if sequence in self.mapping:
            return False

        self.mapping[sequence] = callback
        return True

    def update(self, packet: GameTickPacket) -> None:
        """
        This is the main method that will be called with the recorder and is designed to be called multiple times/second.
        Different states are handled automatically to guarantee one initial call to begin(), multiple calls to update() and
        a final call to end().

        Parameters
        ----------
        packet : GameTickPacket
            The game packet
        """
        # Perform any callbacks
        self._perform_necessary_callbacks(packet)

        # Track other buttons that are being held
        if self.record_hold:
            events = inputs.devices.gamepads[0].read()
            for event in events:
                # Check to see if a button has transitioned from Down->Up
                if event.code != 'BTN_START' and event.code in XBox360ControllerMapping and event.state == ButtonState.Up:
                    self.sequence.append(XBox360ControllerMapping[event.code][0])
                # Done recording the sequence
                if event.code == 'BTN_START' and event.state == ButtonState.Up:
                    self.record_hold = False
                    sequence = tuple(self.sequence)
                    print(sequence)
                    if sequence in self.mapping:
                        callback = self.mapping[sequence]
                        # If the sequence is not in the states yet, then it hasn't been called. This means
                        # that it will need to call begin(). If it's in there and at the Begin state, then
                        # it will also need to call begin().
                        if sequence not in self.states or self.states[sequence] == GenericCallbackState.Begin:
                            print(Fore.CYAN + f'Detected {[btn for btn in sequence]}. Calling {callback.name}.begin()' + Style.RESET_ALL)
                            self.states[sequence] = GenericCallbackState.Begin
                            callback.begin(packet)
                        # If we are currently in the Update state, then the Update state needs to increment
                        # Note the fall through
                        if self.states[sequence] == GenericCallbackState.Update:
                            self.states[sequence] += 1
                        if self.states[sequence] == GenericCallbackState.End:
                            print(Fore.CYAN + f'Detected {[btn for btn in sequence]}. Calling {callback.name}.end()' + Style.RESET_ALL)
                            callback.end(packet)
                        # Increment the state
                        self.states[sequence] += 1
                    # Reset the sequence we were tracking
                    self.sequence = []
        # Otherwise we need to see if BTN_START is going to be held
        else:
            events = inputs.devices.gamepads[0].read()
            for event in events:
                if event.code == 'BTN_START':
                    self.record_hold = True
                    idx = XBox360ControllerMapping['BTN_START'][1]
                    self.buttons[idx] = ButtonState.Down

    def _perform_necessary_callbacks(self, packet: GameTickPacket) -> None:
        """
        Performs any necessary callbacks that are in the Update state
        """
        for seq, state in self.states.items():
            if state == GenericCallbackState.Update:
                callback = self.mapping[seq]
                callback.update(packet)
