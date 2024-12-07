from PyQt5.QtCore import QEvent, QObject
from PyQt5.QtCore import QPropertyAnimation, QEasingCurve
from PyQt5.QtWidgets import QGraphicsOpacityEffect
from qfluentwidgets import ProgressBar


class LoadProgressBar(ProgressBar):

    @staticmethod
    def windowOpacityAnimation(obj: ProgressBar, sv, ev, time: float) -> QPropertyAnimation:
        graphicsEffect: QGraphicsOpacityEffect = obj.graphicsEffect()
        animation = QPropertyAnimation(graphicsEffect, b"opacity")
        animation.setDuration(int(time))  # 动画持续时间（毫秒）
        animation.setStartValue(sv)  # 起始透明度（不透明）
        animation.setEndValue(ev)  # 结束透明度（完全透明）
        animation.setEasingCurve(QEasingCurve.Linear)  # 设置动画的曲线效果
        return animation

    def __init__(self, parent):
        super(LoadProgressBar, self).__init__(parent)
        parent.installEventFilter(self)
        self.setFixedWidth(parent.width())
        self.move(parent.height() - self.height(), 0)
        self.setGraphicsEffect(QGraphicsOpacityEffect())

    def eventFilter(self, obj: QObject, e: QEvent) -> bool:
        if e.type() == QEvent.Resize:
            self.setFixedWidth(obj.width())
            self.move(0, obj.height() - self.height())
        return False

    def show(self, needAni: bool = True) -> None:
        opacity: float = self.graphicsEffect().opacity()
        if needAni and (opacity != 1 or self.isHidden()):
            # 创建 QPropertyAnimation
            super(LoadProgressBar, self).show()
            self.animation = self.windowOpacityAnimation(self, sv=0, ev=1, time=3000 - opacity * 3000)
            self.animation.finished.connect(super(LoadProgressBar, self).show)
            self.animation.start()  # 开始动画
        else:
            super(LoadProgressBar, self).show()

    def hide(self, needAni: bool = True) -> None:
        opacity: float = self.graphicsEffect().opacity()
        if needAni and opacity != 0:
            # 创建 QPropertyAnimation
            self.animation = self.windowOpacityAnimation(self, sv=1, ev=0, time=opacity * 3000)
            self.animation.finished.connect(super(LoadProgressBar, self).hide)
            self.animation.start()  # 开始动画
        else:
            super(LoadProgressBar, self).hide()
