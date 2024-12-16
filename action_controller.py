from screen_reader import ScreenReader
from main import Controller
from time import sleep
import mss
from typing import List
import pyautogui # replace with pywin32, connect to window

class Environment():
    
    def __init__(self):
        self.sp = 3
        self.controller = Controller()
        self.screenreader = ScreenReader()
        self.action_keys = {
            "STRONG ATTACK ENEMY":["q"],
            "WEAK ATTACK ENEMY":["q"],
            "BUFF ALLY":["e", "right arrow", "right arrow", "e"], # figuring out how to "find" Blade may be too complex for a non-AI solution. Just stick him at the end and scroll to the end every time.
            "BUFF SELF":["e", "e", "q"], # Blade-exclusive ability. 
            "GIVE ALLIES SHIELD":["e", "e"],
            "ULTIMATE": ["space"] # ideally the controller knows the correct number and tells us. This is a want-to-have.
        }
        self.screenshot_path = None
        
    def make_move(self, keys:List[str])->None:
        for key in keys:
            try:
                print(f"Pressed:{key}")
                pyautogui.press(key)
            except:
                print(f"Could not press {key}. Pressing space instead...")
                pyautogui.press('space')
            sleep(1)
        print("Done pressing keys.")
        
    def alt_tab(self):
        pyautogui.hotkey('alt', 'tab')
        
    def invoke_env(self, take_shot=True):
        # while person at top of order is AVENTURINE, SPARKLE, BRONYA, or BLADE:
        # pass health, sp, char from screenreader to controller
        # interpret output, simulate
        # then wait 5-10 seconds (random or fixed - your preference)
        
        if take_shot:
            self.alt_tab() 
            sleep(5) # in case window switching is slow
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
            
        while True:
            cur_char = self.screenreader.read_action_order(self.screenshot_path)
            print(f"Current character is {cur_char}")
            if cur_char == 'Nobody':
                print("Nobody in team is about to go.")
                # break
                continue
            is_healthy = self.screenreader.read_team_health(self.screenshot_path)
            print(f"Are we healthy?: {is_healthy}\nWe have {self.sp} skill points currently.")
            
            move_full = self.controller.get_move(char=cur_char, is_health_good=is_healthy, sp=self.sp)
            move = self.controller.find_move_in_msg(move_full)
            print(f"We should do: {move} because {move_full}")
            if move in ['BUFF ALLY', 'GIVE ALLIES SHIELD', 'BUFF SELF']:
                self.sp = max(self.sp - 1, 0)
            elif move == 'WEAK ATTACK ENEMY':
                self.sp = max(self.sp + 1, 7)
            self.make_move(self.action_keys[move])
            sleep(5)
    
    def env_test(self):
        # Test if the environment can make proper moves w/o errors
        self.screenshot_path = "./screenshots/blade_examples/Screenshot 2024-12-10 193230.png" # Sparkle's turn, Healthy
        self.invoke_env(take_shot=False)
        
        
if __name__ == "__main__":
    env = Environment()
    # env.env_test()
    env.invoke_env()
    
    