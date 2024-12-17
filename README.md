# HSR-GPT-Project
 A short project testing if ChatGPT can play Honkai: Star Rail (HSR).

Behavior Loop:

1. action_controller queries screen_reader for whose turn it is currently ("NOBODY" if it is the enemy's turn) & team health.

2. screen_reader opens the game (assuming you are running it), reads current person in turn order & how healthy everyone is. Returns this to action_controller.

3. action_controller feeds this information and internal tracker of other necessary information (i.e. skill points) into main - gets back what move to take.

4. action_controller translate this move into key presses. Inputs this into game and waits some time for the animations to finish.

## TODO's:
- [ ] Feed active ultimates + special stage abilities into the bot
- [ ] Distinguish the characters by unique colors only present in their design instead of measuring SSIM (Structural Similarity)
    * The characters are actually very similar, and putting the image in monochrome only worsens this. 
- [ ] Experiment with different LLMs to see who is the best at playing HSR (out of the box
