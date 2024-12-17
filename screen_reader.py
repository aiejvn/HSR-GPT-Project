from skimage.metrics import structural_similarity as ssim
from PIL import Image
import numpy as np
import random
import math
from typing import List, Tuple

class ScreenReader():
    def __init__(self, debug=False):
        # Shrunken icons of just the character (pulled from online)
        # Should be similar size to that of bounding box for action space
        self.img_mode = 'CMYK' # RGB or CMYK
        self.icons = {
            "AVENTURINE":"./icons/aventurine-character_icon.png",
            "BRONYA":"./icons/bronya-item-2_icon.png",
            "SPARKLE":"./icons/sparkle-character_icon.png",
            "BLADE":"./icons/blade-character_icon.png",
        }
        
        self.transformed_icons = {} # stores numpy array versions of icons scaled to fit the action space
        
        for char in self.icons:
            char_icon = Image.open(self.icons[char])
            char_icon.thumbnail(size=[94, 83], resample=Image.LANCZOS)
            
            # Create new blank canvas for image
            if self.img_mode == 'RGB':
                new_icon = Image.new('RGB', [94, 83], color=(255, 255, 255))
            elif self.img_mode == 'CMYK':
                new_icon = Image.new('CMYK', [94, 83], color=(0, 0, 0, 0))
            
            # Get offset to center image, paste image onto new canvas
            x_offset = (94 - char_icon.size[0]) // 2
            y_offset = (83 - char_icon.size[1]) // 2
            new_icon.paste(char_icon, (x_offset, y_offset))
            char_icon = new_icon
            
            # char_icon.show()
                        
            char_icon = np.array(char_icon)
            self.transformed_icons[char] = char_icon
        
        
        # Bounding boxes where we can numbers for shield
        # Shield starts on left so we only need to read small left portion
        self.healthbars = [
            [152, 1084, 152+34, 1084+15],
            [378, 1084, 378+34, 1084+15],
            [604, 1084, 604+34, 1084+15],
            [830, 1084, 830+34, 1084+15],
        ]
        self.debug = debug
        
        self.ultimates = {
            "AVENTURINE":[252, 987, 252 + 65, 987 + 61],
            "BRONYA":[478, 986, 478 + 65, 986 + 61],
            "SPARKLE":[704, 987, 704 + 65, 987 + 61],
            "BLADE":[927, 987, 927 + 65, 987 + 61],
        }
        
    def ssim_read(self, path: str) -> str:
        img = Image.open(path)
        if self.img_mode == 'RGB': img = img.convert('RGB')
        elif self.img_mode == 'CMYK': img = img.convert('CMYK')
        
        current_turn = img.crop([73, 17, 73+94, 17+83]) # [left bound, up bound, right bound, low bound]
        
        # current_turn.show()
        
        current_icon = np.array(current_turn) # np array for ssim calc
        # current_icon = cv2.resize(current_icon, self.target_dim)
        
        # TODO: Change to weighted random pick based on ssim indexes
        # cur_char = "Nobody"
        weights = []
        # best_ssim = 0.27 # we want ssim values close to 0 (like cosine similarity). 
        #                 # also, in testing it seems that correct ssim scores are all under 0.28. may need tweaking
        if self.debug: print("SSIM Scores: (Lower is better)")
        
        for char in self.transformed_icons:
            
            # char_icon = cv2.resize(char_icon, self.target_dim)
            char_icon = self.transformed_icons[char]
            
            ssim_index, _ = ssim(current_icon, char_icon, full=True, channel_axis=2)
            ssim_index = abs(ssim_index)
            # if ssim_index < best_ssim:
            #     best_ssim = ssim_index
            #     cur_char = char
            weights.append(1 - ssim_index) # prioritize lower ssim
            if self.debug: print(f"{char}: {ssim_index}")
        
        sum_w = sum(weights)
        remaining = math.ceil(sum_w) - sum_w
        weights.append(remaining) # chance of 'Nobody'
        weights = weights / sum(weights)
        
        population = ['AVENTURINE', 'BRONYA', 'SPARKLE', 'BLADE', 'NOBODY']
        cur_char = random.choices(population, weights, k=1)
        
        if self.debug:
            print("Weights for char selection")
            res = dict(zip(population, weights))
            for key in res:
                print(f"{key}: {res[key]}")
        
        return cur_char[0]

    def read_action_order(self, path: str) -> str:
        # Use cv2 to read whoever is currently going in action order
        # If it matches one of our allies, then it's their turn
        
        # Errors from this function are soft-illegal.
        # Making a sp move on 0 sp cannot ever be done, so it is hard illegal
        # However, using ability as Sparkle when we are actually Aventurine (assuming valid sp) still works - just is unoptimal  
        return self.ssim_read(path)
    
        # Potential Fix - assign each character a color that only appears in their icon (i.e. aventurine - some shade of yellow, bronya, some shade of green)
        # Look for this color in the icons
        
        
    def read_team_health(self, path:str) -> bool:
        # Measure how much white (shield) we see in healthbars
        # If all healthbars have some white, return healthy
        # Otherwise, return unhealthy
        img = Image.open(path).convert(self.img_mode)
        for healthbar in self.healthbars:
            shield_bar = img.crop(healthbar)
            # if self.debug: shield_bar.show()
            shield_bar = np.array(shield_bar)
            
            n = 0
            for row in shield_bar:
                for elem in row:
                    if self.img_mode == 'RGB' and np.equal(elem, np.array([255, 255, 255])).all():
                        n += 1
                    elif self.img_mode == 'CMYK' and np.equal(elem, np.array([0, 0, 0, 0])).all():
                        n += 1
            if self.debug: print(n)
            if n < 36: return False
            
        return True

    def read_ults(self, path:str) -> List[Tuple[str, bool]]:
        img = Image.open(path).convert(self.img_mode)
        res = []
        for char in self.ultimates:
            ult_bar = img.crop(self.ultimates[char])
            # ult_bar.show()
            ult_bar = np.array(ult_bar)
            
            n = 0
            check_color = [255, 255, 255] if self.img_mode == 'RGB' else [0, 0, 0, 0]
            acceptable_diff = [30] * 3 if self.img_mode == 'RGB' else [30] * 4
            for row in ult_bar: # search for white pixels
                for elem in row:
                    if (abs(elem - check_color) < acceptable_diff).all():
                        n += 1
            if self.debug: print(f"Found this many white pixels for {char} ult:", n)
            
            res.append([char, n >= 100]) # many white pixels -> ult art is shining -> ult is ready
            
        return res
    
    def read_skill_restriction(self, path:str) -> bool:
        # Check if [241, 212, 152] (RGB) or [0, 12, 37, 5] (CMYK) in skill window (starts at 1782,936, is 46*46 pixel window)
        img = Image.open(path).convert(self.img_mode)
        img = img.crop([1786, 941, 1786+37, 941+36])
        # img.show()
        img = np.array(img)
        restricted_color = [99, 60, 45] if self.img_mode == 'RGB' else [14, 42, 102, 0]
        n = 0
        for row in img:
            for elem in row:
                # print(elem)
                if np.equal(elem, restricted_color).all():
                    n += 1
        if self.debug: print("Found this many restricted pixels: ", n)
        return n < 2

