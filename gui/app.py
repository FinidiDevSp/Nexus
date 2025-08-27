"""Interfaz gráfica sencilla para interactuar con :class:`NexusAssistant`.

Incluye un área de conversación con burbujas de mensajes, una barra
superior y controles de entrada para enviar texto al asistente.
"""

import json
import threading

import keyboard
import speech_recognition as sr
from datetime import datetime

from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGraphicsOpacityEffect,
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

from main import CONFIG_FILE, NexusAssistant


class ChatBubble(QWidget):
    """Pequeño widget con apariencia de burbuja de chat."""

    def __init__(
        self,
        text: str,
        is_user: bool,
        avatar: QPixmap | None = None,
        theme: str = "light",
    ) -> None:
        super().__init__()
        self.is_user = is_user
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setAlignment(Qt.AlignRight if is_user else Qt.AlignLeft)

        avatar_label = QLabel()
        if avatar is not None and not avatar.isNull():
            avatar_label.setPixmap(
                avatar.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        else:
            avatar_icon = self.style().standardIcon(
                QStyle.SP_DialogYesButton if is_user else QStyle.SP_ComputerIcon
            )
            avatar_label.setPixmap(avatar_icon.pixmap(32, 32))
        avatar_label.setFixedSize(32, 32)

        self.bubble = QLabel(text)
        self.bubble.setWordWrap(True)
        self.update_theme(theme)

        if is_user:
            layout.addStretch()
            layout.addWidget(self.bubble)
            layout.addWidget(avatar_label)
        else:
            layout.addWidget(avatar_label)
            layout.addWidget(self.bubble)
            layout.addStretch()

    def update_theme(self, theme: str) -> None:
        """Actualizar los colores de la burbuja según el tema."""
        if theme == "dark":
            bg = "#3D7E9A" if self.is_user else "#4E4E4E"
            text_color = "#EEEEEE"
        else:
            bg = "#CDE8F6" if self.is_user else "#F0F0F0"
            text_color = "#333333"
        self.bubble.setStyleSheet(
            f"""
            background-color: {bg};
            color: {text_color};
            border-radius: 12px;
            padding: 8px 12px;
            """
        )

    def animate_show(self) -> None:
        """Mostrar la burbuja con una animación suave."""
        final_height = self.sizeHint().height()
        self.setMaximumHeight(0)

        effect = QGraphicsOpacityEffect(self)
        effect.setOpacity(0)
        self.setGraphicsEffect(effect)

        height_anim = QPropertyAnimation(self, b"maximumHeight")
        height_anim.setStartValue(0)
        height_anim.setEndValue(final_height)
        height_anim.setDuration(200)
        height_anim.setEasingCurve(QEasingCurve.OutCubic)

        opacity_anim = QPropertyAnimation(effect, b"opacity")
        opacity_anim.setStartValue(0)
        opacity_anim.setEndValue(1)
        opacity_anim.setDuration(200)

        self._anim_refs = (height_anim, opacity_anim)
        height_anim.start()
        opacity_anim.start()


class ChatWindow(QMainWindow):
    """Ventana principal del asistente con icono en la bandeja."""

    def __init__(self, assistant: NexusAssistant | None = None) -> None:
        super().__init__()
        self.setWindowTitle("Nexus")
        self.resize(400, 500)

        # Asistente -----------------------------------------------------------
        self.assistant = assistant or NexusAssistant()
        self.assistant.speak_callback = lambda text: QTimer.singleShot(0, lambda: self.add_message(text, is_user=False))
        self.listening = False
        self.listen_thread: threading.Thread | None = None

        # Avatares ------------------------------------------------------------
        self.user_avatar = self._load_avatar_pixmap(self.assistant.config.get("avatar_usuario"))
        self.bot_avatar = self._load_avatar_pixmap(self.assistant.config.get("avatar_asistente"))

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
        self.top_bar = QWidget()
        top_layout = QHBoxLayout(self.top_bar)
        avatar = QLabel()
        avatar.setPixmap(self.style().standardIcon(QStyle.SP_ComputerIcon).pixmap(32, 32))
        title_box = QVBoxLayout()
        self.title = QLabel("Need help?")
        self.subtitle = QLabel("We reply immediately")
        title_box.addWidget(self.title)
        title_box.addWidget(self.subtitle)
        top_layout.addWidget(avatar)
        top_layout.addLayout(title_box)
        top_layout.addStretch()
        settings_btn = QToolButton()
        settings_btn.setIcon(self.style().standardIcon(QStyle.SP_FileDialogDetailedView))
        settings_menu = QMenu(settings_btn)
        user_menu = settings_menu.addMenu("Avatar usuario")
        asis_menu = settings_menu.addMenu("Avatar asistente")
        for menu, is_user in ((user_menu, True), (asis_menu, False)):
            action_def = menu.addAction("Predeterminado")
            action_def.triggered.connect(lambda _=False, u=is_user: self._set_avatar_style(u))
            action_comp = menu.addAction("Computadora")
            action_comp.triggered.connect(lambda _=False, u=is_user: self._set_avatar_style(u, computer=True))
            menu.addSeparator()
            action_upload = menu.addAction("Cargar imagen...")
            action_upload.triggered.connect(lambda _=False, u=is_user: self._load_avatar_image(u))
        theme_menu = settings_menu.addMenu("Tema")
        action_light = theme_menu.addAction("Claro")
        action_dark = theme_menu.addAction("Oscuro")
        action_auto = theme_menu.addAction("Automático")
        action_light.triggered.connect(lambda: self._set_theme("light"))
        action_dark.triggered.connect(lambda: self._set_theme("dark"))
        action_auto.triggered.connect(lambda: self._set_theme("auto"))
        settings_btn.setMenu(settings_menu)
        settings_btn.setPopupMode(QToolButton.InstantPopup)
        min_btn = QToolButton()
        min_btn.setIcon(self.style().standardIcon(QStyle.SP_TitleBarMinButton))
        min_btn.clicked.connect(self.showMinimized)
        close_btn = QToolButton()
        close_btn.setIcon(self.style().standardIcon(QStyle.SP_TitleBarCloseButton))
        close_btn.clicked.connect(self.close)
        top_layout.addWidget(settings_btn)
        top_layout.addWidget(min_btn)
        top_layout.addWidget(close_btn)
        v_layout.addWidget(self.top_bar)

        # Área de mensajes
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.messages_widget = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.addStretch()
        self.scroll_area.setWidget(self.messages_widget)
        v_layout.addWidget(self.scroll_area, 1)

        # Entrada de texto
        self.input_bar = QWidget()
        input_layout = QHBoxLayout(self.input_bar)
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
        v_layout.addWidget(self.input_bar)

        keyboard.add_hotkey(self.assistant.hotkey, self._hotkey_listen)

        # Aplicar tema inicial y comprobar cambios automáticos
        self.theme_timer = QTimer(self)
        self.theme_timer.timeout.connect(self._update_theme_if_auto)
        self.theme_timer.start(60000)
        self._apply_theme(self._calculate_theme())

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

    def _load_avatar_pixmap(self, path: str | None) -> QPixmap | None:
        if path:
            pix = QPixmap(path)
            if not pix.isNull():
                return pix
        return None

    def _save_config(self) -> None:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.assistant.config, f, ensure_ascii=False, indent=2)

    def _set_avatar_style(self, is_user: bool, computer: bool = False) -> None:
        if computer:
            icon = QStyle.SP_ComputerIcon if is_user else QStyle.SP_DriveHDIcon
        else:
            icon = QStyle.SP_DialogYesButton if is_user else QStyle.SP_ComputerIcon
        pix = self.style().standardIcon(icon).pixmap(32, 32)
        key = "avatar_usuario" if is_user else "avatar_asistente"
        self.assistant.config[key] = ""
        if is_user:
            self.user_avatar = pix
        else:
            self.bot_avatar = pix
        self._save_config()

    def _load_avatar_image(self, is_user: bool) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar imagen", "", "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if path:
            pix = QPixmap(path)
            if not pix.isNull():
                key = "avatar_usuario" if is_user else "avatar_asistente"
                self.assistant.config[key] = path
                if is_user:
                    self.user_avatar = pix
                else:
                    self.bot_avatar = pix
                self._save_config()

    # Temas -----------------------------------------------------------------
    def _calculate_theme(self) -> str:
        mode = self.assistant.config.get("tema", "auto")
        if mode == "dark" or mode == "oscuro":
            return "dark"
        if mode == "light" or mode == "claro":
            return "light"
        hour = datetime.now().hour
        return "dark" if hour >= 20 or hour < 7 else "light"

    def _apply_theme(self, theme: str) -> None:
        self.theme = theme
        if theme == "dark":
            widget_bg = "#2B2B2B"
            text_color = "#EEEEEE"
            line_bg = "#3C3F41"
            line_border = "#555555"
            top_bg = "#3C3F41"
            top_border = "#444444"
            sub_color = "#BBBBBB"
        else:
            widget_bg = "#FAFAFA"
            text_color = "#333333"
            line_bg = "#FFFFFF"
            line_border = "#CCCCCC"
            top_bg = "#FFFFFF"
            top_border = "#E0E0E0"
            sub_color = "#888888"
        self.setStyleSheet(
            f"""
            QWidget {{
                background-color: {widget_bg};
                font-family: Arial, sans-serif;
                font-size: 14px;
                color: {text_color};
            }}
            QLineEdit {{
                border: 1px solid {line_border};
                border-radius: 8px;
                padding: 4px 8px;
                background-color: {line_bg};
            }}
            QToolButton {{
                border-radius: 8px;
                padding: 4px;
            }}
            QScrollArea {{
                border: none;
            }}
            """
        )
        self.top_bar.setStyleSheet(
            f"background-color: {top_bg}; padding: 8px; border-bottom: 1px solid {top_border};"
        )
        self.input_bar.setStyleSheet(
            f"background-color: {top_bg}; padding: 4px; border-top: 1px solid {top_border};"
        )
        self.title.setStyleSheet(
            f"font-weight: bold; color: {text_color}; font-size: 14px;"
        )
        self.subtitle.setStyleSheet(
            f"font-size: 11px; color: {sub_color};"
        )
        # Actualizar burbujas existentes
        for i in range(self.messages_layout.count() - 1):
            item = self.messages_layout.itemAt(i)
            widget = item.widget()
            if isinstance(widget, ChatBubble):
                widget.update_theme(theme)

    def _update_theme_if_auto(self) -> None:
        if self.assistant.config.get("tema", "auto") == "auto":
            new_theme = self._calculate_theme()
            if new_theme != getattr(self, "theme", "light"):
                self._apply_theme(new_theme)

    def _set_theme(self, mode: str) -> None:
        self.assistant.config["tema"] = mode
        self._save_config()
        self._apply_theme(self._calculate_theme())

    # ------------------------------------------------------------------
    def add_message(self, text: str, is_user: bool) -> None:
        avatar = self.user_avatar if is_user else self.bot_avatar
        bubble = ChatBubble(text, is_user, avatar, self.theme)
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, bubble)
        bubble.animate_show()
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

