def expandMapping(src, escapeVariant=None):
    dst = {}
    for abbrv, values in src.items():
        if not isinstance(values, tuple):
            raise Exception('Found non-tuple for {}'.format(abbrv))
        for variant in values + (abbrv,):
            if escapeVariant is not None:
                variant = escapeVariant(variant)
            if dst.get(variant, abbrv) != abbrv:
                raise Exception('Name conflict at src["{}"] = "{}" != "{}"'.format(variant, abbrv, src[variant]))
            dst[variant] = abbrv
    return dst
