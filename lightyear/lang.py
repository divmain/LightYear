from .globals import BLK_OPEN, BLK_CLOSE, COMMENT_DELIM
from .types import RuleBlock, CSSRule, MixIn
from .core import LyLang


ly_grammar = ""
funcmap = {}
defer_children_eval = []


class Grammar(object):
    def __init__(self, ruletxt, defer=False):
        global ly_grammar
        ly_grammar += ruletxt + '\n'

        self.rulenames = []
        for line in ruletxt.split('\n'):
            line = line.strip()
            if line:
                name = line.split('=')[0].strip()
                self.rulenames.append(name)
                if defer:
                    defer_children_eval.append(self.rulename)

    def __call__(self, f):
        for name in self.rulenames:
            funcmap[name] = f


###

@Grammar(r'ltree = root_element*')
def ltree(env, node, children):
    return children


@Grammar(r'root_block / mixin_decl / var_decl / rule_block / (___ nl ___)')
def root_element(env, node, children):
    return children[0]


### SELECTORS

@Grammar(r'rule_block = tag? simple_selector ("," _ simple_selector)* ___ nl ___ block')
def rule_block(env, node, children):
    tag, simple_sel, more_selectors, _, _, _, block = children

    selectors = [simple_sel]
    if more_selectors:
        selectors = selectors.extend([selector for _, selector in more_selectors])

    return RuleBlock(tag=tag,
                     selectors=selectors,
                     block=block)


@Grammar(r'block = blk_open (declaration / rule_block / parent_selector / nl)+ blk_close')
def block(env, node, children):
    return children[1]


Grammar(r'parent_selector = "&" rule_block')


@Grammar(r'simple_selector = (type_sel / universal_sel) (attribute_sel / id_sel / pseudo_class)*')
def simple_selector(env, node, children):
    return node.text

Grammar(r'''
type_sel = name
universal_sel = "*"

attribute_sel = "[" name ("=" / "~=" / "|=") name "]"
id_sel = "#" name

pseudo_class = ":" (pseudo_class_param "(" num ")") / pseudo_class_not / pseudo_class_noparam
pseudo_class_param = "nth-child" / "nth-last-child" / "nth-of-type" / "nth-last-of-type" / "lang"
pseudo_class_noparam = "last-child" / "first-of-type" / "last-of-type" / "only-child" / "only-of-type" / "root" / "empty" / "target" / "enabled" / "disabled" / "checked" / "link" / "visited" / "hover" / "active" / "focus" / "first-letter" / "first-line" / "first-child" / "before" / "after"
pseudo_class_not = "not(" ... ")"
''')


### CSS RULES

@Grammar(r'declaration = tag? property ":" _ expr+ ___ nl')
def declaration(env, node, children):
    tag, prop, _, _, values, _, _ = children
    return CSSRule(tag=tag,
                   prop=prop,
                   values=values)


@Grammar(r'property = name')
def property_(env, node, children):
    return node.text


@Grammar(r'expr = mixin_or_func_call / lvalue / math / string_val _?')
def expr(env, node, children):
    return children[0]


### MIXINS, FUNCTIONS, and VARIABLES
@Grammar(r'mixin_decl = name "(" (name _)* "):" ___ nl ___ block',
         defer=True)
def mixin_decl(env, node):
    name, _, variables, _, _, _, _, block = node

    ly_engine = LyLang(env=env)
    name = ly_engine._evalnode(name)
    variables = [varname for varname, _ in ly_engine._evalnode(variables)]

    def f(args):
        local_vars = list(zip(variables, args))
        global_vars = env.items()
        temp_env = dict(global_vars + local_vars)

        ly_engine_local = LyLang(env=temp_env)
        return ly_engine_local._evalnode(block)

    return MixIn(name=name,
                 func=f)


### Grammar rules with no associated function.  Returns empty list.

Grammar(r'''
tag = "(" name ")" _
num = ~"\-?\d+(\.\d+)?"
hex = ~"[0-9a-fA-F]+/"
hexcolor = "#" hex
name = ~"[a-zA-Z\_][a-zA-Z0-9\-\_]*"

unit = "em" / "ex" / "px" / "cm" / "mm" / "in" / "pt" / "pc" / "deg" / "rad" / "grad" / "ms" / "s" / "hz" / "khz" / "%"
color_name = "aliceblue" / "antiquewhite" / "aqua" / "aquamarine" / "azure" / "beige" / "bisque" / "black" / "blanchedalmond" / "blue" / "blueviolet" / "brown" / "burlywood" / "cadetblue" / "chartreuse" / "chocolate" / "coral" / "cornflowerblue" / "cornsilk" / "crimson" / "cyan" / "darkblue" / "darkcyan" / "darkgoldenrod" / "darkgray" / "darkgreen" / "darkkhaki" / "darkmagenta" / "darkolivegreen" / "darkorange" / "darkorchid" / "darkred" / "darksalmon" / "darkseagreen" / "darkslateblue" / "darkslategray" / "darkturquoise" / "darkviolet" / "deeppink" / "deepskyblue" / "dimgray" / "dodgerblue" / "firebrick" / "floralwhite" / "forestgreen" / "fuchsia" / "gainsboro" / "ghostwhite" / "gold" / "goldenrod" / "gray" / "green" / "greenyellow" / "honeydew" / "hotpink" / "indianred " / "indigo " / "ivory" / "khaki" / "lavender" / "lavenderblush" / "lawngreen" / "lemonchiffon" / "lightblue" / "lightcoral" / "lightcyan" / "lightgoldenrodyellow" / "lightgray" / "lightgreen" / "lightpink" / "lightsalmon" / "lightseagreen" / "lightskyblue" / "lightslategray" / "lightsteelblue" / "lightyellow" / "lime" / "limegreen" / "linen" / "magenta" / "maroon" / "mediumaquamarine" / "mediumblue" / "mediumorchid" / "mediumpurple" / "mediumseagreen" / "mediumslateblue" / "mediumspringgreen" / "mediumturquoise" / "mediumvioletred" / "midnightblue" / "mintcream" / "mistyrose" / "moccasin" / "navajowhite" / "navy" / "oldlace" / "olive" / "olivedrab" / "orange" / "orangered" / "orchid" / "palegoldenrod" / "palegreen" / "paleturquoise" / "palevioletred" / "papayawhip" / "peachpuff" / "peru" / "pink" / "plum" / "powderblue" / "purple" / "red" / "rosybrown" / "royalblue" / "saddlebrown" / "salmon" / "sandybrown" / "seagreen" / "seashell" / "sienna" / "silver" / "skyblue" / "slateblue" / "slategray" / "snow" / "springgreen" / "steelblue" / "tan" / "teal" / "thistle" / "tomato" / "turquoise" / "violet" / "wheat" / "white" / "whitesmoke" / "yellow" / "yellowgreen"
nl = "\n"

blk_open = "{blk_open}"
blk_close = "{blk_close}"
comment = ~"{comment_delim}[^{comment_delim}]*{comment_delim}"

any = ~"."
___ = ~"\s*" (comment ~"\s*")?
_ = ~"\s+"
'''.format(
    comment_delim=COMMENT_DELIM,
    blk_open=BLK_OPEN,
    blk_close=BLK_CLOSE))
