#!/usr/bin/env python3
"""Minimal s-expression reader + helpers for KiCad netlist/sch/pcb files.
Shared by the other review scripts. No external dependencies."""
import re, sys

def parse_sexpr(text):
    tok = re.compile(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+')
    stack, cur = [], []
    for m in tok.finditer(text):
        t = m.group()
        if t == '(':
            new = []; cur.append(new); stack.append(cur); cur = new
        elif t == ')':
            cur = stack.pop()
        elif t.startswith('"'):
            cur.append(t[1:-1].encode().decode('unicode_escape'))
        else:
            cur.append(t)
    return cur

def find_all(node, key):
    """Yield every sub-list whose head is `key`, at any depth."""
    if isinstance(node, list):
        if node and node[0] == key:
            yield node
        for c in node:
            yield from find_all(c, key)

def get(node, key, default=None):
    """First direct child list with head `key`, else default."""
    for c in node:
        if isinstance(c, list) and c and c[0] == key:
            return c
    return default

def val(node, key, idx=1, default=None):
    c = get(node, key)
    return c[idx] if c and len(c) > idx else default

def load(path):
    return parse_sexpr(open(path, encoding='utf-8').read())
