import re


def pprint(explanation):
    explanation = explanation.replace('\n', '<br>')
    return re.sub(r'`([^`]*)`', r'<code>\1</code>', explanation)


def percent(result):
    total = result['passed'] + result['failed']
    if total == 0:
        return None
    return 100. * result['passed'] / total
