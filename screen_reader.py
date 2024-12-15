from skimage.metrics import structural_similarity as ssim
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt

class ScreenReader():
    def __init__(self, debug=False):
        # Shrunken icons of just the character (pulled from online)
        # Should be similar size to that of bounding box for action space
        self.icons = {
            "AVENTURINE":"./icons/aventurine-character_icon.png",
            "BRONYA":"./icons/bronya-item-2_icon.png",
            "SPARKLE":"./icons/sparkle-character_icon.png",
            "BLADE":"./icons/blade-character_icon.png",
        }
        
        # Bounding boxes where we can numbers for shield
        # Shield starts on left so we only need to read small left portion
        self.healthbars = [
            [152, 1084, 152+34, 1084+15],
            [378, 1084, 378+34, 1084+15],
            [604, 1084, 604+34, 1084+15],
            [830, 1084, 830+34, 1084+15],
        ]
        self.debug = debug
        
    def ssim_read(self, path: str) -> str:
        img = Image.open(path)
        current_turn = img.crop([73, 17, 73+94, 17+83]) # [left bound, up bound, right bound, low bound]
        
        # current_turn.show()
        
        current_icon = np.array(current_turn) # np array for ssim calc
        # current_icon = cv2.resize(current_icon, self.target_dim)
        
        cur_char = "Nobody"
        best_ssim = 0.27 # we want ssim values close to 0 (like cosine similarity). 
                        # also, in testing it seems that correct ssim scores are all under 0.28. may need tweaking
        if self.debug: print("SSIM Scores: (Lower is better)")
        for char in self.icons:
            char_icon = Image.open(self.icons[char])
            char_icon.thumbnail(size=[94, 83], resample=Image.LANCZOS)
            
            # Create new blank canvas for image
            new_icon = Image.new('RGB', [94, 83], color=(255, 255, 255))
            
            # Get offset to center image, paste image onto new canvas
            x_offset = (94 - char_icon.size[0]) // 2
            y_offset = (83 - char_icon.size[1]) // 2
            new_icon.paste(char_icon, (x_offset, y_offset))
            char_icon = new_icon
            
            # char_icon.show()
                        
            char_icon = np.array(char_icon)
            # char_icon = cv2.resize(char_icon, self.target_dim)
            
            ssim_index, _ = ssim(current_icon, char_icon, full=True, channel_axis=2)
            if ssim_index < best_ssim:
                best_ssim = ssim_index
                cur_char = char
            if self.debug: print(f"{char}: {ssim_index}")
        
        return cur_char

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
        img = Image.open(path)
        for healthbar in self.healthbars:
            shield_bar = img.crop(healthbar)
            # if self.debug: shield_bar.show()
            shield_bar = np.array(shield_bar)
            
            n = 0
            for row in shield_bar:
                for elem in row:
                    if np.equal(elem, np.array([255, 255, 255])).all():
                        n += 1
            if self.debug: print(n)
            if n < 36: return False
            
        return True


if __name__ == '__main__':
    scrnshts = [
        "./screenshots/blade_examples/Screenshot 2024-12-10 193230.png", # Sparkle's turn, Healthy
        "./screenshots/blade_examples/Screenshot 2024-12-10 193245.png", # Blade's turn, Healthy
        "./screenshots/blade_examples/Screenshot 2024-12-10 193316.png", # Blade's turn, Healthy
        "./screenshots/blade_examples/Screenshot 2024-12-13 135933.png", # Nobody's turn, Healthy
        "screenshots/blade_examples/Screenshot 2024-12-13 141929.png" # Bronya's turn, Not healthy
    ]
    for scrnsht in scrnshts:
        print(f"Reading {scrnsht} ...")

        # We will internally track skill points.    
        screen_reader = ScreenReader(debug=True)
        print(f"It is {screen_reader.read_action_order(scrnsht)}'s turn.")
        print(f"Are we healthy? {screen_reader.read_team_health(scrnsht)}")