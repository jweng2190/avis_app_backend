from avis_app import redis_cli

def get_all_events():
    events = redis_cli.get('all_events')
    return events

def put_all_events(events):
    redis_cli.set('all_events', events, ex=7*24*3600)
