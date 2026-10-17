v=op('/validate')
d=v.op('driver') or v.create(td.executeDAT,'driver')
d.text='''def onFrameEnd(frame):
    for c in op('/validate').children:
        if c.isCOMP:
            for o in c.children:
                if o.isTOP and o.name.startswith('out'):
                    o.cook(force=True)
    return
'''
d.par.framestart=1
d.par.frameend=1
print([p.name for p in d.pars()][:30])
