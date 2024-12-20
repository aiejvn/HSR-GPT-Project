from skimage.metrics import structural_similarity as ssim
from PIL import Image
import numpy as np
import random
import math
from typing import List, Tuple, Dict
import pytesseract
from scipy import stats

class ScreenReader():
    def __init__(self, debug=False, img__palette_mode='RGB'):
        # Shrunken icons of just the character (pulled from online)
        # Should be similar size to that of bounding box for action space
        self.img_mode = img__palette_mode # RGB or CMYK
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
        pytesseract.pytesseract.tesseract_cmd = r'C:\Users\noten\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'
        
        self.char_metrics = {
            "AVENTURINE": {
                "mean": [187.47268, 173.610284, 163.784928],
                "median": [209, 192, 177],
                "mode": [249, 231, 224]
            },
            "BRONYA": {
                "mean": [171.930812, 157.011252, 163.004484],
                "median": [178, 164, 172],
                "mode": [250, 238, 239]
            },
            "SPARKLE": {
                "mean": [158.114348, 130.871488, 133.941088],
                "median": [155, 109, 118],
                "mode": [253, 242, 239]
            },
            "BLADE": {
                "mean": [131.996096, 119.450136, 121.90904],
                "median": [102, 80,  93],
                "mode": [250, 239, 233]
            },
        }

        
    def ssim_read(self, current_icon) -> str:
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

    def metric_read(self, path:str, metric='median') -> str:
        
        # These colors suck - find better ones
        # TODO: Perform EDA (exploratory data analysis) on color distributions of screenshots w/ chars in them
        # Check mean, median, and mode of images - we want metrics resistant to outliers (likely median & mode)
        # If median &/or mode line up w/ a specific character, then that should be the one
        img = Image.open(scrnsht).convert(screen_reader.img_mode).crop([100, 39, 100+29, 39+62]).resize(size=[500, 500], resample=Image.NEAREST)
        # img.show()
        img = np.array(img)
        
        img = img.reshape([-1, 1, 3]) # all pixels together in one row
        
        mean, median, mode = np.mean(img, axis=0), np.median(img, axis=0), stats.mode(img).mode
        
        mean_median_mode = {
            "mean": mean,
            "median": median, 
            "mode": mode
        }
        actual = mean_median_mode[metric]
        
        # print(np.mean(img, axis=0))
        # print(np.median(img, axis=0))
        # print(stats.mode(img).mode, stats.mode(img).count) # most frequent color found
        
        acceptable_diff = [10] * 3 if self.img_mode == 'RGB' else [10] *4
        for char in self.char_metrics:
            cur_metric = self.char_metrics[char][metric]
            diff = abs(cur_metric - actual)
            if (diff < acceptable_diff).all():
                return char
        
        return "Nobody"

    def read_action_order(self, path: str) -> str:
        # img = Image.open(path)
        # if self.img_mode == 'RGB': img = img.convert('RGB')
        # elif self.img_mode == 'CMYK': img = img.convert('CMYK')
        
        # current_turn = img.crop([73, 17, 73+94, 17+83]) # [left bound, up bound, right bound, low bound]
        # current_turn.show()        
        # current_icon = np.array(current_turn) # np array for calc
        # return self.ssim_read(current_icon)
        
        return self.metric_read(path=path, metric='median')
        
        
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
        acceptable_diff = [30] * 3 if self.img_mode == 'RGB' else [30] * 4
        restricted_color = [99, 60, 45] if self.img_mode == 'RGB' else [14, 42, 102, 0]
        n = 0
        for row in img:
            for elem in row:
                # print(elem)
                if (abs(elem - restricted_color) < acceptable_diff).all():
                    n += 1
        if self.debug: print("Found this many restricted pixels: ", n)
        return n < 100
    
    def read_stage_ability(self, path:str) -> bool:
        # Same as checking ults but just for this
        # Essentially an ult
        img = Image.open(path).convert(self.img_mode)
        img = img.crop([1783, 747, 1783+57, 747+56])
        img = np.array(img)
        
        n = 0
        check_color = [255, 255, 255] if self.img_mode == 'RGB' else [0, 0, 0, 0]
        acceptable_diff = [30] * 3 if self.img_mode == 'RGB' else [30] * 4
        for row in img: # search for white pixels
            for elem in row:
                if (abs(elem - check_color) < acceptable_diff).all():
                    n += 1
        if self.debug: print(f"Found this many white pixels for stage ult:", n)
        
        return n >= 100 # many white pixels -> stage art is shining -> ult is ready
     
    def read_skill_points(self, path:str) -> str:
        # Use tesseract OCR form OpenCv (or any good digit reader from OpenCV) 
        # to read 1 digit numbers from the screen
        # Then pass this to the model
        img = Image.open(path).convert(mode='RGB') # only compatible mode
        
        start = [1399, 1067]
        offset = [142, 43]
        img = img.crop([start[0], start[1], start[0] + offset[0], start[1] + offset[1]])
        
        text = pytesseract.image_to_string(img, config="")
        if text: return text[0]    
        else: return "Could not read skill points."
    
