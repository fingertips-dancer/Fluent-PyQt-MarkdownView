from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QVBoxLayout, QApplication, QFileDialog,QHBoxLayout,QSpacerItem,QSizePolicy
from qfluentwidgets import TransparentPushButton
from qframelesswindow import FramelessWindow

from MarkdownEditor import MarkdownEdit


class View(FramelessWindow):
    def __init__(self):
        super(View, self).__init__()
        self.makdownView = MarkdownEdit()
        self.openBtn = TransparentPushButton(self.tr('open'), self)
        self.saveBtn = TransparentPushButton(self.tr('save'), self)

        self.mianLayout = QVBoxLayout(self)
        self.hLayout = QHBoxLayout()
        self.mianLayout.setContentsMargins(5, 5, 5, 5)
        self.hLayout.addWidget(self.openBtn, alignment=Qt.AlignLeft)
        self.hLayout.addWidget(self.saveBtn, alignment=Qt.AlignLeft)
        self.hLayout.addSpacerItem(QSpacerItem(0,0,QSizePolicy.Expanding,QSizePolicy.Minimum))
        self.mianLayout.addLayout(self.hLayout)
        self.mianLayout.addWidget(self.makdownView)

        self.openBtn.clicked.connect(self.onOpenBtnClickedEvent)
        self.saveBtn.clicked.connect(self.onSaveBtnClickedEvent)

        with open("test.md","r",encoding="utf8") as f:
            self.makdownView.setMarkdown(text=f.read())

    def onOpenBtnClickedEvent(self):
        path, filetype = QFileDialog.getOpenFileName(self.window(), "open markdown", "", "*.md")
        if path == "":return
        with open(path,"r",encoding="utf8") as f:
            self.makdownView.setMarkdown(text=f.read())

    def onSaveBtnClickedEvent(self):
        path, filetype = QFileDialog.getOpenFileName(self.window(), "open markdown", "", "*.md")
        if path == "":return
        self.makdownView.save(path)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    view = View()
    view.show()
    sys.exit(app.exec_())
