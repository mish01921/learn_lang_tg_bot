from typing import Dict, List

DAILY_BLOCKS = {
    "steady": [
        {"id": "warmup",     "title": "Տաքացում",           "min": 3,  "desc": "Արագ հիշեցում"},
        {"id": "words",      "title": "Նոր բառեր (5)",      "min": 7,  "desc": "Օրվա հիմնական բառերը"},
        {"id": "story",      "title": "Պատմություն (AI)",   "min": 5,  "desc": "Բառերը կոնտեքստում"},
        {"id": "coach",      "title": "Մարզիչի կարծիք",     "min": 2,  "desc": "Արդյունքների վերլուծություն"},
    ],
    "deep": [
        {"id": "warmup",     "title": "Ակտիվացում",         "min": 5,  "desc": "Ուղեղի նախապատրաստում"},
        {"id": "words",      "title": "Նոր բառեր (10)",     "min": 12, "desc": "Ինտենսիվ ուսուցում"},
        {"id": "practice",   "title": "Interactive Task",   "min": 10, "desc": "Կիրառել նախադասության մեջ"},
        {"id": "palace",     "title": "Memory Palace",      "min": 8,  "desc": "Տեսողական հիշողություն"},
        {"id": "coach",      "title": "Coach Analysis",     "min": 3,  "desc": "Խորացված վերլուծություն"},
    ],
}


async def get_today_guided_blocks(user_id: int) -> List[Dict]:
    from src.database.models import get_user_plan
    plan_key = await get_user_plan(user_id) # "steady" or "deep"
    blocks = list(DAILY_BLOCKS.get(plan_key, DAILY_BLOCKS["steady"]))
    return blocks
