from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
import os
from typing import List, Tuple

class Controller:
    
    def __init__(self, debug=False):
        load_dotenv(find_dotenv())
        api_key = os.getenv("OPENAI_API_KEY")
        
        self.debug = debug
        self.client = OpenAI(api_key=api_key)
        self.messages = [
            {
                "role": "system",
                "content": """In our team, we have characters AVENTURINE, BRONYA, SPARKLE, and BLADE, and some skill points. We will only be playing one of these characters at a given moment. Each character has their own set of moves, and on a character's turn they can choose one legal move to take. Each move is in format "string":int, where "string" describes what it does while int describes how it increases/decreases our number of skill points. Skill points will always be in the range of [0,7], inclusive. A move is illegal if a character does not know that move OR it decreases our skill points to below 0.   

These are the moves each character knows:

AVENTURINE: { "WEAK ATTACK ENEMY":0, "GIVE ALLIES SHIELD":0 }

BRONYA: {  "WEAK ATTACK ENEMY":-1, "BUFF ALLY":+1 }

SPARKLE: { "WEAK ATTACK ENEMY":-1, "BUFF ALLY":+1 }

BLADE: { "STRONG ATTACK ENEMY":0, "BUFF SELF":+1 } 

You have 2 laws:
1. All allies must always have a shield.
2. Keep BLADE as effective as possible except where it conflicts with the first law.\n""",
        }
    ] 
        # This is just a reward function with extra steps.
        # We tell it the units are skill points, this is actually just the reward we want to give it.
        
        # The laws are mostly cherry on top - it may be possible to operate entirely w/o them.
        
        self.moves = { # moves w/ (REAL) costs
            "STRONG ATTACK ENEMY":0,
            "WEAK ATTACK ENEMY":1,
            "BUFF ALLY":-1,
            "BUFF SELF":-1,
            "GIVE ALLIES SHIELD":-1,
            "AVENTURINE ULT":0,
            "BRONYA ULT":0,
            "SPARKLE ULT":0,
            "BLADE ULT":0,
        }
        
        ult_names = ["AVENTURINE ULT", "BRONYA ULT", "SPARKLE ULT", "BLADE ULT"]
        
        self.knows = {
            "AVENTURINE":["WEAK ATTACK ENEMY", "GIVE ALLIES SHIELD"] + ult_names,
            "BRONYA":["WEAK ATTACK ENEMY", "BUFF ALLY"] + ult_names,
            "SPARKLE":["WEAK ATTACK ENEMY", "BUFF ALLY"] + ult_names,
            "BLADE":["STRONG ATTACK ENEMY", "BUFF SELF"] + ult_names,
        }
    
    def find_move_in_msg(self, msg, char):
        # Final move typically comes last so we want to traverse backwards, looking for moves
        lines = msg.split('\n')
        n = len(lines) - 1
        for i in range(n, -1, -1):
            cur = lines[i]
            for move in self.knows[char]:
                if move in cur:
                    return move
        
        # If no move found, return whole message for debug purposes.
        return msg

    def get_move(self, char:str, is_health_good:bool, sp:int, can_skill:bool, ult_status:List[Tuple[str, bool]])->str:
        message = f"You are currently playing as {char}. You have {str(7 - sp)} skill points. "
        if is_health_good: 
            message += "Everyone has a shield. "
        else:
            message += "We do not have a shield. "
        if not can_skill:
            message += f"We may not use {self.knows[char][1]}. "
        
        for char, ult in ult_status:
            if ult:
                message += f"{char} ULT is ready. "
                match char:
                    case "AVENTURINE": 
                        message += "AVENTURINE ULT makes BLADE significantly more effective. "
                    case "BRONYA":
                        message += "BRONYA ULT makes BLADE significantly more effective. "
                    case "SPARKLE":
                        message += "SPARKLE ULT makes BLADE significantly more effective AND spends 4 skill points. "
                    case "BLADE":
                        message += "BLADE ULT makes BLADE more effective than using BUFF SELF or STRONG ATTACK ENEMY. "
            
        message += "Give only one move. "
        
        self.messages.append(
            {
                "role": "user",
                "content":  message,
            }
        )
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=self.messages,
            temperature=1.0,
        )
        if response.choices:
            res = response.choices[-1].message.content
        else:
            res = "Request failed (for some unknown reason)."
            print(res)
            
        # if the bot makes a move that a character doesn't know, tell it that and make it try again.
            # if this succeeds, then the move must exist
        # if the bot makes a sp- move on 0sp, tell it that and make it try again.
        # There is a decently high chance the bot breaks the first rule. This prevents it from doing so.
        # Aventurine is the prime culprit for breaking this rule. 
        
        n_errors = 1
        while self.find_move_in_msg(res, char) not in self.knows[char] or self.moves[self.find_move_in_msg(res, char)] < 0 and int(sp) == 0 or (self.find_move_in_msg(res, char) == self.knows[char][1] and not can_skill):
            warning = res
            warning += " \nYou made an illegal move."
            if self.find_move_in_msg(res, char) not in self.knows[char]:
                warning += f" {char} cannot use that move."
                
            elif self.moves[self.find_move_in_msg(res, char)] < 0 and int(sp) == 0:
                warning += " You have too many skill points so you cannot use that move."
                # Normally we tell it that it has no skill points. We also inverted costs, so we should also invert this as well
            
            elif self.find_move_in_msg(res, char) == self.knows[char][1] and not can_skill: # mainly for when the bot tries to blade skill, but we cannot
                warning += " You cannot use that move right now."
            warning += " Try again."    
            
            
            self.messages.append(
                {
                    "role": "user",
                    "content": warning,
                }
            )
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=self.messages,
                temperature=1.0,
            )
            if response.choices:
                res = response.choices[-1].message.content
                
                if self.debug: print("Convo:", self.messages) 
                
            else:
                res = "Request failed (for some unknown reason)."
                print(res)
                
            if self.find_move_in_msg(res, char) in self.knows[char] and self.moves[self.find_move_in_msg(res, char)] >= 0:
                for i in range(n_errors):
                    self.messages.pop() # remove validator messages
                break
            n_errors += 1
        
        
        
        if self.debug: print("Convo:", self.messages)
            
            
        # remove last move's message if keeping them in memory pollutes the convo 
        # if not, uncomment this line
        self.messages.pop() 
        
        return res

if __name__ == "__main__":
    ct = Controller(debug=True)
    
    while True: # these should all be found by the screen reader, except sp. That is smth we can track ourselves
        char = input("Who is the current character? (Enter 'exit' to quit) ")
        if char == 'exit': break
        is_health_good = input("Is our health good? (y/n) ")
        if is_health_good == 'y': 
            is_health_good = True
        else:
            is_health_good = False
        sp = int(input("How many skill points do we have? "))
        
        can_skill = input("Can we use skill? (y/n) ")
        can_skill = True if can_skill == 'y' else False
        
        ults = []
        for char in ['AVENTURINE', 'BRONYA', 'SPARKLE', 'BLADE']:
            ult_status = input(f"Is {char} ultimate ready? (y/n) ")
            ults.append([char, ult_status == 'y'])
        
        result = ct.get_move(char=char, is_health_good=is_health_good, sp=sp, can_skill = can_skill, ult_status=ults)
        print(result)
        print(ct.find_move_in_msg(msg=result, char=char))
        