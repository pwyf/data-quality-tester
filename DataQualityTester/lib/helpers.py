import re


def pprint(explanation):
    explanation = explanation.strip()
    if len(explanation) > 0:
        explanation = explanation[0].upper() + explanation[1:]
    explanation = explanation.replace('\n', '<br>') + '.'
    return re.sub(r'`([^`]*)`', r'<code>\1</code>', explanation)
