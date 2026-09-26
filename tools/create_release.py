import json

with open('RELEASE_NOTES_CN.md', 'r', encoding='utf-8') as f:
    notes = f.read()

data = {
    'tag_name': 'v1.0.7',
    'name': 'v1.0.7',
    'body': notes,
    'draft': False,
    'prerelease': False
}

with open(r'C:\Users\chenk\AppData\Local\Temp\release_body.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent='\t')

print('Release body saved. Length:', len(notes))
