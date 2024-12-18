from screen_reader import ScreenReader
from main import Controller
from time import sleep
import mss
from typing import List
from pywinauto import Application
from pywinauto.findwindows import find_windows
from key_interface import KeyPress
    
class Environment():
    
    def __init__(self):
        self.sp = 3
        self.controller = Controller(debug=True)
        self.screenreader = ScreenReader()
        self.action_keys = {
            "STRONG ATTACK ENEMY":["q"],
            "WEAK ATTACK ENEMY":["q"],
            "BUFF ALLY":["e", "e"], # game automatically "finds" blade for us
            "BUFF SELF":["e", "e", "q"], # Blade-exclusive ability. 
            "GIVE ALLIES SHIELD":["e", "e"],
            
            "AVENTURINE ULT": ["1", "space"],
            "BRONYA ULT": ["2", "space"],
            "SPARKLE ULT": ["3", "space"],
            "BLADE ULT": ["4", "space"],
            "STAGE ULT": ["r"],
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
            
            "space":0x39,
            
            # some cool hex key codes
            "caps lock":0x3A,
            "f1":0x41
        }
        
    def make_move(self, keys:List[str])->None:
        for key in keys:
            print(f"Pressing:{key}")
            KeyPress(self.key_codes[key])
        print("Done pressing keys.")
                
    def find_hsr(self)->int:
        for handle in find_windows():
            try:
                app = Application().connect(handle=handle)
                window = app.window(handle=handle)
                title = window.window_text()
                if title == 'Honkai\xa0: Star Rail':
                    return handle
            except Exception as e:
                continue
                
    def invoke_env(self, take_shot=True, loop=True):
        # while person at top of order is AVENTURINE, SPARKLE, BRONYA, or BLADE:
        # pass health, sp, char from screenreader to controller
        # interpret output, simulate
        # then wait 5-10 seconds (random or fixed - your preference)
        
        hsr_handle = self.find_hsr()
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
                
                skill_available = self.screenreader.read_skill_restriction(self.screenshot_path)
                print(f"Can we skill?: {skill_available}")
                
                ults = self.screenreader.read_ults(self.screenshot_path)
                for char, is_ready in ults:
                    print(f"{char}: {is_ready}")
                    
                stage_ready = self.screenreader.read_stage_ability(self.screenshot_path)
                if stage_ready: print("Stage ult ready.")
                
                move_full = self.controller.get_move(char=cur_char, is_health_good=is_healthy, sp=self.sp, can_skill=skill_available, ult_status=ults, can_stage=stage_ready)
                move = self.controller.find_move_in_msg(move_full, cur_char)
                print(f"We should do: {move} because {move_full}")
                if move in ['BUFF ALLY', 'GIVE ALLIES SHIELD', 'BUFF SELF']:
                    self.sp = max(self.sp - 1, 0)
                elif move == 'WEAK ATTACK ENEMY':
                    self.sp = min(self.sp + 1, 7)
                elif move == 'SPARKLE ULT':
                    self.sp = min(self.sp + 4, 7)
                self.make_move(self.action_keys[move])
            else:
                print("Nobody in team is about to go.")
            sleep(5) # used to be 3
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
    
    def test_keys(self):
        # Test if we can press keys:
        print("Program is starting...")
        for key in env.action_keys['STAGE ULT']:
            KeyPress(env.key_codes[key])
    
if __name__ == "__main__":
    env = Environment()
    env.invoke_env()
    # env.debug()
    # env.env_test()
    # env.test_keys()