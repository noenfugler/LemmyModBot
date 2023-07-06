from pylemmy import Lemmy
from detoxify import Detoxify
import credentials
from datetime import datetime
from time import sleep

def process_comment(comment):
    flags = []
    content = comment.comment_view.comment.content
    name = comment.post.post_view.post.name
    print(datetime.now().isoformat())
    # print(content)
    if content is not None:
        results = Detoxify('unbiased').predict(content)
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
        print('***')
        print('REPORT FOR COMMENT:')
        print(flags)
        print('***\n')
        myfile = open("reports.txt", "a")
        try:
            post.create_report(reason='Detoxify bot. '+', '.join(flags))
            myfile.write(post.post_view.post.id + ", " + name + ", "+content[:50]+", " + '|'.join(flags)+", REPORTED COMMENT")
        except:
            print("ERROR: UNABLE TO CREATE REPORT")
            myfile.write(post.post_view.post.id + ", " + name + ", " + content[:50] + ", " + '|'.join(flags) + ", FAILED TO REPORT COMMENT")
        myfile.close
    # print('****************************************************************')

lemmy = Lemmy(
    lemmy_url=credentials.instance,
    username=credentials.username,
    password=credentials.password,
    user_agent="custom user agent (by "+credentials.alt_username+")",
)

while True:
    try:
        community = lemmy.get_community(credentials.community)
        for comment in community.stream.get_comments():
            process_comment(comment)
    except:
        print('Error in connection or stream.  Waiting 60s and trying again')
        sleep(60)
