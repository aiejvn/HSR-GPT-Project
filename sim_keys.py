import pyautogui
import time

import pyautogui


def simulate_key_input(key_input: str):
    """
    Simulates pressing a single key or a combination of keys.

    Parameters:
    key_input (str): The key or combination of keys to simulate pressing.
                     For combinations, keys should be separated by spaces. Example: 'ctrl home'
    """
    try:
        keys = key_input.split()
        
        # print(f"We will used to be pressing: {keys}")
        # for i in range(len(keys)):
        #     if keys[i] == ' ' or keys[i] == '(space)': keys[i] == 'space' 
        #     elif keys[i] == ",": keys[i] == 'comma' 
        #     elif keys[i] == ".": keys[i] == 'period' 
        #     elif keys[i] == "\n": keys[i] == 'enter' 
        
        # print(f"We will now be pressing: {keys}")
        
        if len(keys) > 1:
            pyautogui.hotkey(*keys)
            # print(f"Successfully pressed the combination: {', '.join(keys)}")
        else:
            pyautogui.press(keys[0])
            # print(f"Successfully pressed the '{keys[0]}' key.")
    except Exception as e:
        print(f"An error occurred: {e}")
        print(keys, key_input)
        print("Pressed space instead.")
        pyautogui.press('space')


def multi_key_press(str):
    keys = str.rsplit("\n")
    for key in keys:
        key = key.strip()
        simulate_key_input(key)
        # time.sleep(0.01)
        print(f"Successfully pressed the '{key}' key.")
    # print(f"Successfully pressed the '{str}' key.")

def write_text(str):
    # asterisk words are commands
    words = str.split("\n")
    for i in words:
        if "*" in i: 
            simulate_key_input(i.strip("*"))
        elif i == "comma": simulate_key_input(',')
        elif i == "period": simulate_key_input('.')
        elif i == "enter": simulate_key_input('enter')
        elif i == "space": simulate_key_input('space')
        elif i == "tab": simulate_key_input('tab')
        else:
            for j in i:
                simulate_key_input(j)
        # pyautogui.press('space')

# # Example usage:
# simulate_key_input('a')         # This will simulate pressing the 'a' key.
# simulate_key_input('ctrl home') # This will simulate pressing Ctrl + Home.
# # simulate_key_input('shift home') # This will simulate pressing Ctrl + Home.

# multi_key_press("""ctrl a
#                 ctrl c""")


# multi_key_press("alt tab")
# write_text(""""Hello \n
#            space* \n 
#            Wow!""")