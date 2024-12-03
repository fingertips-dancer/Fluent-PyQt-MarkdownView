import io
import os
import typing as t

import matplotlib.font_manager as mfm
from PyQt5.QtCore import QPointF
from PyQt5.QtCore import Qt, QByteArray, QRectF, QSizeF
from PyQt5.QtGui import QPainter, QFontMetrics, QImage, QColor
from PyQt5.QtSvg import QSvgRenderer
from matplotlib.mathtext import MathTextParser

# from .cursor import MarkdownCursor
from .markdown_ast import MarkdownASTBase
from .text_paragraph import TextParagraph


class ImageRender():
    latexPool = {}
    imagePool = {}

    @classmethod
    def math_to_image(cls, s, filename_or_obj, prop=None, dpi=None, format=None, *, color=None):
        """
        Given a math expression, renders it in a closely-clipped bounding
        box to an image file.

        Parameters
        ----------
        s : str
            A math expression.  The math portion must be enclosed in dollar signs.
        filename_or_obj : str or path-like or file-like
            Where to write the image data.
        prop : `.FontProperties`, optional
            The size and style of the text.
        dpi : float, optional
            The output dpi.  If not set, the dpi is determined as for
            `.Figure.savefig`.
        format : str, optional
            The output format, e.g., 'svg', 'pdf', 'ps' or 'png'.  If not set, the
            format is determined as for `.Figure.savefig`.
        color : str, optional
            Foreground color, defaults to :rc:`text.color`.
        """
        from matplotlib import figure

        parser = MathTextParser('path')
        width, height, depth, _, _ = parser.parse(s, dpi=72, prop=prop)
        fig = figure.Figure(figsize=(width / 72.0, height / 72.0))
        fig.text(0, depth / height, s, fontproperties=prop, color=color)
        fig.savefig(filename_or_obj, dpi=dpi, format=format)

        return depth

    @classmethod
    def renderLatexSvg(cls, latex: str) -> io.BytesIO:
        if latex not in cls.latexPool:
            prop = mfm.FontProperties(math_fontfamily='stix', size=64, weight='bold')
            bfo = io.BytesIO()
            try:
                cls.math_to_image(rf"${latex}$", bfo, prop=prop, dpi=72, format="svg")
            except Exception as e:
                print(type(e))
                string = str(e)
                for excetion in ["ParseSyntaxException:", "ParseFatalException", "ParseException"]:
                    if excetion in string:
                        cls.math_to_image(rf"Latex Error: {latex}", bfo, prop=prop, dpi=72, format="svg", color="r")
                        break
                else:
                    raise e
            bfo.seek(0)  # 重置指针
            cls.latexPool[latex] = bfo
        return cls.latexPool[latex]

    @classmethod
    def renderImage(cls, url: str) -> QImage:
        if url not in cls.imagePool:
            # 如果不存在
            if os.path.exists(url):
                cls.imagePool[url] = QImage(url)
            else:
                cls.imagePool[url] = None
        return cls.imagePool[url]


@TextParagraph.registerRenderFunction(TextParagraph.Render_BlankLine)
def renderBlankLine(tp: TextParagraph, data: t.Any, ast: MarkdownASTBase, painter: QPainter):
    painter.drawLine(QPointF(tp.margins().left(), tp.paintPoint().y() + tp.lineHeight() / 2),
                     QPointF(tp.viewWdith() - tp.margins().right(),
                             tp.paintPoint().y() + tp.lineHeight() / 2))
    tp.setPaintPoint(QPointF(tp.viewWdith() - tp.margins().right(), tp.paintPoint().y()))


@TextParagraph.registerRenderFunction(TextParagraph.Render_SoftBreak)
def renderSoftBreak(tp: TextParagraph, data: t.Any, ast: MarkdownASTBase, painter: QPainter):
    fm = QFontMetrics(painter.font())
    tp.addCursorBase(tp.paintPoint() + QPointF(0, 0))
    # paint pos
    pos = QPointF(tp.margins().left() + tp.indentation(),
                  tp.paintPoint().y() + fm.height() + tp.inPragraphReutrnSpace())
    tp.setPaintPoint(pos)


