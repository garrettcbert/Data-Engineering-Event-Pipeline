#  - event_id: string, unique identifier for the event
#  - user_id: int, unique identifier for the user
#  - event_type: string, type of the event (e.g., "click", "view", "purchase")
#  - timestamp: datetime, time when the event occurred
#  - source: string, source of the event (e.g., "web", "mobile", "email")
#  - metadata: json, additional information about the event in JSON format

import random
import numpy as np
import json

def generate_event_data(num_events, missing_prob = 0.05):
    generated_data = [] # init final list

    for i in range(num_events):
        event_data = {} # init event dict

        if random.random() > missing_prob:
            event_data['event_id'] = f'evt_{str(i).zfill(6)}' # should return evt_000001

        if random.random() > missing_prob:
            event_data['user_id'] = str(random.randint(1, 10000))

        event_list = list(interaction_events.keys())
        event_weights = list(interaction_events.values())
        event_choice = random.choices(event_list, weights = event_weights, k = 1)[0]
        if random.random() > missing_prob:
            event_data['event_type'] = event_choice
        
        if random.random() > missing_prob:
            time_null_prob = 0.03 # time null 3%
            if random.random() <= time_null_prob:
                event_data['timestamp'] = None
            else:
                event_data['timestamp'] = str(np.datetime64('now') - np.timedelta64(random.randint(1, 1000000), 's'))

        source_list = list(sources.keys())
        source_weights = list(sources.values())
        if random.random() > missing_prob:
            event_data['source'] = random.choices(source_list, weights = source_weights, k = 1)[0]

        meta_list = list(meta_data[event_choice].keys())
        meta_weights = list(meta_data[event_choice].values())
        if random.random() > missing_prob:
            event_data['metadata'] = random.choices(meta_list, weights = meta_weights, k = 1)[0]

        generated_data.append(event_data)

    return generated_data

interaction_events = {
    'page_view' : 0.39,
    'scroll': 0.24,
    'search': 0.14,
    'add_to_cart': 0.09,
    'remove_from_cart': 0.07,
    'purchase': 0.03,
    None: 0.04
}

sources = {
    'web': 0.39,
    'mobile_ios': 0.19,
    'mobile_android': 0.04,
    'tablet': 0.09,
    'desktop_app': 0.14,
    'email': 0.09,
    None: 0.06
}

meta_data = {
    'page_view': {
        'viewed product page': 0.24,
        'landed on homepage': 0.19,
        'opened pricing page': 0.14,
        'Page loaded': 0.09,
        'accidentally opened page': 0.07,
        'page refresh loop??': 0.03,
        'user stared at page for a while': 0.01,
        'PAGE_VIEW': 0.05,
        'opened page then immediately left': 0.09,
        None: 0.09
    },
    'scroll': {
        'scrolled down': 0.29,
        'fast scroll through page': 0.19,
        'slow scroll, reading carefully': 0.14,
        'barely scrolling': 0.09,
        'scrolling endlessly': 0.09,
        'scroll spam': 0.06,
        'user flicked page aggresively': 0.04,
        'autoscroll triggered': 0.02,
        'scroll??': 0.01,
        None: 0.06
    },
    'search': {
        'searched for shoes': 0.24,
        'search query: headphones': 0.19,
        'looked up return policy': 0.14,
        'random search': 0.09,
        'typo in search query': 0.09,
        'search fired twice': 0.07,
        'rage searched product': 0.05,
        'SEARCH EVENT': 0.04,
        'searched nothing': 0.02,
        None: 0.07
    },
    'add_to_cart': {
        'added item to cart': 0.29,
        'added product to shopping cart': 0.19,
        'add to cart clicked': 0.14,
        'added same item twice': 0.09,
        'cart updated': 0.09,
        'accidental add to cart': 0.07,
        'added then removed item quickly': 0.05,
        'item added??': 0.02,
        'added item but inventory unclear': 0.01,
        None: 0.05
    },
    'remove_from_cart': {
        'removed item from cart': 0.29,
        'removed product': 0.19,
        'changed mind, removed': 0.09,
        'remove clicked': 0.14,
        'cart item deleted': 0.09,
        'cart cleaned': 0.07,
        'removed item immediately after adding': 0.05,
        'remove_from_cart': 0.02,
        'item removed unexpectedly': 0.01,
        None: 0.05
    },
    'purchase': {
        'purchase completed': 0.24,
        'checkout finished': 0.19,
        'payment successful': 0.14,
        'order placed': 0.09,
        'clicked buy but didn\'t mean to': 0.08,
        'just browsing, no intent to buy': 0.06,
        'purchase??': 0.04,
        'payment whent through twice': 0.02,
        None: 0.04
    },
    None: {
        None: 100
    }
}

for i in range(3):
    with open(f'data/raw/events_2025_01_0{i}.json', 'w', encoding = 'utf-8') as f:
        json.dump(generate_event_data(10000), f, indent =2)




