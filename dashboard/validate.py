import os

for fname in ['index.html', 'geo.html', 'products.html']:
    with open(fname, 'r', encoding='utf-8') as f:
        content = f.read()
    checks = {
        'DOCTYPE': '<!DOCTYPE html>' in content,
        'html close': '</html>' in content,
        'DATA const': 'const DATA = {"products"' in content,
        'Navbar Slooze': 'Slooze' in content,
        'B2B text': 'B2B' in content,
        'Footer': 'products indexed' in content,
        'Chart.js v4': 'chart.js@4' in content,
        'Tailwind': 'cdn.tailwindcss.com' in content,
        'FontAwesome': 'fontawesome.com' in content,
        'Body class': 'class="pt-20' in content,
    }
    print(f'\n=== {fname} ({len(content):,} bytes) ===')
    for k, v in checks.items():
        status = 'PASS' if v else 'FAIL'
        print(f'  [{status}] {k}')
    # Count products in JSON
    import re
    match = re.search(r'"products":\s*\[', content)
    if match:
        print(f'  [PASS] Products JSON array found')
    else:
        print(f'  [FAIL] Products JSON array missing')

print('\nAll checks complete!')