if __name__ == '__main__':
    scrnshts = [
        "./screenshots/blade_examples/Screenshot 2024-12-10 193230.png", # Sparkle's turn, Healthy, Can Skill, No ults
        "./screenshots/blade_examples/Screenshot 2024-12-10 193245.png", # Blade's turn, Healthy, Can Skill, No ults
        "./screenshots/blade_examples/Screenshot 2024-12-10 193316.png", # Blade's turn, Healthy, Cannot Skill, No ults
        "./screenshots/blade_examples/Screenshot 2024-12-13 135933.png", # Nobody's turn, Healthy, Can Skill, No ults
        "./screenshots/blade_examples/Screenshot 2024-12-13 141929.png", # Bronya's turn, Not healthy, Can Skill, Just Aventurine (Jade) ult
        "./screenshots/blade_examples\Screenshot 2024-12-17 142415.png" # Blade's turn, Not Healthy, Cannot Skill, All ults
    ]
    for scrnsht in scrnshts:
        print(f"Reading {scrnsht} ...")

        # We will internally track skill points.    
        screen_reader = ScreenReader(debug=True)
        print(f"It is {screen_reader.read_action_order(scrnsht)}'s turn.")
        print(f"Are we healthy? {screen_reader.read_team_health(scrnsht)}")
        print(f"Can we skill? {screen_reader.read_skill_restriction(scrnsht)}")
        print("We have the following ults:")
        ults = screen_reader.read_ults(scrnsht)
        for char, is_ready in ults:
            print(f"{char}: {is_ready}")
        print("---------------------------")