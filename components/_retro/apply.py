import sys,re,os
R=os.path.expanduser('~/software/td-plugins/components/')
h=open(R+'_retro.py').read()
for n in sys.argv[1:]:
    f=R+n+'/build.py'; s=open(f).read()
    s=re.sub(r'# RETRO BEGIN.*?# RETRO END\n','',s,flags=re.S)
    lines=s.split('\n'); i=next(j for j,l in enumerate(lines) if l.startswith('NAME') or l.startswith('def rd'))
    lines.insert(i,h); open(f,'w').write('\n'.join(lines))
