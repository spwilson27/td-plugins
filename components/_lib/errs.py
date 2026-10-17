def errs(c):
    out=[]
    for o in [c]+c.findChildren():
        for k,s in (('err',o.errors()),('warn',o.warnings()),('script',o.scriptErrors())):
            if s: out.append((k,o.path,s[:200]))
        if False:
            i=o.op(o.name+'_info') or None
    return out
