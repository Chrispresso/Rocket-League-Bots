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

    def begin(self, packet: GameTickPacket) -> None:
        self.begin_time = time.time()

    def update(self, packet: GameTickPacket) -> None:
        self.updates += 1

    def end(self, packet: GameTickPacket) -> None:
        self.end_time = time.time()
        print(f'ran for {self.end_time - self.begin_time}s')



def on_activate_h():
    print('<ctrl>+h pressed')

def on_activate_i():
    print('<ctrl>+i pressed')




class MyBot(BaseAgent):

    def __init__(self, name, team, index):
        super().__init__(name, team, index)
        with keyboard.GlobalHotKeys({
            '<ctrl>+h': on_activate_h,
            '<ctrl>+i': on_activate_i}) as h:
            h.join()



        self.potato_recorder = SimpleRecorder('Potato')
        self.hello_world_callback = HelloWorldCallback('HelloWorld', self)
        # Register the sequence BTN_START + A + B to HelloWorldCallback
        self.potato_recorder.register(
            ['A', 'B'],
            self.hello_world_callback
        )
        
    def initialize_agent(self):
        pass

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        """
        This function will be called by the framework many times per second. This is where you can
        see the motion of the ball, etc. and return controls to drive your car.
        """
        # Set up a simple recorder for tracking player stats
        self.potato_recorder.update(packet)
    
        return SimpleControllerState()
