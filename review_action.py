#!/usr/bin/env python3
"""AI Code Review - runs inside GitHub Actions"""

import os, json, urllib.request

key = os.environ.get('OPENROUTER_KEY', '')
if not key:
    msg = 'Missing OPENROUTER_API_KEY secret. Set it in repo Settings > Secrets > Actions.'
    print(msg)
    with open('/tmp/review_output.txt', 'w') as f:
        f.write('ð´ ' + msg)
    exit(1)

# Read PR info from environment
title = os.environ.get('PR_TITLE', 'PR Review')
body = os.environ.get('PR_BODY', '')

# Read diff file if it exists
diff_path = '/github/workspace/diff.txt'
if os.path.exists(diff_path):
    with open(diff_path) as f:
        diff = f.read()[:6000]
else:
    # Try to generate diff from git
    import subprocess
    result = subprocess.run(
        ['bash', '-c', 'git fetch origin ${{ github.event.pull_request.base.ref }} --depth=1 2>/dev/null; git diff origin/${{ github.event.pull_request.base.ref }}...HEAD || echo ""'],
        capture_output=True, text=True, timeout=30
    )
    diff = result.stdout[:6000] if result.stdout else '(no diff available)'

prompt = f"""Review this Pull Request:

Title: {title}
Description: {body or '(none)'}

Code changes:
```diff
{diff}
```

Check: 1) bugs/performance 2) security 3) best practices 4) maintainability.
Format: one issue per line with 'â ï¸' or 'ð´'. If good, 'â LGTM'. Keep concise."""

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

print("Review complete:")
print(review[:200])
