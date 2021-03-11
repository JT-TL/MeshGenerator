from PyQt5.QtWidgets import QWidget, QMessageBox
from PyQt5 import QtGui
from PyQt5 import QtCore
from design import Ui_Form
import sys
import os
import tempfile
from ScriptingUtils.qt_3matic_app import Qt3MaticApp
from TiMeshWorkflow import *
import threaded_trimatic as t
import time


class TiMeshGen(QWidget):
    """docstring for TiMeshGen"""
    def __init__(self):
        super().__init__()
        # self.resource_path = os.path.dirname(sys.argv[0]) + "\\resources\\"
        self.resource_path = os.getcwd() + "\\resources\\"
        self.temp_save_path = tempfile.gettempdir()
        print("Resources Path: " + self.resource_path)

        self.ui = Ui_Form()
        self.ui.resource_path = self.resource_path
        self.ui.setupUi(self)

        self.ui.go_to_execute_workflow_page.clicked.connect(self.go_to_execute_workflow)
        self.display_message("")
        self.ui.go_to_next_step.clicked.connect(self.proceed_to_next_step)
        self.ui.go_to_previous_step.clicked.connect(self.proceed_to_previous_step)
        self.ui.exit.clicked.connect(self.finish_workflow)

        self.n_steps = 0
        self.cur_step = -1
        self.step_function = None
        self.steps = []
        self.job_done = True
        self.timer = None
        self.guide_images = []

    def display_message(self, messages):
        combined_msg = ""
        for msg in messages:
            combined_msg = combined_msg + msg + "\n"
            self.ui.information_text.setText(combined_msg)

    def go_to_execute_workflow(self):
        print("go_to_execute_workflow executed")
        if len(self.ui.patient_id_edit.text()) == 0:
            QMessageBox.information(self, self.windowTitle(), "Patient ID must not be empty!", QMessageBox.Ok)
        else:
            self.ui.stackedWidget.setCurrentIndex(1)
            self.TiMeshWorkflow()

    def finish_workflow(self):
        self.close()

    def execute_step(self, step_index, forward):
        if step_index not in range(0, self.n_steps):
            print("error happende here")
            raise IndexError
        keys = list(self.steps.keys())
        self.job_done = False
        self.cur_step = step_index
        print("Execute step: %d" % self.cur_step)
        key = keys[self.cur_step]
        if forward:
            self.step_function = self.steps[key][1]
        else:
            self.step_function = None
        self.update_ui()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.on_tick)
        self.timer.setSingleShot(True)
        self.timer.start(100)

    def proceed_to_next_step(self):
        self.execute_step(self.cur_step + 1, True)

    def proceed_to_previous_step(self):
        self.execute_step(self.cur_step - 1, False)

    def on_tick(self):
        if self.step_function:
            try:
                self.step_function(self)
                self.step_function = None
                if self.cur_step == self.n_steps - 1:
                    message = "Titanium scaffold for patient ID :{} is created.".format(self.ui.patient_id_edit.text())
                    QMessageBox.information(self, self.windowTitle(), message, QMessageBox.Ok)
            except Exception as e:
                print("Error:{}".format(e))
                self.crashHandler(e)
                return
        self.job_done = True
        self.update_ui()
        
    def crashHandler(self, error_message):
        # update ui
        self.ui.stackedWidget.setCurrentIndex(2)
        self.ui.Error_information.setText(str(error_message))
        self.ui.exit.setEnabled(True)
        self.ui.crash_image_display.setPixmap(QtGui.QPixmap(self.resource_path + "computer_stare.jpg"))
        self.ui.step_check_lable_2.setPixmap(QtGui.QPixmap(self.resource_path + "error.png"))

    def TiMeshWorkflow(self):
        print("TiMeshWorkflow executed")
        self.job_done = False
        self.n_steps = len(ti_mesh_steps) # 5
        self.guide_images = ti_mesh_step_guid_images
        self.steps = ti_mesh_steps
        self.update_ui()
        self.execute_step(0, True)

    def update_ui(self):
        # print("update_ui executed")
        keys = list(self.steps.keys())  # length=5
        index = self.cur_step if self.cur_step in range(self.n_steps) else 0
        key = keys[index]
        self.ui.go_to_previous_step.setEnabled(self.cur_step > 0 and self.job_done)
        self.ui.go_to_next_step.setEnabled(self.cur_step < self.n_steps - 1 and self.job_done)
        self.ui.information_text.setText(self.steps[key][0])
        self.ui.step_description.setText(self.steps[key][2])
        self.ui.total_steps_text.setText(str(self.n_steps))

        if self.job_done:
            self.ui.step_check_lable.setPixmap(QtGui.QPixmap(self.resource_path + "ic_done.png"))
        else:
            self.ui.step_check_lable.setPixmap(QtGui.QPixmap(self.resource_path + "ic_not_done.png"))

        try:
            print("\n")
            self.ui.step_indicator_text.setText(str(self.cur_step + 1))
            self.ui.guide_image_display.setPixmap(QtGui.QPixmap(self.resource_path + self.guide_images[index]))
            print("  ")
        except Exception as e:
            print(e)


if __name__ == '__main__':
    a = Qt3MaticApp(TiMeshGen)
    a.run()




        