@TextParagraph.registerRenderFunction(TextParagraph.Render_HardBreak)
def renderHardBreak(tp: TextParagraph, data: t.Any, ast: MarkdownASTBase, painter: QPainter):
    fm = QFontMetrics(painter.font())
    tp.addCursorBase(tp.paintPoint() + QPointF(0, 0))
    # paint pos
    pos = QPointF(tp.margins().left(), tp.paintPoint().y() + fm.height() + tp.outPragraphReutrnSpace())
    tp.setPaintPoint(pos)


@TextParagraph.registerRenderFunction(TextParagraph.Render_Text)
def renderText(tp: TextParagraph, data: t.Any, ast: MarkdownASTBase, painter: QPainter, haveBreak=False):
    """
    :param tp: TextParagraph
    :param data: content need render
    :param ast: ast
    :param painter: QPainter
    :param haveBreak: It is have break symbol in data
    :return:
    """
    # 使用 QFontMetrics 计算文本的尺寸
    fm, text = painter.fontMetrics(), data
    rep = QPointF(0, tp.lineHeight() - fm.descent())
    for char in text:

        char_width = fm.width(char)  # 获取文本宽度,高度
        tp.addCursorBase(tp.paintPoint() + QPointF(0, 0))
        # return line
        # 换行功能需要手动实现
        if tp.paintPoint().x() + char_width > tp.viewWdith() - tp.margins().right() or char == "\n":
            tp.setPaintPoint(QPointF(tp.margins().left() + tp.indentation(),
                                     tp.paintPoint().y() + tp.lineHeight() + tp.inPragraphReutrnSpace()))
        painter.drawText(tp.paintPoint() + rep, char)
        # pos transfome
        tp.setPaintPoint(tp.paintPoint() + QPointF(char_width, 0))


@TextParagraph.registerRenderFunction(TextParagraph.Render_HideText)
def renderHideText(tp: TextParagraph, data: t.Any, ast: MarkdownASTBase, painter: QPainter):
    """" 绘制隐藏的文本 """
    fm, text = QFontMetrics(painter.font()), data
    t = QPointF(0, 0)
    for char in text:
        tp.addCursorBase(tp.paintPoint() + t)


@TextParagraph.registerRenderFunction(TextParagraph.Render_SerialNumber)
def renderSerialNumber(tp: TextParagraph, data: t.Union[int, str], ast: MarkdownASTBase, painter: QPainter):
    """ 序号 """
    # 在边距外绘制
    _p_pos = tp.paintPoint()
    if isinstance(data, int):
        text = f"{data}."
        fm = QFontMetrics(painter.font())
        painter.drawText(tp.paintPoint() + QPointF(-fm.width(text), tp.lineHeight()), text)


@TextParagraph.registerRenderFunction(TextParagraph.Render_BlockLatexImage)
def renderBlockLatexImage(tp: TextParagraph, data: str, ast: MarkdownASTBase, painter: QPainter):
    """" 绘制latex """
    svgRender = QSvgRenderer(QByteArray(ImageRender.renderLatexSvg(latex=data).getvalue()))

    # 如果不是在边距上,另开一行渲染
    if tp.margins().left() != tp.paintPoint().x():
        tp.setPaintPoint(QPointF(float(tp.margins().left()),
                                 float(tp.paintPoint().y() + tp.lineHeight() + tp.inPragraphReutrnSpace())))
    # reszie
    svgSize = svgRender.defaultSize()

    rect = QRectF(tp.paintPoint(), QSizeF(svgSize))
    # 居中
    rect.moveTo((tp.viewWdith() - tp.margins().left() - tp.margins().right() - rect.width()) / 2, tp.paintPoint().y())

    # 绘制 SVG
    svgRender.render(painter, rect)
    # transfome
    tp.setPaintPoint(QPointF(tp.margins().left(), rect.bottom()))


@TextParagraph.registerRenderFunction(TextParagraph.Render_BlockLatexText)
def renderBlockLatexText(tp: TextParagraph, data: str, ast: MarkdownASTBase, painter: QPainter):
    """" 绘制latex 的文本"""
    # 在绘制 $$
    _p_pos, fm = tp.paintPoint(), QFontMetrics(painter.font())
    renderText(tp=tp, data="$$", ast=ast, painter=painter)
    renderSoftBreak(tp=tp, data=data, ast=ast, painter=painter)

    # 如果不是在边距上,另开一行渲染
    renderText(tp=tp, data=data, ast=ast, painter=painter, haveBreak=True)

    renderSoftBreak(tp=tp, data=data, ast=ast, painter=painter)
    renderText(tp=tp, data="$$", ast=ast, painter=painter)
    renderSoftBreak(tp=tp, data=data, ast=ast, painter=painter)


