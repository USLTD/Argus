from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QComboBox,
    QSpinBox,
    QLineEdit,
    QPushButton,
    QLabel,
    QGroupBox,
    QHBoxLayout
)

from PyQt6.QtCore import Qt


class SettingsPage(QWidget):

    def __init__(self, bridge=None):

        super().__init__()

        self.bridge = bridge

        self.setStyleSheet("""
            QWidget {
                font-size: 14px;
            }

            QLabel#title {
                font-size: 24px;
                font-weight: bold;
            }

            QLabel#subtitle {
                color: #777;
            }

            QGroupBox {
                font-weight: bold;
                border: 1px solid #cccccc;
                border-radius: 8px;
                margin-top: 12px;
                padding: 12px;
            }

            QLineEdit,
            QSpinBox,
            QComboBox {
                padding: 6px;
                border-radius: 5px;
                border: 1px solid #aaa;
            }

            QPushButton {
                background-color: #2563eb;
                color: white;
                padding: 10px;
                border-radius: 6px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)


        main = QVBoxLayout(self)
        main.setContentsMargins(25, 25, 25, 25)
        main.setSpacing(15)


        title = QLabel(
            "Argus Configuration"
        )

        title.setObjectName(
            "title"
        )

        main.addWidget(title)


        subtitle = QLabel(
            "Configure drivers, scripts and monitoring behavior."
        )

        subtitle.setObjectName(
            "subtitle"
        )

        main.addWidget(subtitle)



        # -------------------------
        # Engine Settings
        # -------------------------

        engine_box = QGroupBox(
            "Engine Settings"
        )

        engine_form = QFormLayout()


        self.driver_override = QLineEdit()

        self.driver_override.setPlaceholderText(
            "Auto detect"
        )

        self.driver_override.setToolTip(
            "Force Argus to use a specific driver."
        )


        engine_form.addRow(
            "Driver Override",
            self.driver_override
        )



        self.poll_interval = QSpinBox()

        self.poll_interval.setRange(
            100,
            60000
        )

        self.poll_interval.setValue(
            1000
        )

        self.poll_interval.setSuffix(
            " ms"
        )


        engine_form.addRow(
            "Refresh Interval",
            self.poll_interval
        )


        engine_box.setLayout(
            engine_form
        )

        main.addWidget(
            engine_box
        )



        # -------------------------
        # Script Settings
        # -------------------------

        script_box = QGroupBox(
            "Script Runtime"
        )

        script_form = QFormLayout()



        self.script_compatibility = QComboBox()

        self.script_compatibility.addItems(
            [
                "skip",
                "load"
            ]
        )

        script_form.addRow(
            "Compatibility",
            self.script_compatibility
        )



        self.script_batch_size = QSpinBox()

        self.script_batch_size.setRange(
            1,
            100
        )

        self.script_batch_size.setValue(
            4
        )

        script_form.addRow(
            "Batch Size",
            self.script_batch_size
        )



        self.script_timeout = QSpinBox()

        self.script_timeout.setRange(
            100,
            60000
        )

        self.script_timeout.setValue(
            5000
        )

        self.script_timeout.setSuffix(
            " ms"
        )


        script_form.addRow(
            "Timeout",
            self.script_timeout
        )



        self.script_execution_mode = QComboBox()

        self.script_execution_mode.addItems(
            [
                "blocking",
                "nonblocking",
                "mixed"
            ]
        )

        self.script_execution_mode.setCurrentText(
            "nonblocking"
        )


        script_form.addRow(
            "Execution Mode",
            self.script_execution_mode
        )


        script_box.setLayout(
            script_form
        )

        main.addWidget(
            script_box
        )



        # -------------------------
        # Performance
        # -------------------------

        performance_box = QGroupBox(
            "Performance"
        )

        performance_form = QFormLayout()


        self.process_tick_interval = QSpinBox()

        self.process_tick_interval.setRange(
            1,
            100
        )

        self.process_tick_interval.setValue(
            5
        )

        performance_form.addRow(
            "Process Tick Interval",
            self.process_tick_interval
        )


        performance_box.setLayout(
            performance_form
        )

        main.addWidget(
            performance_box
        )



        # Save area

        bottom = QHBoxLayout()

        bottom.addStretch()


        self.status = QLabel("")

        bottom.addWidget(
            self.status
        )


        self.save_button = QPushButton(
            "Save Configuration"
        )

        self.save_button.clicked.connect(
            self.save_config
        )

        bottom.addWidget(
            self.save_button
        )


        main.addLayout(
            bottom
        )


    def load_config(self):

        if not self.bridge:
            return


        config = self.bridge.get_config()


        self.driver_override.setText(
            config.get("driver_override") or ""
        )


        self.poll_interval.setValue(
            config.get(
                "poll_interval_ms",
                1000
            )
        )


        self.script_compatibility.setCurrentText(
            config.get(
                "script_compatibility_default",
                "skip"
            )
        )


        self.script_batch_size.setValue(
            config.get(
                "script_batch_size",
                4
            )
        )


        self.script_timeout.setValue(
            config.get(
                "script_timeout_ms",
                5000
            )
        )


        self.script_execution_mode.setCurrentText(
            config.get(
                "script_execution_mode",
                "nonblocking"
            )
        )


        self.process_tick_interval.setValue(
            config.get(
                "process_tick_interval",
                5
            )
        )



    def save_config(self):

        config = {

            "driver_override":
                self.driver_override.text()
                if self.driver_override.text()
                else None,


            "poll_interval_ms":
                self.poll_interval.value(),


            "script_compatibility_default":
                self.script_compatibility.currentText(),


            "script_batch_size":
                self.script_batch_size.value(),


            "script_timeout_ms":
                self.script_timeout.value(),


            "script_execution_mode":
                self.script_execution_mode.currentText(),


            "process_tick_interval":
                self.process_tick_interval.value()
        }


        if self.bridge:

            self.bridge.update_config(
                config
            )