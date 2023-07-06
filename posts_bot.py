from pylemmy import Lemmy
from detoxify import Detoxify
import credentials
from datetime import datetime
from time import sleep
import traceback

def process_post(post):
    flags = []
    name = post.post_view.post.name
    body = post.post_view.post.body
    print(datetime.now().isoformat())
    # print('post id',post.post_view.post.id)
    # print(name)
    if name is not None:
        results = Detoxify('unbiased').predict(name)
        print(results)
        if results['toxicity'] > 0.8:
            flags.append('toxicity')
        if results['severe_toxicity'] > 0.5:
            flags.append('severe_toxicity')
        if results['obscene'] > 0.5:
            flags.append('obscene')
        if results['identity_attack'] > 0.5:
            flags.append('identity_attack')
        if results['insult'] > 0.8:
            flags.append('insult')
        if results['threat'] > 0.5:
            flags.append('threat')
        if results['sexual_explicit'] > 0.8:
            flags.append('sexual_explicit')
    # print('................................................................')
    # print(body)
    if body is not None:
        results = Detoxify('unbiased').predict(body)
        print(results)
        if results['toxicity'] > 0.8:
            flags.append('toxicity')
        if results['severe_toxicity'] > 0.5:
            flags.append('severe_toxicity')
        if results['obscene'] > 0.5:
            flags.append('obscene')
        if results['identity_attack'] > 0.5:
            flags.append('identity_attack')
        if results['insult'] > 0.8:
            flags.append('insult')
        if results['threat'] > 0.5:
            flags.append('threat')
        if results['sexual_explicit'] > 0.8:
            flags.append('sexual_explicit')
    if len(flags) > 0:
        myfile = open("reports.txt", "a")
        try:
            post.create_report(reason='Detoxify bot. '+', '.join(flags))
            myfile.write(post.post_view.post.id + ", " + name + ", , " + '|'.join(flags)+", REPORTED POST")
        except:
            print("ERROR: UNABLE TO CREATE REPORT")
            myfile.write(post.post_view.post.id + ", " + name + ", , " + '|'.join(flags) + ", FAILED TO REPORT POST")
        myfile.close()
    # print('****************************************************************')
    # pass

lemmy = Lemmy(
    lemmy_url=credentials.instance,
    username=credentials.username,
    password=credentials.password,
    user_agent="custom user agent (by "+credentials.alt_username+")",
)

while True:
    try:
        community = lemmy.get_community(credentials.community)
        for post in community.stream.get_posts():
            process_post(post)
    except Exception:
        print('Error in connection or stream.  Waiting 60s and trying again')
        traceback.print_exc()
        sleep(60)