@TextParagraph.registerRenderFunction(TextParagraph.Render_Image)
def renderImage(tp: TextParagraph, data: str, ast: MarkdownASTBase, painter: QPainter):
    image: QImage = ImageRender.renderImage(url=data)
    # 如果不是在边距上,另开一行渲染
    if tp.margins().left() != tp.paintPoint().x():
        tp.setPaintPoint(QPointF(float(tp.margins().left()),
                                 float(tp.paintPoint().y() + tp.lineHeight() + tp.inPragraphReutrnSpace())))
    width = tp.viewWdith() - tp.margins().left() - tp.margins().right()
    p = QPointF(tp.margins().left(), tp.paintPoint().y()).toPoint()

    # the image is not exists
    if image is None:
        text = "😡没有图片呀!"
        fm = painter.fontMetrics()
        rect = fm.boundingRect(text)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(225, 0, 0, 75))
        img_size = QSizeF(width, rect.height() + 2 * tp.inPragraphReutrnSpace())
        painter.drawRoundedRect(QRectF(p, img_size), 5, 5)
        painter.setPen(QColor(255, 255, 255, 255))
        textP = QPointF((img_size.width() - rect.width()) / 2,
                        (p.y() + (img_size.height() + rect.height()) / 2 - fm.descent()))
        painter.drawText(textP, text)
        nextP = QPointF(tp.margins().left(), tp.paintPoint().y() + img_size.height())
    else:
        # reszie
        image = image.scaled(int(width), int(image.height() / image.width() * width), Qt.KeepAspectRatio)
        painter.drawImage(p, image)
        nextP = QPointF(tp.margins().left(), tp.paintPoint().y() + image.height())
    tp.setPaintPoint(nextP)


@TextParagraph.registerRenderFunction(TextParagraph.Render_InlineLatexImage)
def renderInLineLatexImage(tp: TextParagraph, data: str, ast: MarkdownASTBase, painter: QPainter):
    """" 绘制 Latex  """
    svgRender = QSvgRenderer(QByteArray(ImageRender.renderLatexSvg(latex=data).getvalue()))
    # 1. 判断当前的 svg是否需要超过基线
    jRnder = QSvgRenderer(QByteArray(ImageRender.renderLatexSvg(latex='j').getvalue()))  # 基线判例

    # 2.reszie
    # 2.1调整到size 和行一致
    # 3. 判断当前的 svg是否需要超过基线
    if jRnder.defaultSize().height() == svgRender.defaultSize().height():
        svgHight = painter.fontMetrics().height() - painter.fontMetrics().descent()
    elif jRnder.defaultSize().height() > svgRender.defaultSize().height():
        svgHight = painter.fontMetrics().ascent() - painter.fontMetrics().descent()
    else:
        svgHight = painter.fontMetrics().height() - painter.fontMetrics().descent()
    svgSize = svgRender.defaultSize() * svgHight / svgRender.defaultSize().height()

    # 3.判断是否需要新开一行
    if tp.viewWdith() - tp.paintPoint().x() - tp.margins().right() < svgSize.width():
        tp.setPaintPoint(QPointF(tp.margins().left() + tp.indentation(),
                                 tp.paintPoint().y() + tp.lineHeight() + tp.inPragraphReutrnSpace()))

    # 绘制 SVG
    rect = QRectF(tp.paintPoint() + QPointF(0, painter.fontMetrics().descent() * 2), QSizeF(svgSize))
    svgRender.render(painter, rect)
    # transfome
    # 不计 cursor
    tp.setPaintPoint(tp.paintPoint() + QPointF(rect.width(), 0))


@TextParagraph.registerRenderFunction(TextParagraph.Render_InlineLatexText)
def renderInlineLatexText(tp: TextParagraph, data: str, ast: MarkdownASTBase, painter: QPainter):
    # 自动添加 &
    # 如果不是在边距上,另开一行渲染
    renderText(tp=tp, data="$" + data + "$", ast=ast, painter=painter)
