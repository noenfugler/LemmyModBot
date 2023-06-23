# from pylemmy import Lemmy
from pylemmy_foo import Lemmy
from detoxify import Detoxify
import credentials

def process_post(post):
    flags = []
    name = post.post_view.post.name
    body = post.post_view.post.body
    print(name, body)
    if name is not None:
        results = Detoxify('unbiased').predict(name)
        if results['toxicity'] > 0.5:
            flags.append('toxicity')
        if results['severe_toxicity'] > 0.5:
            flags.append('severe_toxicity')
        if results['obscene'] > 0.5:
            flags.append('obscene')
        if results['identity_attack'] > 0.5:
            flags.append('identity_attack')
        if results['insult'] > 0.5:
            flags.append('insult')
        if results['threat'] > 0.5:
            flags.append('threat')
        if results['sexual_explicit'] > 0.5:
            flags.append('sexual_explicit')
    if body is not None:
        results = Detoxify('unbiased').predict(body)
        if results['toxicity'] > 0.5:
            flags.append('toxicity')
        if results['severe_toxicity'] > 0.5:
            flags.append('severe_toxicity')
        if results['obscene'] > 0.5:
            flags.append('obscene')
        if results['identity_attack'] > 0.5:
            flags.append('identity_attack')
        if results['insult'] > 0.5:
            flags.append('insult')
        if results['threat'] > 0.5:
            flags.append('threat')
        if results['sexual_explicit'] > 0.5:
            flags.append('sexual_explicit')
    if len(flags) > 0:
        # post.create_comment(', '.join(flags))
        post.create_post_report(reason=', '.join(flags))

    pass

lemmy = Lemmy(
    lemmy_url=credentials.instance,
    username=credentials.username,
    password=credentials.password,
    user_agent="custom user agent (by "+credentials.alt_username+")",
)

# community = lemmy.get_community("asklemmy@lemmy.world")
community = lemmy.get_community("asklemmy@lemmy.world")
for post in community.stream.get_posts():
    process_post(post)

