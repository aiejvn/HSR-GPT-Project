# HSR-GPT-Project
 A short project testing if ChatGPT can play Honkai: Star Rail (HSR).
 Running code as admin is a MUST.

## Quickstart guide:
1. Clone this repository from the repo or using this url: ```https://github.com/aiejvn/HSR-GPT-Project.git```.
2. Create a ```.env``` file with your GPT API key inside. It should be in the same folder as ```main.py```.
3. ```cd``` into this project and run ```pip install -r requirements.txt```.
4. Open a window of Honkai : Star Rail and start a combat.
5. Run ```action_controller.py``` as admin (required so that the program can make input).

## Behavior Loop:

1. ```action_controller``` queries screen_reader for whose turn it is currently ("NOBODY" if it is the enemy's turn) & team health.

2. ```screen_reader``` opens the game (assuming you are running it) and reads necessary info from game. Returns this to ```action_controller```.

3. ```action_controller``` feeds this information and internal tracker of other necessary information (i.e. skill points) into main - gets back what move to take.

4. ```action_controller``` translates this move into key presses. Inputs this into game and waits some time for the animations to finish.

## Bosses GPT4o Has Beaten (Spoiler Warning):
- Phantylia the Undying (Difficulty V)
- "Harmonious Choir" The Great Septimus & "Embryo of Philosophy" Sunday (Difficulty V)
- Shadow of "Feixiao" (Difficulty V)
