from sheared import error
from sheared.protocol.http import splitHeaderList

def parse_accepts_header(value):
    """parse_accepts_header(header_value) -> widgets

    Parse a HTTP Accept(-.*)? header into a list of acceptable widgets,
    in decreasing order of preference (e.g. [("text/html", 1.0),
    ("text/plain", 0.2)])."""

    widgets = []
    for header in splitHeaderList(value):
        all = header.split(';')
        if len(all) == 1:
            gizmos, = all
            qval = 1.0
        elif len(all) == 2:
            gizmos, qval = all
            qval = qval.strip()
            if not qval.startswith('q='):
                raise ValueError, 'bad parameter in Accept-header: %s' % qval
            qval = float(qval[2:])
        else:
            raise ValueError, 'bad Accept-header: %s' % value

        for gizmo in gizmos.split(','):
            widget = gizmo.strip(), qval
            widgets.append(widget)

    widgets.sort(lambda a, b: cmp(a[1], b[1]))
    return widgets
    
def chooseContentType(request, content_types):
    """chooseContentType(request, content_types) -> content_type
    
    Find the preferred content type for a given request, among a list of
    possible content types. Or, if none of the possible content types
    are acceptable raise sheared.error.web.NotAcceptable."""

    def is_acceptable(widget, gizmo):
        return (widget == gizmo) or \
               (gizmo == '*/*') or \
               (gizmo.endswith('/*') and widget.startswith(gizmo[:-1]))

    if request.headers.has_key('Accept'):
        chosen = None
        acceptable = parse_accepts_header(request.headers['Accept'])
        for content_type in content_types:
            for gizmo, qval in acceptable:
                if is_acceptable(content_type, gizmo):
                    if not chosen or qval > chosen[1]:
                        chosen = content_type, qval

        if chosen is None:
            raise error.web.NotAcceptable, \
                  'cannot serve any of %s' % request.headers['Accept']

    else:
        chosen = content_types[0], 1.0

    return chosen[0]
