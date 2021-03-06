"""
Utility classes for rewriting elements of HTML-like strings
"""

import re


FIND_A_TAG = re.compile(r'<a(\b[^>]*)>')
FIND_EMBED_TAG = re.compile(r'<embed(\b[^>]*)/>')
FIND_ATTRS = re.compile(r'([\w-]+)\="([^"]*)"')


def extract_attrs(attr_string):
    """
    helper method to extract tag attributes, as a dict of un-escaped strings
    """
    attributes = {}
    for name, val in FIND_ATTRS.findall(attr_string):
        val = val.replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&amp;', '&')
        attributes[name] = val
    return attributes


class EmbedRewriter:
    """
    Rewrites <embed embedtype="foo" /> tags within rich text into the HTML fragment given by the
    embed rule for 'foo'. Each embed rule is a function that takes a dict of attributes and
    returns the HTML fragment.
    """
    def __init__(self, embed_rules):
        self.embed_rules = embed_rules

    def replace_tag(self, match):
        attrs = extract_attrs(match.group(1))
        try:
            rule = self.embed_rules[attrs['embedtype']]
        except KeyError:
            # silently drop any tags with an unrecognised or missing embedtype attribute
            return ''
        return rule(attrs)

    def __call__(self, html):
        return FIND_EMBED_TAG.sub(self.replace_tag, html)


class LinkRewriter:
    """
    Rewrites <a linktype="foo"> tags within rich text into the HTML fragment given by the
    rule for 'foo'. Each link rule is a function that takes a dict of attributes and
    returns the HTML fragment for the opening tag (only).
    """
    def __init__(self, link_rules):
        self.link_rules = link_rules

    def replace_tag(self, match):
        attrs = extract_attrs(match.group(1))
        try:
            link_type = attrs['linktype']
        except KeyError:
            # return ordinary links without a linktype unchanged
            return match.group(0)

        try:
            rule = self.link_rules[link_type]
        except KeyError:
            # unrecognised link type
            return '<a>'

        return rule(attrs)

    def __call__(self, html):
        return FIND_A_TAG.sub(self.replace_tag, html)


class MultiRuleRewriter:
    """Rewrites HTML by applying a sequence of rewriter functions"""
    def __init__(self, rewriters):
        self.rewriters = rewriters

    def __call__(self, html):
        for rewrite in self.rewriters:
            html = rewrite(html)
        return html
