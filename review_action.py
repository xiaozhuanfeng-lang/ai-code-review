#!/usr/bin/env python3
"""AI Code Review - runs inside GitHub Actions"""

import os, json, urllib.request, subprocess

key = os.environ.get('OPENROUTER_KEY', '')
if not key:
    msg = 'Missing OPENROUTER_API_KEY secret. Set it in repo Settings > Secrets > Actions.'
    print(msg)
    with open('/tmp/review_output.txt', 'w') as f:
        f.write('ð´ ' + msg)
    exit(1)

title = os.environ.get('PR_TITLE', 'PR Review')
body = os.environ.get('PR_BODY', '')
base_ref = os.environ.get('BASE_REF', 'main')

# Get diff using git (use GH_TOKEN for auth)
import os
try:
    token = os.environ.get('GH_TOKEN', '')
    repo_url = f'https://oauth2:{token}@github.com/{os.environ.get("GITHUB_REPOSITORY", "")}.git'
    result = subprocess.run(
        ['bash', '-c', f'git remote set-url origin {repo_url} 2>/dev/null; git fetch origin {base_ref} --depth=1 2>&1; git diff origin/{base_ref}...HEAD 2>/dev/null || echo "(no diff)"'],
        capture_output=True, text=True, timeout=30
    )
    diff = result.stdout.strip()
    if not diff or diff == '(no diff)':
        diff = '(no diff available)'
    else:
        # Filter out git fetch stderr noise
        lines = [l for l in diff.split('\n') if not l.startswith('From ') and not l.startswith(' *')]
        diff = '\n'.join(lines)[:6000]
except Exception as e:
    diff = f'(failed to get diff: {e})'

prompt = f"""Review this Pull Request:

Title: {title}
Description: {body or '(none)'}

Code changes:
```diff
{diff}
```

Check: 1) bugs/performance 2) security 3) best practices 4) maintainability.
Format: one issue per line with 'â ï¸' or 'ð´'. If good, just say 'â LGTM'. Keep concise."""

payload = json.dumps({
    "model": "nvidia/nemotron-3-super-120b-a12b:free",
    "messages": [{"role": "user", "content": prompt}],
    "max_tokens": 1000,
    "temperature": 0.2
}).encode()

try:
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "X-Title": "AI-Code-Review"
        }
    )
    resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
    review = resp['choices'][0]['message']['content']
except Exception as e:
    review = f"ð´ AI review failed: {str(e)[:100]}"

with open('/tmp/review_output.txt', 'w') as f:
    f.write(review)

print("Review result (first 200 chars):")
print(review[:200])
