from sheared import error
from sheared.protocol.http import splitHeaderList

import re

def parse_accepts_header(value):
    """parse_accepts_header(header_value) -> widgets

    Parse a HTTP Accept header into a list of acceptable widgets, in
    decreasing order of preference (e.g. [("text/html", 1.0),
    ("text/plain", 0.2)])."""

    widgets = []
    for header in splitHeaderList(value):
        all = header.split(';')
        if len(all) == 1:
            gizmo, = all
            qval = 1.0
        elif len(all) == 2:
            gizmo, qval = all
            qval = qval.strip()
            if not qval.startswith('q='):
                raise ValueError, 'bad parameter in Accept-header: %s' % qval
            qval = float(qval[2:])
        else:
            raise ValueError, 'bad Accept-header: %s' % value

        gizmo = gizmo.strip()
        if gizmo == '*/*':
            qval = 0.0001
        elif gizmo.endswith('/*'):
            qval = 0.001            
        widget = gizmo, qval
        widgets.append(widget)

    widgets.sort(lambda a, b: cmp(a[1], b[1]))
    return widgets
    
def chooseContentType(request, content_types):
    """chooseContentType(request, content_types) -> content_type
    
    Find the preferred content type for a given request, among a list of
    possible content types. Or, if none of the possible content types
    are acceptable raise sheared.error.web.NotAcceptable."""

    if request.headers.get('User-Agent', '').find('MSIE') > 0:
        accepts = 'text/html, */*'
    else:
        accepts = request.headers.get('Accept', '*/*')

    def is_acceptable(widget, gizmo):
        return (widget == gizmo) or \
               (gizmo.endswith('/*') and widget.startswith(gizmo[:-1])) or \
               (gizmo == '*/*') or \
               (gizmo == '*')

    chosen = None
    acceptable = parse_accepts_header(accepts)
    for content_type in content_types:
        for gizmo, qval in acceptable:
            if is_acceptable(content_type, gizmo):
                if not chosen or qval > chosen[1]:
                    chosen = content_type, qval

    if chosen is None:
        raise error.web.NotAcceptable, \
              'cannot serve any of %s' % accepts

    return chosen[0]
