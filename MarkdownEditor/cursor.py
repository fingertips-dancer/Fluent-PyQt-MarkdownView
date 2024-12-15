import typing as t

from PyQt5.QtCore import QPointF, QPoint

from .abstruct import AbstructCursor, AbstractMarkDownDocument, AbstractMarkdownEdit
from .markdown_ast import Text, MarkdownASTBase, Image, MarkdownAstRoot


class MarkdownCursor(AbstructCursor):
    MOVE_FELT = 1
    MOVE_RIGHT = 2
    MOVE_MOUSE = 3
    MOVE_DOWN = 4
    MOVE_UP = 5

    contentAST = (Text, Image)

    def __init__(self, parent):
        super(MarkdownCursor, self).__init__(parent)

    def setAST(self, ast: MarkdownASTBase, pos: int = None):
        assert isinstance(ast.parent, MarkdownAstRoot), ""
        assert isinstance(pos, int) or pos is None, ""
        super(MarkdownCursor, self).setAST(ast=ast, pos=pos)

    def add(self, text: str) -> None:
        """添加文本"""
        self.swapSelectionContent(text=text)

    def pop(self, _len):
        """ 删除 """
        if _len == 0: return
        # 倒叙查找之前的idx
        # 可能不够删除
        children = self.rootAst().children[:self.rootAst().index(self.ast())][::-1]
        can_pop_len, next_ast = self.pos(), self.ast()
        for c in children:
            if _len <= can_pop_len: break
            can_pop_len, next_ast = can_pop_len + len(c.toMarkdown()), c
        # 计算开始 pos
        start_idx = can_pop_len - _len
        # remove
        self.__swap(start_ast=next_ast, start_pos=start_idx, end_ast=self.ast(), end_pos=self.pos())

    def _return(self):
        """换行"""
        # 1.获取这个文本段落
        markdown, root = self.ast().toMarkdown(), self.rootAst()
        # 2.分类
        # 2.1新开一个段落
        if markdown[self.pos():] == "\n":
            idx = root.index(self.ast())
            self.setAST(root.insert(ast="paragraph", idx=idx + 1))
            self.setPos(0)
        else:
            self.add("\n")

    def __swap_content_in_stard_and_end(self, s: int, e: int, markdown) -> t.Tuple[t.List[MarkdownASTBase], int]:
        """ 返回 markdown 分析处的ast , 以及插入的位置"""
        # 1.添加
        isup = s != 0
        isdown = e != len(self.rootAst().children)

        # 联通上下两个段落重新分析
        root: MarkdownAstRoot = self.rootAst()
        anys = MarkdownAstRoot()
        text_list = ([root.children[s - 1].toMarkdown()] if isup else []) + \
                    [markdown] + \
                    ([root.children[e].toMarkdown()] if isdown else [])
        anys.setText("".join(text_list))
        # 重置
        root.swap(old=(s - (1 if isup else 0),
                       e + (1 if isdown else 0)),
                  new=anys.children)
        # 在markdown处理返回结果
        # 分析出的ast
        # 位于的位置
        asts = anys.children
        if not isup:  # 没有向上
            insert_index = 0
        else:
            # 大于表示有新增内容
            if len(asts[0].toMarkdown()) > len(text_list[0]):
                insert_index = len(text_list[0])
            # 内容抱持不变
            elif asts[0].toMarkdown() == text_list[0]:
                insert_index, asts = 0, asts[1:]
            else:  # 小于表示swap的content 导致内容减少
                prosible_text = ""
                for i, ast in enumerate(asts):
                    _prosible_text = prosible_text + ast.toMarkdown()  # 判断是否包含了text_list的部分
                    if len(_prosible_text) > len(text_list[0]):
                        asts, insert_index = asts[i:], len(text_list[0]) - len(prosible_text)
                        break
                    prosible_text = _prosible_text
                else:
                    raise Exception(f"没想到为什么会减少\n{asts[0].toMarkdown()}\n----\n{text_list[0]}")
        if isdown and asts[-1].toMarkdown() == text_list[-1]:
            asts.pop(-1)

        return asts, insert_index

    def move(self, flag, pos: QPointF = None):
        if flag == self.MOVE_FELT:
            self.setPos(self.pos() - 1)

        elif flag == self.MOVE_RIGHT:
            self.setPos(self.pos() + 1)

        elif flag == self.MOVE_UP:  # 向上
            bs = self.parent().cursorBases(ast=self.ast())
            g = self.parent().geometryOf(self.ast())
            next_ast = self.parent().astIn(pos=g.topRight() + QPoint(-1, -2))
            next_bs = self.parent().cursorBases(ast=next_ast) if next_ast else []
            cp = self.parent().cursorBases(ast=self.ast(), pos=self.pos())
            # all y value
            ys = {p.y() for p in bs + next_bs}
            # filter
            y = max((y for y in ys if y < cp.y()), default=cp.y())
            self.parent().cursorMoveTo(QPoint(int(cp.x()), int(y)))

        elif flag == self.MOVE_DOWN:
            bs = self.parent().cursorBases(ast=self.ast())
            g = self.parent().geometryOf(self.ast())
            next_ast = self.parent().astIn(pos=g.bottomRight() + QPoint(-1, 2))
            next_bs = self.parent().cursorBases(ast=next_ast) if next_ast else []
            cp = self.parent().cursorBases(ast=self.ast(), pos=self.pos())
            # all y value
            ys = {p.y() for p in bs + next_bs}
            # filter
            y = min((y for y in ys if y > cp.y()), default=cp.y())
            self.parent().cursorMoveTo(QPoint(int(cp.x()), int(y)))

        elif flag == self.MOVE_MOUSE:
            self.parent().cursorMoveTo(pos)

    def removeSelectionContent(self):
        """ 移除选中 """
        start_ast, start_pos, end_ast, end_pos = self.selectedASTs()
        self.__swap(start_ast=start_ast, start_pos=start_pos, end_ast=end_ast, end_pos=end_pos)
        self.setSelectMode(self.SELECT_MODE_SINGLE)  # 重新设置状态

    def swapSelectionContent(self, text):
        """ 替换选中 """
        # 如果是在末端添加 “ ”
        # 需要删除,因为markdown 不支持
        if len(self.ast().toMarkdown()) == self.pos() + 1:
            text = text.rstrip()
        start_ast, start_pos, end_ast, end_pos = self.selectedASTs()
        self.__swap(start_ast=start_ast, start_pos=start_pos, end_ast=end_ast, end_pos=end_pos, text=text)
        self.setSelectMode(self.SELECT_MODE_SINGLE)  # 重新设置状态

    def __swap(self,
               start_ast: MarkdownASTBase, start_pos: int,
               end_ast: MarkdownASTBase, end_pos: int,
               text="",
               isMoveCursor: bool = True):
        """ 移除内容 """
        # 1.计算需要更新的markdown
        start_idx, end_idx = self.rootAst().index(start_ast), self.rootAst().index(end_ast)
        new_markdown = start_ast.toMarkdown()[:start_pos] + text + end_ast.toMarkdown()[end_pos:]
        asts, insertidx = self.__swap_content_in_stard_and_end(s=start_idx, e=end_idx + 1, markdown=new_markdown)
        if isMoveCursor:
            # 可能减少block,也可能增加block
            # 所以需要重新定位
            # 原始长度 + cusror原始位置 - 删除长度 ----< cursor
            posible_pos = insertidx + start_pos + len(text)
            if len(asts) == 0:  # 没有解释出新段落
                # 3. 没有解释出新段落
                # 3. 原来的段落会被消除
                # 3. 重新开辟一个新段落
                self.setAST(self.rootAst().astOf(start_idx - 1))
                self.setPos(self.POSITION_END)
                self._return()
            elif len(asts[0].toMarkdown()) > posible_pos:
                self.setAST(ast=asts[0])
                self.setPos(posible_pos)
            else:
                # 当前容纳不下
                for ast in asts:
                    t = len(ast.toMarkdown())
                    if posible_pos >= t:
                        posible_pos -= t
                    else:
                        self.setAST(ast=ast)
                        self.setPos(posible_pos)
                        break
                else:
                    raise Exception(asts)

    def isIn(self, ast: MarkdownASTBase):
        """ 是否在这个节点中"""
        if not (self.ast().isChild(ast) or self.ast() is ast):
            return False
        p_markdown = self.ast().toMarkdown()
        sub_markdown = ast.toMarkdown()
        return sub_markdown in p_markdown[max(0, self.pos() - len(sub_markdown)):
                                          min(self.pos() + len(sub_markdown), len(p_markdown))]

    def ast(self) -> MarkdownASTBase:
        return super(MarkdownCursor, self).ast()

    def rootAst(self) -> MarkdownAstRoot:
        """ root ast """
        return self.ast().parent

    def parent(self) -> AbstractMarkdownEdit:
        return super(MarkdownCursor, self).parent()

    def document(self) -> AbstractMarkDownDocument:
        return self.parent().document()
