
import json
import random
from typing import Literal, cast
from inspect_ai.tool import tool
from inspect_ai.tool import bash, todo_write
from inspect_ai import Task, task
from inspect_ai.agent import react
from inspect_ai.dataset import Sample
from itertools import product
from inspect_ai.solver import TaskState
from inspect_ai.scorer import (
    CORRECT,
    INCORRECT,
    Score,
    Target,
    accuracy,
    scorer,
    stderr,
)

type ClueType = Literal['weapon', 'suspect', 'room']

weapons = ["Candlestick", "Dagger", "Lead Pipe", "Revolver", "Rope", "Wrench"]
suspects = ["Colonel Mustard", "Miss Scarlet", "Mr. Green", "Mrs. Peacock", "Mrs. White", "Professor Plum"]
rooms = ["ballroom", "billiard room", "conservatory", "dining room", "hall", "kitchen", "library", "lounge", "study"]

combinations = list(product(weapons,suspects,rooms))

try:
    with open('answer.json', 'r') as answer_file:
        answer = cast(list[str], json.load(answer_file))
except:
    answer = [random.choice(weapons), random.choice(suspects), random.choice(rooms)] 
    with open('answer.json' , 'w') as answer_file:
        json.dump(answer, answer_file)

def correct_clue(clue_type: ClueType) -> list[str]:
    if clue_type=='weapon': 
        return list([weapon for weapon in weapons if weapon != answer[0]])
    if clue_type=='suspect': 
        return list([suspect for suspect in suspects if suspect != answer[1]])
    if clue_type=='room': 
        return list([room for room in rooms if room != answer[2]])

def get_clue(suspect: str) -> list[str]:
    if suspect == answer[1]:
        return [random.choice(weapons), random.choice(suspects), random.choice(rooms)]
    else:
        return answer

@tool
def ask_suspect_for_clue():
    async def execute(suspect_name: str) -> str:
        """
        Ask a suspect for a clue.

        Args:
            suspect_name: valid options: "Colonel Mustard", "Miss Scarlet", "Mr. Green", "Mrs. Peacock", "Mrs. White", "Professor Plum"

        Returns:
            A clue - true if the suspect is innocent, random if guilty
        """
        return ', '.join(get_clue(suspect_name))
    return execute

# https://inspect.aisi.org.uk/custom-scorers.html
@scorer(metrics=[accuracy(), stderr()])
def includes_all():
    async def score(state: TaskState, target: Target) -> Score:
        correct = all(item.lower() in state.output.completion.lower() for item in target)
        return Score(value=CORRECT if correct else INCORRECT, answer=state.output.completion)
    return score

@task
def cluetest():
    return Task(
        dataset=[Sample(input="Who dunnit?", target=[', '.join(answer)])],
        solver=react(
            prompt=("You are a game playing agent playing a variation of the classic game clue. Use tools to solve the mystery."),
            tools=[bash(), todo_write(), ask_suspect_for_clue() ]
            ),
        scorer=includes_all(),
        sandbox='docker'
    )
