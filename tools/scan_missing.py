"""List assets referenced by mirror/ pages and CSS that weren't downloaded.
Usage: python3 tools/scan_missing.py mirror > tools/missing.txt"""
import re, os, glob, urllib.parse, sys
DOM = "everestsidingandwindows.com"
os.chdir(sys.argv[1])
miss = set()
files = glob.glob('**/*.html', recursive=True) + glob.glob('**/*.css', recursive=True) + glob.glob('**/*.css?*', recursive=True)
for f in files:
    s = open(f, errors='ignore').read(); base = os.path.dirname(f)
    refs = re.findall(r'(?:href|src|data-src|data-lazy-src|data-bg|poster|content)=["\']([^"\'#]+)["\']', s)
    refs += re.findall(r'url\(["\']?([^"\')]+)["\']?\)', s)
    refs += re.findall(r'(?:srcset|data-srcset|data-lazy-srcset)=["\']([^"\']+)["\']', s)
    refs += re.findall(r'((?:https?:)?\\?/\\?/(?:www\.)?' + re.escape(DOM) + r'[^"\'\s)]+?\.(?:css|js|webp|png|jpe?g|gif|svg|woff2?|ttf|eot|otf|mp4|webm|pdf|ico))', s)
    for r in refs:
        for part in r.split(','):
            u = part.strip().split(' ')[0].replace('\\/', '/')
            if not u or u.startswith(('data:', 'mailto:', 'tel:', 'javascript:', '#')): continue
            if u.startswith('//'): u = 'https:' + u
            if u.startswith('http'):
                if DOM not in u: continue
                p = urllib.parse.urlparse(u).path.lstrip('/')
            elif u.startswith('/'): p = u.lstrip('/')
            elif f.endswith('.html') and not re.search(r'\.(css|js|webp|png|jpe?g|gif|svg|woff2?|ttf|eot|otf|mp4|webm|pdf|ico)$', u.split('?')[0], re.I):
                continue
            else: p = os.path.normpath(os.path.join(base, u))
            p = urllib.parse.unquote(p.split('?')[0].split('#')[0])
            if p.startswith('..'): continue
            if re.search(r'\.(css|js|webp|png|jpe?g|gif|svg|woff2?|ttf|eot|otf|mp4|webm|pdf|ico)$', p, re.I) \
               and not os.path.exists(p) and not glob.glob(glob.escape(p) + '?*'):
                miss.add(p)
print('\n'.join(sorted(miss)))
