def get_return_dict(username: str, message: str = ""):
    query = {"username": username}
    # doc = db.subscribers_db.find(query)
    subscriptions = []
    if not 0:
        subscriptions = []
    else:
        subscriptions = ['DeepSpeech']

    return {
        "Message": message,
        "Subscriptions": subscriptions,
        "Publishers": ["GitHub", "BitBucket", "GitLab"]
    }

def EN(msg):
    repo = msg['repo']
    if ((repo[0]>='a') & (repo[0]<='h')):
        return ['5101']
    if ((repo[0]>='i') & (repo[0]<='q')):
        return ['5102']
    if ((repo[0]>='r') & (repo[0]<='z')):
        return ['5103']

msg = {}
msg['repo'] = 'pdp'

print(EN(msg))