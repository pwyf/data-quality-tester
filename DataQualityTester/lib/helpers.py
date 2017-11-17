import re


def pprint(explanation):
    explanation = explanation.replace('\n', '<br>')
    return re.sub(r'`([^`]*)`', r'<code>\1</code>', explanation)
