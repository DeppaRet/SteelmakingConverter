from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

import app_theme
from theme_settings import get_theme, manager
from locale_settings import manager as locale_manager


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(500, 220)
        Dialog.setMinimumSize(380, 160)
        self._dialog = Dialog

        outer = QtWidgets.QVBoxLayout(Dialog)
        outer.setContentsMargins(28, 24, 28, 24)
        outer.setSpacing(14)

        title = QtWidgets.QLabel()
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self._title_label = title
        outer.addWidget(title)

        divider = QtWidgets.QFrame()
        divider.setFrameShape(QtWidgets.QFrame.HLine)
        self._divider = divider
        outer.addWidget(divider)

        self.label = QtWidgets.QLabel()
        self.label.setObjectName("label")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFont(QFont("Segoe UI", 10))
        self.label.setWordWrap(True)
        outer.addWidget(self.label)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)
        self.refresh_theme()
        manager().theme_changed.connect(lambda _t: self.refresh_theme())
        locale_manager().language_changed.connect(
            lambda _l: self.refresh_language(Dialog)
        )

    def refresh_language(self, Dialog):
        self.retranslateUi(Dialog)

    def refresh_theme(self):
        theme = get_theme()
        t = app_theme.tokens(theme)
        self._dialog.setPalette(app_theme.palette(theme))
        self._dialog.setStyleSheet(app_theme.about_style(theme))
        if hasattr(self, "_title_label"):
            self._title_label.setStyleSheet(
                f"color: {t['accent2']}; margin-bottom: 4px;")
        if hasattr(self, "_divider"):
            self._divider.setStyleSheet(
                f"color: rgba(0, 120, 168, 0.3);")
        if hasattr(self, "label"):
            self.label.setStyleSheet(f"color: {t['text']};")

    def retranslateUi(self, Dialog):
        from i18n import tr as _t
        Dialog.setWindowTitle(_t("Dialog", "О программе"))
        self._title_label.setText(_t("Dialog", "О программе"))
        self.label.setText(_t("Dialog",
            "Программный комплекс предназначен для обучения\n"
            "операторов-дистрибьюторов управлению сталеплавильным конвертером.\n\n"
            "Разработан в рамках ВКР студентом группы 429м\n"
            "Левинским Ильёй"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ui = Ui_Dialog()
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())
