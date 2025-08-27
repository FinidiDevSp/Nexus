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
    QPushButton,
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
        label = QLabel(text)
        label.setWordWrap(True)
        label.setStyleSheet(
            "background-color: %s; border-radius: 8px; padding: 4px 8px;"
            % ("#DCF8C6" if is_user else "#E5E5EA")
        )
        if is_user:
            layout.addStretch()
            layout.addWidget(label)
        else:
            layout.addWidget(label)
            layout.addStretch()


class ChatWindow(QMainWindow):
    """Ventana principal del asistente con icono en la bandeja."""

    def __init__(self, assistant: NexusAssistant | None = None) -> None:
        super().__init__()
        self.setWindowTitle("Nexus")
        self.resize(400, 500)

        # Asistente -----------------------------------------------------------
        self.assistant = assistant or NexusAssistant()
        original_say = self.assistant._say

        def patched_say(text: str) -> None:
            original_say(text)
            QTimer.singleShot(0, lambda: self.add_message(text, is_user=False))

        self.assistant._say = patched_say  # type: ignore[attr-defined]
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
        top_layout = QHBoxLayout(top_bar)
        icon = QLabel()
        icon.setPixmap(self.style().standardIcon(QStyle.SP_ComputerIcon).pixmap(24, 24))
        title = QLabel("Nexus")
        top_layout.addWidget(icon)
        top_layout.addWidget(title)
        top_layout.addStretch()
        info_btn = QToolButton()
        info_btn.setIcon(self.style().standardIcon(QStyle.SP_MessageBoxInformation))
        close_btn = QToolButton()
        close_btn.setIcon(self.style().standardIcon(QStyle.SP_TitleBarCloseButton))
        close_btn.clicked.connect(self.close)
        top_layout.addWidget(info_btn)
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
        input_layout = QHBoxLayout(input_bar)
        self.input = QLineEdit()
        self.input.returnPressed.connect(self.send_message)
        send_btn = QPushButton("Enviar")
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
            self.assistant._say("Error con el servicio de reconocimiento de voz.")
            return ""

    def _listen_loop(self) -> None:
        while self.listening:
            text = self._listen()
            if text:
                QTimer.singleShot(0, lambda t=text: self.add_message(t, True))
                self.assistant._process(text)

    def _hotkey_listen(self) -> None:
        text = self._listen()
        if text:
            QTimer.singleShot(0, lambda t=text: self.add_message(t, True))
            self.assistant._process(text)

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
        self.assistant._process(text)


__all__ = ["ChatWindow", "ChatBubble"]

