from pylemmy import Lemmy
from detoxify import Detoxify
import credentials

def process_comment(comment):
    flags = []
    content = comment.comment_view.comment.content
    # body = post.post_view.post.body
    print('\n',content)
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
        comment.create_report(reason=', '.join(flags))

lemmy = Lemmy(
    lemmy_url=credentials.instance,
    username=credentials.username,
    password=credentials.password,
    user_agent="custom user agent (by "+credentials.alt_username+")",
)

community = lemmy.get_community(credentials.community)
for comment in community.stream.get_comments():
    process_comment(comment)

