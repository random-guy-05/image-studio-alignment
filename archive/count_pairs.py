import json
data = json.load(open('/Users/admin/opencode-imagestudio/targets.json'))
print(len(data['pairs']), 'pairs')
