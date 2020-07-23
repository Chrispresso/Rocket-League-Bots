from pynput.keyboard import Key, Listener
from pynput import keyboard


from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.messages.flat.QuickChatSelection import QuickChatSelection
from rlbot.utils.structures.game_data_struct import GameTickPacket
from util.recorder import SimpleRecorder, GenericCallback
import time


class HelloWorldCallback(GenericCallback):
    def __init__(self, name: str, agent: BaseAgent):
        super().__init__(name)
        self.agent = agent
        self.updates = 0

    def begin(self) -> None:
        self.begin_time = time.time()

    def update(self, packet: GameTickPacket) -> None:
        print(packet.game_info.seconds_elapsed)
        self.updates += 1

    def end(self) -> None:
        self.end_time = time.time()
        print(f'ran for {self.end_time - self.begin_time}s')



def on_activate_h():
    print('<ctrl>+h pressed')

def on_activate_i():
    print('<ctrl>+i pressed')




class MyBot(BaseAgent):

    def __init__(self, name, team, index):
        super().__init__(name, team, index)
 
        self.potato_recorder = SimpleRecorder()
        self.hello_world_callback = HelloWorldCallback('HelloWorld', self)
        # Register the sequence BTN_START + A + B to HelloWorldCallback
        self.potato_recorder.register(
            '<ctrl>+h',
            self.hello_world_callback
        )
        
    def initialize_agent(self):
        self.potato_recorder.start()
        print('here?')

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        """
        This function will be called by the framework many times per second. This is where you can
        see the motion of the ball, etc. and return controls to drive your car.
        """
        # Set up a simple recorder for tracking player stats
        self.potato_recorder.update(packet)
    
        return SimpleControllerState()
