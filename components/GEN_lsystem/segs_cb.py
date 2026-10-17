def onCook(scriptOp):
    # reads parent() parameters, so it re-cooks only when one of them changes (and once on load)
    op('lsys_expand').module.build(parent(), scriptOp)
