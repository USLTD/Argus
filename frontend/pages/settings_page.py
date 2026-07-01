from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QComboBox,
    QSpinBox,
    QLineEdit,
    QPushButton,
    QLabel
)


class SettingsPage(QWidget):

    def __init__(self, bridge=None):

        super().__init__()

        self.bridge = bridge

        layout = QVBoxLayout(self)

        layout.addWidget(
            QLabel("Argus Configuration")
        )

        form = QFormLayout()


        # driver_override

        self.driver_override = QLineEdit()

        self.driver_override.setPlaceholderText(
            "Auto detect"
        )

        form.addRow(
            "Driver Override",
            self.driver_override
        )


        # poll_interval_ms

        self.poll_interval = QSpinBox()

        self.poll_interval.setRange(
            100,
            60000
        )

        self.poll_interval.setValue(
            1000
        )

        form.addRow(
            "Poll Interval (ms)",
            self.poll_interval
        )


        # script_compatibility_default

        self.script_compatibility = QComboBox()

        self.script_compatibility.addItems(
            [
                "skip",
                "load"
            ]
        )

        form.addRow(
            "Script Compatibility",
            self.script_compatibility
        )


        # script_batch_size

        self.script_batch_size = QSpinBox()

        self.script_batch_size.setRange(
            1,
            100
        )

        self.script_batch_size.setValue(
            4
        )

        form.addRow(
            "Script Batch Size",
            self.script_batch_size
        )


        # script_timeout_ms

        self.script_timeout = QSpinBox()

        self.script_timeout.setRange(
            100,
            60000
        )

        self.script_timeout.setValue(
            5000
        )

        form.addRow(
            "Script Timeout (ms)",
            self.script_timeout
        )


        # script_execution_mode

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

        form.addRow(
            "Execution Mode",
            self.script_execution_mode
        )


        # process_tick_interval

        self.process_tick_interval = QSpinBox()

        self.process_tick_interval.setRange(
            1,
            100
        )

        self.process_tick_interval.setValue(
            5
        )

        form.addRow(
            "Process Tick Interval",
            self.process_tick_interval
        )


        layout.addLayout(form)


        self.save_button = QPushButton(
            "Save Configuration"
        )

        self.save_button.clicked.connect(
            self.save_config
        )

        layout.addWidget(
            self.save_button
        )


        self.load_config()



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