if __name__ == '__main__':
    print("Program is starting...")
    scrnshts = [
        "./screenshots/blade_examples/Screenshot 2024-12-10 193230.png", # Sparkle's turn, Healthy, Can Skill, No ults, no stage ult
        "./screenshots/blade_examples/Screenshot 2024-12-10 193245.png", # Blade's turn, Healthy, Can Skill, No ults, no stage ult
        "./screenshots/blade_examples/Screenshot 2024-12-10 193316.png", # Blade's turn, Healthy, Cannot Skill, No ults, no stage ult
        "./screenshots/blade_examples/Screenshot 2024-12-13 135933.png", # Nobody's turn, Healthy, Can Skill, No ults, no stage ult
        "./screenshots/blade_examples/Screenshot 2024-12-13 141929.png", # Bronya's turn, Not healthy, Can Skill, Just Aventurine (Jade) ult, no stage ult
        "./screenshots/blade_examples/Screenshot 2024-12-17 142415.png", # Blade's turn, Not Healthy, Cannot Skill, All ults, no stage ult
        "./screenshots/blade_examples/Screenshot 2024-12-17 214514.png" # Aventurine's turn, Healthy, Can Skill, All Ults, Stage Ult
    ]
    screen_reader = ScreenReader(debug=True)
    for scrnsht in scrnshts:
        print(f"Reading {scrnsht} ...")
    
        print(f"It is {screen_reader.read_action_order(scrnsht)}'s turn.")
        print(f"Are we healthy? {screen_reader.read_team_health(scrnsht)}")
        print(f"Can we skill? {screen_reader.read_skill_restriction(scrnsht)}")
        print(f"Can we stage ult? {screen_reader.read_stage_ability(scrnsht)}")
        print("We have the following ults:")
        ults = screen_reader.read_ults(scrnsht)
        for char, is_ready in ults:
            print(f"{char}: {is_ready}")
        sp = screen_reader.read_skill_points(scrnsht)
        print(f"We have {sp} skill points." if sp.isnumeric() else "Could not read skill points.")
        
        
        # Find the mean, median, and mode of each char
        # img = Image.open(scrnsht).convert(screen_reader.img_mode).crop([100, 39, 100+29, 39+62]).resize(size=[500, 500], resample=Image.NEAREST)
        # img.show()
        # img = np.array(img)
        
        # img = img.reshape([-1, 1, 3]) # all pixels together in one row
        
        # print(np.mean(img, axis=0))
        # print(np.median(img, axis=0))
        # print(stats.mode(img).mode, stats.mode(img).count) # most frequent color found
        
        # # acceptable difference seems to be 10 for each channel
        
        print("---------------------------")
    