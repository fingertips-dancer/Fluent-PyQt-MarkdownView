import typing as t

from PyQt5.QtCore import QPointF, QRectF

from .abstruct import AbstructCursor, AbstractMarkDownDocument
from .cache_paint import CachePaint
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
        self._cachePaint: CachePaint = None

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
        parent = self.parent()
        if flag == self.MOVE_FELT:
            self.setPos(self.pos() - 1)

        elif flag == self.MOVE_RIGHT:
            self.setPos(self.pos() + 1)

        elif flag == self.MOVE_UP:  # 向上
            # 偏移
            self.__moveToPos(pos=QPointF(0, -10 - self._cachePaint.lineHeight(ast=self.ast(), pos=self.pos())))

        elif flag == self.MOVE_DOWN:
            # 偏移
            self.__moveToPos(pos=QPointF(0, 10 + self._cachePaint.lineHeight(ast=self.ast(), pos=self.pos())))

        elif flag == self.MOVE_MOUSE:
            self.__moveToPos(pos)

    def removeSelectionContent(self):
        """ 移除选中 """
        start_ast, start_pos, end_ast, end_pos = self.selectedASTs()
        self.__swap(start_ast=start_ast, start_pos=start_pos, end_ast=end_ast, end_pos=end_pos)
        self.setSelectMode(self.SELECT_MODE_SINGLE)  # 重新设置状态

    def swapSelectionContent(self, text):
        """ 替换选中 """
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

    def __moveToPos(self, pos: QPointF):
        """ 将光标移动 pos(偏移) """
        # 1. find target ast
        y = pos.y() + self._cachePaint.cursorPluginBases(ast=self.ast(), pos=self.pos()).y()
        x = pos.x() + self._cachePaint.cursorPluginBases(ast=self.ast(), pos=self.pos()).x()
        if y > 0:
            for ast in self.rootAst().children[(self.rootAst().index(ast=self.ast())):]:
                if y < self._cachePaint.cachePxiamp()[ast].height():
                    break
                y -= self._cachePaint.cachePxiamp()[ast].height()
            else:
                ast = self.rootAst().children[-1]
        else:
            for ast in self.rootAst().children[:self.rootAst().index(ast=self.ast())][::-1]:
                y += self._cachePaint.cachePxiamp()[ast].height()
                if 0 <= y:
                    break
            else:
                ast = self.rootAst().children[0]
        bs, t = self._cachePaint.cursorPluginBases(ast=ast), 0
        for bi, b in enumerate(bs):
            print(b.y(), y, b.y() + self._cachePaint.lineHeight(ast, bi), len(bs))
            if b.y() <= y <= b.y() + self._cachePaint.lineHeight(ast, bi):
                if b.x() >= x:
                    self.setAST(ast)
                    self.setPos(bi)
                    if bi != 0 and x - bs[bi - 1].x() < b.x() - x:
                        self.setPos(bi - 1)
                    return
                elif len(bs) > bi + 1 and b.y() < bs[bi + 1].y():  # 在同一个段落内换行,选择最右侧
                    self.setAST(ast)
                    self.setPos(bi)
                elif len(bs) == bi + 1:
                    self.setAST(ast)
                    self.setPos(bi)
            elif b.y() > y:
                return

        # self._cachePaint.cachePxiamp()[]

        # parent = self.parent()
        # possible = None
        #
        # # 帅选
        # for i, p in enumerate(parent.textParagraphs()):
        #     if len(p.cursorBases()) == 0: continue
        #     if p.cursorBases()[0].y() < pos.y() <= p.cursorBases()[-1].y() + p.lineHeight():
        #         possible = p
        #         break
        # if possible is None: return
        # ps, t = [p for p in parent.textParagraphs() if p.ast() is possible.ast()], 0
        # for p in ps:
        #     bs = p.cursorBases()
        #     # 加速跳过
        #     # 跳过前面的
        #     for bi, b in enumerate(bs):
        #         if b.y() <= pos.y() <= b.y() + p.lineHeight():
        #             if b.x() >= pos.x():
        #                 self.setAST(p.ast())
        #                 self.setPos(t)
        #                 if bi != 0 and pos.x() - bs[bi - 1].x() < b.x() - pos.x():
        #                     self.setPos(t - 1)
        #                 return
        #             elif len(bs) > bi + 1 and b.y() < bs[bi + 1].y():  # 在同一个段落内换行,选择最右侧
        #                 self.setAST(p.ast())
        #                 self.setPos(t)
        #             elif len(bs) == bi + 1:
        #                 self.setAST(p.ast())
        #                 self.setPos(t)
        #                 return
        #         t += 1
        return

    def rect(self) -> QRectF:
        parent = self.parent()
        if len(parent.textParagraphs()) != 0:
            ps = [p for p in parent.textParagraphs() if p.ast() is self.ast()]
            all_bases = []
            for p in ps: all_bases += p.cursorBases()
            return QRectF(all_bases[self.pos()], all_bases[self.pos()] + QPointF(1, p.lineHeight()))
        return QRectF(0, 0, 1, 1)

    def ast(self) -> MarkdownASTBase:
        return super(MarkdownCursor, self).ast()

    def rootAst(self) -> MarkdownAstRoot:
        """ root ast """
        return self.ast().parent

    def setAST(self, ast: MarkdownASTBase, pos: int = None):
        assert isinstance(ast.parent, MarkdownAstRoot), ""
        assert isinstance(pos, int) or pos is None, ""
        super(MarkdownCursor, self).setAST(ast=ast, pos=pos)

    def isIn(self, ast: MarkdownASTBase):
        """ 是否在这个节点中"""
        if not (self.ast().isChild(ast) or self.ast() is ast):
            return
        p_markdown = self.ast().toMarkdown()
        sub_markdown = ast.toMarkdown()
        return sub_markdown in p_markdown[max(0, self.pos() - len(sub_markdown)):
                                          min(self.pos() + len(sub_markdown), len(p_markdown))]

    def parent(self) -> AbstractMarkDownDocument:
        return super(MarkdownCursor, self).parent()
