def split_header_list(s):
    l = []
    for e in s.split(','):
        e = e.strip()
        if e:
            l.append(e)
    return l

def parse_accepts_header(value):
    """parse_accepts_header(header_value) -> widgets

    Parse a HTTP Accept header into a list of acceptable widgets, in
    decreasing order of preference (e.g. [("text/html", 1.0),
    ("text/plain", 0.2)])."""

    widgets = []
    for header in split_header_list(value):
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
    
def is_explorer(environ):
    return environ.get('HTTP_USER_AGENT', '').startswith('Mozilla/4.0 (compatible; MSIE ')
def choose_widget(environ, widgets, default=None):
    """choose_widget(environ, widgets) -> widget
    
    Find the preferred widget for the clients Accept-headers for a given
    request, among a list of possible (widget, headers dict) pairs. Or, if
    none of the possible widgets are acceptable return default."""

    if is_explorer(environ):
        accepts = 'text/html, */*'
    elif environ.has_key('HTTP_ACCEPT'):
        accepts = environ['HTTP_ACCEPT']
    else:
        accepts = '*/*'

    def is_acceptable(widget, gizmo):
        return (widget == gizmo) or \
               (gizmo.endswith('/*') and widget.startswith(gizmo[:-1])) or \
               (gizmo == '*/*') or \
               (gizmo == '*')

    chosen = None
    acceptable = parse_accepts_header(accepts)
    for widget, headers in widgets:
        for gizmo, qval in acceptable:
            ct = headers.get('Content-Type', None)
            if ct and is_acceptable(ct, gizmo):
                if not chosen or qval > chosen[1]:
                    chosen = widget, qval

    if chosen is None:
        return default
    else:
        return chosen[0]
