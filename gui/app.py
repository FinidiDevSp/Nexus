"""Interfaz gráfica sencilla para interactuar con :class:`NexusAssistant`.

Incluye un área de conversación con burbujas de mensajes, una barra
superior y controles de entrada para enviar texto al asistente.
"""

import threading

import keyboard
import speech_recognition as sr
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QScrollArea,
    QSystemTrayIcon,
    QStyle,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from main import NexusAssistant


class ChatBubble(QWidget):
    """Pequeño widget con apariencia de burbuja de chat."""

    def __init__(self, text: str, is_user: bool) -> None:
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setAlignment(Qt.AlignRight if is_user else Qt.AlignLeft)

        avatar = QLabel()
        avatar_icon = self.style().standardIcon(
            QStyle.SP_DialogYesButton if is_user else QStyle.SP_ComputerIcon
        )
        avatar.setPixmap(avatar_icon.pixmap(32, 32))
        avatar.setFixedSize(32, 32)

        bubble = QLabel(text)
        bubble.setWordWrap(True)
        bubble.setStyleSheet(
            """
            background-color: %s;
            color: #333333;
            border-radius: 12px;
            padding: 8px 12px;
            """
            % ("#CDE8F6" if is_user else "#F0F0F0")
        )

        if is_user:
            layout.addStretch()
            layout.addWidget(bubble)
            layout.addWidget(avatar)
        else:
            layout.addWidget(avatar)
            layout.addWidget(bubble)
            layout.addStretch()


class ChatWindow(QMainWindow):
    """Ventana principal del asistente con icono en la bandeja."""

    def __init__(self, assistant: NexusAssistant | None = None) -> None:
        super().__init__()
        self.setWindowTitle("Nexus")
        self.resize(400, 500)
        self.setStyleSheet(
            """
            QWidget {
                background-color: #FAFAFA;
                font-family: Arial, sans-serif;
                font-size: 14px;
                color: #333333;
            }
            QLineEdit {
                border: 1px solid #CCCCCC;
                border-radius: 8px;
                padding: 4px 8px;
                background-color: #FFFFFF;
            }
            QToolButton {
                border-radius: 8px;
                padding: 4px;
            }
            QScrollArea {
                border: none;
            }
            """
        )

        # Asistente -----------------------------------------------------------
        self.assistant = assistant or NexusAssistant()
        self.assistant.speak_callback = lambda text: QTimer.singleShot(0, lambda: self.add_message(text, is_user=False))
        self.listening = False
        self.listen_thread: threading.Thread | None = None

        # Icono en bandeja ----------------------------------------------------
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

        # Interface principal -------------------------------------------------
        central = QWidget()
        self.setCentralWidget(central)
        v_layout = QVBoxLayout(central)

        # Barra superior
        top_bar = QWidget()
        top_bar.setStyleSheet(
            "background-color: #FFFFFF; padding: 8px; border-bottom: 1px solid #E0E0E0;"
        )
        top_layout = QHBoxLayout(top_bar)
        avatar = QLabel()
        avatar.setPixmap(self.style().standardIcon(QStyle.SP_ComputerIcon).pixmap(32, 32))
        title_box = QVBoxLayout()
        title = QLabel("Need help?")
        title.setStyleSheet("font-weight: bold; color: #333333; font-size: 14px;")
        subtitle = QLabel("We reply immediately")
        subtitle.setStyleSheet("font-size: 11px; color: #888888;")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        top_layout.addWidget(avatar)
        top_layout.addLayout(title_box)
        top_layout.addStretch()
        min_btn = QToolButton()
        min_btn.setIcon(self.style().standardIcon(QStyle.SP_TitleBarMinButton))
        min_btn.clicked.connect(self.showMinimized)
        close_btn = QToolButton()
        close_btn.setIcon(self.style().standardIcon(QStyle.SP_TitleBarCloseButton))
        close_btn.clicked.connect(self.close)
        top_layout.addWidget(min_btn)
        top_layout.addWidget(close_btn)
        v_layout.addWidget(top_bar)

        # Área de mensajes
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.messages_widget = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.addStretch()
        self.scroll_area.setWidget(self.messages_widget)
        v_layout.addWidget(self.scroll_area, 1)

        # Entrada de texto
        input_bar = QWidget()
        input_bar.setStyleSheet(
            "background-color: #FFFFFF; padding: 4px; border-top: 1px solid #E0E0E0;"
        )
        input_layout = QHBoxLayout(input_bar)
        self.input = QLineEdit()
        self.input.setPlaceholderText("Type your message here...")
        self.input.returnPressed.connect(self.send_message)
        send_btn = QToolButton()
        send_btn.setIcon(self.style().standardIcon(QStyle.SP_ArrowForward))
        send_btn.clicked.connect(self.send_message)
        self.mic_btn = QToolButton()
        self.mic_btn.setCheckable(True)
        self.mic_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaVolume))
        self.mic_btn.toggled.connect(self.toggle_listening)
        input_layout.addWidget(self.input, 1)
        input_layout.addWidget(send_btn)
        input_layout.addWidget(self.mic_btn)
        v_layout.addWidget(input_bar)

        keyboard.add_hotkey(self.assistant.hotkey, self._hotkey_listen)

    def _move_to_tray(self) -> None:
        screen = QApplication.primaryScreen().availableGeometry()
        x = screen.width() - self.width()
        y = screen.height() - self.height()
        self.move(x, y)

    def showEvent(self, event) -> None:  # type: ignore[override]
        super().showEvent(event)
        self._move_to_tray()

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

    def toggle_listening(self, active: bool) -> None:
        self.listening = active
        icon = QStyle.SP_MediaStop if active else QStyle.SP_MediaVolume
        self.mic_btn.setIcon(self.style().standardIcon(icon))
        if active:
            self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
            self.listen_thread.start()

    def _listen(self) -> str:
        with sr.Microphone() as source:
            self.assistant.recognizer.adjust_for_ambient_noise(source)
            audio = self.assistant.recognizer.listen(source)
        try:
            comando = (
                self.assistant.recognizer.recognize_google(audio, language="es-ES").lower()
            )
            print(f"Escuchado: {comando}")
            return comando
        except sr.UnknownValueError:
            return ""
        except sr.RequestError:
            self.assistant.speak("Error con el servicio de reconocimiento de voz.")
            return ""

    def _listen_loop(self) -> None:
        while self.listening:
            text = self._listen()
            if text:
                QTimer.singleShot(0, lambda t=text: self.add_message(t, True))
                self.assistant.process_text(text)

    def _hotkey_listen(self) -> None:
        text = self._listen()
        if text:
            QTimer.singleShot(0, lambda t=text: self.add_message(t, True))
            self.assistant.process_text(text)

    # ------------------------------------------------------------------
    def add_message(self, text: str, is_user: bool) -> None:
        bubble = ChatBubble(text, is_user)
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, bubble)
        QTimer.singleShot(
            0,
            lambda: self.scroll_area.verticalScrollBar().setValue(
                self.scroll_area.verticalScrollBar().maximum()
            ),
        )

    def send_message(self) -> None:
        text = self.input.text().strip()
        if not text:
            return
        self.input.clear()
        self.add_message(text, is_user=True)
        # Enviar al asistente
        self.assistant.process_text(text)


__all__ = ["ChatWindow", "ChatBubble"]

