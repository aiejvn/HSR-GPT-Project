from screen_reader import ScreenReader
from main import Controller
from time import sleep
import mss
from typing import List
from pywinauto import Application
from pywinauto.findwindows import find_windows
import ctypes, time

# Issue with using pywinauto and related: Keyboard input shows when editing profile, but not when in combat
    # Game looks for input on lower level than these programs are outputting it on - that is why it only shows in dialogue boxes
    # e.g. Console, Chat, Profile Editing
    # and NOT gameplay
# Credit to u/DanielShawww (https://www.reddit.com/r/learnpython/comments/22tke1/use_python_to_send_keystrokes_to_games_in_windows/?rdt=50240) for the following solution
# Note that the following hex codes follow Quartz Events key codes

# Bunch of stuff so that the script can send keystrokes to game 

SendInput = ctypes.windll.user32.SendInput

# C struct redefinitions 
PUL = ctypes.POINTER(ctypes.c_ulong)
class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort),
                ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong),
                ("wParamL", ctypes.c_short),
                ("wParamH", ctypes.c_ushort)]

class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time",ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput),
                 ("mi", MouseInput),
                 ("hi", HardwareInput)]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ii", Input_I)]

# Actuals Functions

def PressKey(hexKeyCode):
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.ki = KeyBdInput( 0, hexKeyCode, 0x0008, 0, ctypes.pointer(extra) )
    x = Input( ctypes.c_ulong(1), ii_ )
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

def ReleaseKey(hexKeyCode):
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.ki = KeyBdInput( 0, hexKeyCode, 0x0008 | 0x0002, 0, ctypes.pointer(extra) )
    x = Input( ctypes.c_ulong(1), ii_ )
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

def KeyPress(hex:int):
    time.sleep(1)
    PressKey(hex) # press key
    time.sleep(.05)
    ReleaseKey(hex) #release key
    
class Environment():
    
    def __init__(self):
        self.sp = 3
        self.controller = Controller()
        self.screenreader = ScreenReader()
        self.action_keys = {
            "STRONG ATTACK ENEMY":["q"],
            "WEAK ATTACK ENEMY":["q"],
            "BUFF ALLY":["e", "d", "d", "e"], # figuring out how to "find" Blade may be too complex for a non-AI solution. Just stick him at the end and scroll to the end every time.
            "BUFF SELF":["e", "e", "q"], # Blade-exclusive ability. 
            "GIVE ALLIES SHIELD":["e", "e"],
            "ULTIMATE": ["space"] # ideally the controller knows the correct number and tells us. This is a want-to-have.
        }
        self.screenshot_path = None
        self.key_codes = {
            "1":0x2,
            "2":0x3,
            "3":0x4,
            "4":0x5,
            "7":0x8,
            "8":0x9,

            "q":0x10,
            "w":0x11,
            "e":0x12,
            "r":0x13, # q, w, and r here to show pattern in key bindings
            "d":0x20,
            "space":0x31
        }
        
    def make_move(self, keys:List[str])->None:
        for key in keys:
            print(f"Pressing:{key}")
            KeyPress(self.key_codes[key])
        print("Done pressing keys.")
                
    def invoke_env(self, take_shot=True, loop=True):
        # while person at top of order is AVENTURINE, SPARKLE, BRONYA, or BLADE:
        # pass health, sp, char from screenreader to controller
        # interpret output, simulate
        # then wait 5-10 seconds (random or fixed - your preference)
        
        # hsr_handle = 657578 # debug window
        hsr_handle = 1508766
        app = Application().connect(handle=hsr_handle)
        window = app.window(handle=hsr_handle)
        window.set_focus() # bring to front - no need for alt-tabbing
        print("Connected to a Honkai Star Rail window.")
        sleep(5)
        
        i = 0
        while i < 10:
            if take_shot: 
                with mss.mss() as screenshot:
                    try:
                        self.screenshot_path = "./screenshots/cur_shot.png"
                    except:
                        print("Could not find screenshots folder. Putting image in main instead...")
                        self.screenshot_path = "./cur_shot.png"
                    screenshot.shot(
                        mon=1, # default is 1st monitor
                        output = self.screenshot_path # save to path
                    )
            
            cur_char = self.screenreader.read_action_order(self.screenshot_path)
            print(f"Current character is {cur_char}")
            if cur_char != 'NOBODY':
                is_healthy = self.screenreader.read_team_health(self.screenshot_path)
                print(f"Are we healthy?: {is_healthy}\nWe have {self.sp} skill points currently.")
                
                move_full = self.controller.get_move(char=cur_char, is_health_good=is_healthy, sp=self.sp)
                move = self.controller.find_move_in_msg(move_full)
                print(f"We should do: {move} because {move_full}")
                if move in ['BUFF ALLY', 'GIVE ALLIES SHIELD', 'BUFF SELF']:
                    self.sp = max(self.sp - 1, 0)
                elif move == 'WEAK ATTACK ENEMY':
                    self.sp = min(self.sp + 1, 7)
                self.make_move(self.action_keys[move])
            else:
                print("Nobody in team is about to go.")
            sleep(3)
            if not loop: i += 1
    
    def env_test(self, loop=True):
        # Test if the environment can make proper moves w/o errors
        self.screenshot_path = "./screenshots/blade_examples/Screenshot 2024-12-10 193230.png" # Sparkle's turn, Healthy
        self.invoke_env(take_shot=False, loop=loop)

    def debug(self):        
        # Get all window handles and titles
        print("Available windows to connect to:")
        windows = []
        for handle in find_windows():
            try:
                app = Application().connect(handle=handle)
                window = app.window(handle=handle)
                title = window.window_text()
                if title:
                    windows.append((handle, title))
            except Exception as e:
                continue

        # Display the list of window handles and titles
        print(f"Handles are {type(windows[0][0])} type.")
        for handle, title in windows:
            print(f"Handle: {handle}, Title: '{title}'")
        print("------------------------------------")
        env.env_test(loop=False)
    
    def test_buff_ally(self):
        # Test if we can press keys:
        print("Program is starting...")
        for key in env.action_keys['BUFF ALLY']:
            KeyPress(env.key_codes[key])
    
if __name__ == "__main__":
    env = Environment()
    env.invoke_env()
    