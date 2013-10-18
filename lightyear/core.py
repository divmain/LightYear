import re

from parsimonious.grammar import Grammar

from .lang import rules, funcmap, defer_children_eval
from .errors import IndentationError
from .globals import BLK_OPEN, BLK_CLOSE, INDENT_SIZE, COMMENT_DELIM


class LyLang(object):
    grammar = None

    def __init__(self):
        if not self.grammar:
            self.__class__.grammar = Grammar(rules)['ltree']
        self.env = {}

    def eval(self, ly_code):
        '''
        Takes as input a string containing LightYear code, and recursively
        evaluates the root node.
        '''
        node = self.grammar.parse(ly_code)
        return self._evalnode(node)

    def _evalnode(self, node):
        '''
        Evaluates a Parsimonious node.
        '''
        fn = funcmap.get(node.expr_name, lambda env, node, children: children)
        if node.expr_name in defer_children_eval:
            return fn(self.env, node)
        return fn(self.env, node, [self._evalnode(child) for child in node])


def tokenize_whitespace(self, lines):
    """
    For each line, indentify current level of indendation and compare
    against indentation of previous line.  Insert BLK_OPEN or BLK_CLOSE
    as appropriate.
    """

    firstline = True
    prevdent = 0

    for line in lines:
        line = line.expandtabs(INDENT_SIZE)

        # Don't allow empty lines to effect tracking of indentation.
        stripped = line.strip()
        if stripped == '' or stripped[:2] == '//':
            yield line
            continue

        # Check for indentation on the first line.
        if firstline:
            if line[0] == " ":
                raise IndentationError
            firstline = False

        leading_spaces = re.match('[ ]*', line).group()
        curdent = len(leading_spaces) // INDENT_SIZE

        if curdent == prevdent:
            yield line
        elif curdent == prevdent + 1:
            yield BLK_OPEN + line
        elif curdent < prevdent:
            yield BLK_CLOSE * (prevdent - curdent) + line
        else:
            raise self.IndentationError(line)

        prevdent = curdent

    # Handle indented last line.
    yield BLK_CLOSE * prevdent


def tokenize_comments(self, lines):
    '''
    Identify and tokenize comments.
    '''
    for line in lines:
        for possible in (x.start(0) for x in re.finditer('//', line)):
            if not _isquoted(line, possible):
                line = line[:possible] + COMMENT_DELIM + line[possible:] + COMMENT_DELIM
                break
        yield line


def _isquoted(self, line, pos):
    '''
    Return boolean value indicating whether the character at position
    pos resides within a quote.
    '''
    DQUO = False
    SQUO = False

    for i in range(0, pos):
        if not DQUO and not SQUO:
            if line[i] == '"':
                DQUO = True
            elif line[i] == "'":
                SQUO = True
        elif DQUO:
            if line[i] == '"':
                DQUO = False
        elif SQUO:
            if line[i] == "'":
                SQUO = False

    return (DQUO or SQUO)
