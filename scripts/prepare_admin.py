"""Build-time input preparation only; never used by a business Skill."""
from pathlib import Path
import hashlib,shutil,subprocess,sys
root=Path.cwd();up=Path(sys.argv[1]).resolve()
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=up,text=True).strip()=='7fee0246b05476fb6bc38e44bcfb7cc87b978853'
expected=['f5cf1790c8f0538eee1038df6c16d3591c649791537cf4587289fe2bd5ff02ed','69802fe84828b15b782431b10a55dcde1cb477e04414add1ab4eaaa00268524d','fcc5a6500c3ad2f88116435f58db976baa0b71ab9a941291ef25164777fa6a0f','7439c20d9e1541c26cf26ff68a76e7e36344dfa816ccae466816bc6570bcb310','094ef85e3320bf7ec85ae803532958dc0b896e855f16390db006715d6f9f63ee']
parts=[]
for i,digest in enumerate(expected):
 p=root/f'.transport/admin-script/{i:02d}.txt';data=p.read_bytes()
 assert hashlib.sha256(data).hexdigest()==digest,(str(p),len(data),hashlib.sha256(data).hexdigest(),digest)
 parts.append(data)
script=b''.join(parts)
assert hashlib.sha256(script).hexdigest()=='1900db2f990cfe50f79ba67d07e1116620c0cdcdf75a2cdb577148050c2375b4'
compile(script,'replay_admin.py','exec');(root/'scripts/replay_admin.py').write_bytes(script)
base=root/'cases/admin/baseline';base.mkdir(parents=True,exist_ok=True)
for name in ('main.py','README.md','templates'):
 p=up/'examples/auth_flask_login'/name;q=base/name
 if p.is_dir():shutil.copytree(p,q,dirs_exist_ok=True)
 else:shutil.copy2(p,q)
s=(base/'main.py').read_text();old='app.config["SECRET_KEY"] = "secret"'
assert s.count(old)==1;s=s.replace(old,'app.config["SECRET_KEY"] = os.environ.get("ADMIN_DEMO_SECRET")')
start=s.index('def build_sample_db():');end=s.index('\nif __name__ == "__main__":',start)
s=s[:start]+'def build_sample_db():\n    """Safety-prepared baseline: initialize empty SQLite tables only."""\n    db.create_all()\n\n'+s[end:]
(base/'main.py').write_text(s)
license=up/'LICENSE';license=license if license.exists() else up/'LICENSE.rst';shutil.copy2(license,base/'LICENSE')
(base/'SOURCE.md').write_text('''# Source provenance

`pallets-eco/flask-admin@7fee0246b05476fb6bc38e44bcfb7cc87b978853`,
`examples/auth_flask_login`. BSD-3-Clause source LICENSE is retained.

Before the CTX baseline only: replace the public example secret with an instance
environment value; replace destructive demo seeding with empty-table initialization.
No existing account data exists in this isolated input. The enabled/disabled feature
and additive migration are not present in the baseline. No upstream repository is modified.
''')
candidate=root/'cases/admin/candidate'
for p in base.rglob('*'):
 q=candidate/p.relative_to(base)
 if p.is_file() and not q.exists():q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
(candidate/'templates/auth.html').write_text('''{% extends 'admin/master.html' %}
{% block body %}<h1>{{ title }}</h1><form method="post">{{ form.hidden_tag() }}{% for f in form if f.type != 'CSRFTokenField' %}<p>{{ f.label }} {{ f }}{% for e in f.errors %}<span>{{ e }}</span>{% endfor %}</p>{% endfor %}<button type="submit">Submit</button></form><a href="{{ url_for(alternate) }}">Switch login / registration</a>{% endblock %}
''')
(candidate/'templates/my_master.html').write_text('''{% extends 'admin/base.html' %}
{% block access_control %}{% if current_user.is_authenticated %}<span>{{ current_user.username }}</span><form method="post" action="{{ url_for('admin.logout_view') }}"><input name="csrf_token" type="hidden" value="{{ csrf_token() }}"><button type="submit">Log out</button></form>{% endif %}{% endblock %}
''')
(candidate/'ACCOUNT-STATUS.md').write_text('''# Account availability

This local teaching example retains the upstream enabled-authenticated-manager model.
Set ADMIN_DEMO_SECRET outside source and use an isolated SQLite database.
The account view edits and filters Enabled. Disabling rotates the alternative identity;
re-enabling does not restore old cookies. Migration is additive and idempotent.
Run `python -m unittest test_enabled -v`: thirteen real request/SQLite tests.
RLS validates only the current local Sandbox release contract, not production deployment.
''')
shutil.rmtree(root/'.transport/admin-script')
if (root/'.transport/admin-authorpack').exists():shutil.rmtree(root/'.transport/admin-authorpack')
print('Prepared exact authored driver and pinned existing-project baseline; no lifecycle PASS inferred.')
