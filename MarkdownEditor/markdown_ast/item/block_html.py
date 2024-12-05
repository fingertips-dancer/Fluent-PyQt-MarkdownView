from ..base import MarkdownASTBase
from ...abstruct import AbstructCachePaint
from ...abstruct import AbstructCursor
from ...abstruct import AbstructTextParagraph as ATP
from ...style import MarkdownStyle


@MarkdownASTBase.registerAst("block_html")
class BlockHtml(MarkdownASTBase):
    type: str
    raw: str
    info: str = ""
    propertys = ["type", "raw"]
    attrs = ['info']

    def render(self, ht: AbstructCachePaint, style: MarkdownStyle, cursor: AbstructCursor = None):
        isShowHide = False if cursor is None else cursor.isIn(ast=self)
        # 2. 添加缩进
        ht.painter().setFont(style.hintFont(ht.painter().font(), ast="block_math"))
        ph = ht.nowParagraph()
        ph.setBackgroundEnable(True)
        ph.setBackgroundMargins(*style.hintBackgroundMargins(ast='block_math'))
        ph.setIndentation(indentation=style.hintIndentation(ast="block_math"))
        ph.setBackgroundColor(color=style.hintBackgroundColor(ast="block_math"))
        ph.setBackgroundRadius(radius=style.hintBackgroundRadius(ast="block_math"))
        if isShowHide:
            # ```self.info\n
            # self.raw + \n
            # ```
            ht.renderContent(func=ATP.Render_Text, data=self.toMarkdown(), ast=self)
        else:
            ht.renderContent(func=ATP.Render_Text, data=self.raw, ast=self)
        ht.newParagraph()

    def toMarkdown(self) -> str:
        return self.info + "\n" + self.raw

