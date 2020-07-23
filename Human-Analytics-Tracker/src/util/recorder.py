from colorama import Fore, Style
from abc import abstractmethod
from rlbot.utils.structures.game_data_struct import GameTickPacket
from typing import List, Dict, Callable, Any, Tuple
from enum import IntEnum
from pynput import keyboard


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

    def begin(self) -> None:
        """
        This function is guaranteed to get called once.
        """
        pass

    def update(self, packet: GameTickPacket) -> None:
        """
        This function may be called multiple times.
        """
        raise NotImplementedError()

    def end(self) -> None:
        """
        This function is guaranteed to be called once at the end.
        """
        pass

class SimpleRecorder:
    """
    SimpleRecorder is designed to record human stats using the XBox360 controller.
    This recording can have multiple key configurations and multiple macros (GenericCallbacks).
    """
    def __init__(self):
        self.mapping: Dict[str, GenericCallback] = {}
        self.update_func = {}  # @TODO: Make this part better. No need to have another mapping here
        self.states: Dict[str, GenericCallbackState] = {}
        self.started = False
        self.ghk = None

    def register(self, sequence: str, callback: GenericCallback) -> bool:
        """
        Used for registering a sequence of keys pressed and a GenericCallback associated with those presses.

        Parameters
        ----------
        sequence : str
            The sequence of keys, i.e. "<ctrl>+s" or "<ctrl>+<alt>+a"
        callback : GenericCallback
            Instance of a GenericCallback to use with the associated sequence

        returns True if it registers it, False otherwise
        """
        if sequence in self.mapping:
            return False

        self.states[sequence] = GenericCallbackState.Begin  # Initialize to a Begin state

        def _begin():
            print(Fore.CYAN + f'Detected {sequence}. Calling {callback.name}.begin()' + Style.RESET_ALL)
            callback.begin()
        
        def _end():
            print(Fore.CYAN + f'Detected {sequence}. Calling {callback.name}.end()' + Style.RESET_ALL)
            callback.end()

        # A function which alternates between the begin() and end() function
        def register_callback():
            while True:
                # The first call will change state from Begin -> Update
                self.states[sequence] += 1
                yield _begin()
                # Because Update has already been running a number of times, we need
                # to go from Update -> End
                self.states[sequence] += 1
                yield _end()
                # The next call will transition back to Begin
                self.states[sequence] = GenericCallbackState.Begin
            
        # By setting the mapping to the register_callback above,
        # I can guarantee alternating between begin() and end() using yield.
        _callback = register_callback()
        self.mapping[sequence] = lambda: next(_callback)
        # This is the update function that will actually get called multiple times per second
        self.update_func[sequence] = callback.update
        return True

    def start(self) -> None:
        """
        Sets up the listeners
        """
        # If you try calling start() multiple times, you will have two listener threads.
        # Because  that is not desired, check to see if this thread has started already and restart if needed.
        if self.started:
            self.ghk.stop()
        self.ghk = keyboard.GlobalHotKeys(self.mapping)
        self.ghk.start()
        self.started = True


    def update(self, packet: GameTickPacket) -> None:
        """
        Performs any necessary callbacks that are in the Update state
        """
        for seq, state in self.states.items():
            if state == GenericCallbackState.Update:
                callback_update = self.update_func[seq]
                callback_update(packet)