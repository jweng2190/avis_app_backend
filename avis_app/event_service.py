from Levenshtein._levenshtein import distance
from datetime import datetime, date, timedelta

from avis_app import dao


# This is a suggestion algorithm which provides possible matches for user entered event name.
def suggest_possible_events(keyword):
    possible_suggestion_list = []
    column_names, event_info_list = dao.get_all_events()
    for event in event_info_list:
        event_description = event[4] # This gets event description
        split_words = event_description.split()
        for word in split_words:
            if distance(keyword, word) <= 1:
                possible_suggestion_list.append(event)
                break
    return column_names, possible_suggestion_list


def get_my_upcoming_events(user_id):
    col_names, events = dao.get_events_by_user(user_id)
    upcoming_events = list(filter(lambda x: x[1] > datetime.now(), events))
    return col_names, upcoming_events


def get_other_upcoming_events(user_id):
    col_names, all_events = dao.get_all_events()
    all_upcoming_events = list(filter(lambda x: x[1] > datetime.now(), all_events))
    col_names, my_events = dao.get_events_by_user(user_id)
    my_upcoming_events = list(filter(lambda x: x[1] > datetime.now(), my_events))
    
    other_events = set(all_upcoming_events).difference(set(my_upcoming_events))
    return col_names, other_events


def get_past_events():
    col_names, all_events = dao.get_all_events()
    past_events = list(filter(lambda x: x[1].date() < date.today(), all_events))
    return col_names, past_events
