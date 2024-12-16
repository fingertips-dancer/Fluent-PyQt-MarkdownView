import re
import time

from sympy import solve
from sympy import symbols
from sympy.parsing.sympy_parser import parse_expr

_nSymbol = symbols("n")


def paserMatch_nth_child(source: str, target: int) -> bool:
    """ 匹配 nth-child"""
    st = time.time()
    # 使用正则表达式替换数字和n的组合
    # 正则表达式：r'(\d+)(n)' 匹配数字后跟着字母n
    source = re.sub(r'(\d+)(n)', r'\1*\2', source)
    source = re.sub(r'(n)(\d+)', r'\1*\2', source)

    #  使用 parse_expr 解析替换后的表达式
    expr = parse_expr(source + f"-{target}", evaluate=False)
    # 求解方程
    # 只要整数解
    solutions = solve(expr, _nSymbol)

    result = expr.subs(_nSymbol, int(solutions[0]))
    # 查看是否有整数解
    # print(1,time.time()-st)
    return int(result) == 0
