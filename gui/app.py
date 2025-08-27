from PySide6.QtWidgets import QApplication, QMainWindow, QMenu, QSystemTrayIcon, QStyle


class ChatWindow(QMainWindow):
    """Ventana principal del asistente con icono en la bandeja."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Nexus")
        self.resize(400, 300)

        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))

        menu = QMenu()
        toggle_action = menu.addAction("Mostrar/Ocultar")
        exit_action = menu.addAction("Salir")

        toggle_action.triggered.connect(self.toggle_visibility)
        exit_action.triggered.connect(QApplication.instance().quit)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def toggle_visibility(self) -> None:
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.Trigger:
            self.toggle_visibility()

    def closeEvent(self, event) -> None:  # type: ignore[override]
        event.ignore()
        self.hide()
