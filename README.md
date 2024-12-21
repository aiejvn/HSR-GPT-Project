# HSR-GPT-Project
 A short project testing if ChatGPT can play Honkai: Star Rail (HSR).
 Running code as admin is a MUST.

Behavior Loop:

1. action_controller queries screen_reader for whose turn it is currently ("NOBODY" if it is the enemy's turn) & team health.

2. screen_reader opens the game (assuming you are running it) and reads necessary info from game. Returns this to action_controller.

3. action_controller feeds this information and internal tracker of other necessary information (i.e. skill points) into main - gets back what move to take.

4. action_controller translate this move into key presses. Inputs this into game and waits some time for the animations to finish.

## TODO's:
- [x] Feed active ultimates + special stage abilities into the bot
- [X] Distinguish the characters by the distribution of colors instead of measuring SSIM (Structural Similarity)
    * The characters are actually very similar, and putting the image in monochrome only worsens this. 

## Bosses GPT4o Has Beaten (Spoiler Warning):
- Phantylia the Undying (Difficulty V)
- "Harmonious Choir" The Great Septimus & "Embryo of Philosophy" Sunday (Difficulty V)
- Shadow of "Feixiao" (Difficulty V)