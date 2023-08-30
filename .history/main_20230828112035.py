import sys
from PyQt5.QtWidgets import QApplication
from controllers.feature_selector_controller import FeatureSelectorController

if __name__ == '__main__':
    app = QApplication(sys.argv)
    controller = FeatureSelectorController()
    controller.view.show()
    sys.exit(app.exec_())
