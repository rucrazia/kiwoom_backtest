import sys

from PyQt5.uic.properties import QtWidgets
from ui.GUI import *
from PyQt5.QtWidgets import *
import main.MainFunctions as mf
import numpy as np
from mpldatacursor import datacursor
from matplotlib.dates import DateFormatter

from main.ui.GUI import Ui_MainWindow


class Main(QtWidgets.QMainWindow):

    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self,parent)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.mainFunctions = mf.MainFunctions()

        self._set_signal_slots()

    def _set_signal_slots(self):
        self.ui.loginBtn.clicked.connect(self.loginBtn_clicked)
        self.ui.flagBtn.clicked.connect(self.flagBtn_clicked)
        self.ui.testingBtn.clicked.connect(self.testingBtn_clicked)
        self.ui.scopeCheck.stateChanged.connect(self.scope_changed)

    def loginBtn_clicked(self):
        pwd = self.ui.pwdEdit.text()
        if pwd == "":
            QMessageBox.about(self, "로그인 실패", "패스워드를 입력하세요")
            self.ui.listWidget.addItem(QListWidgetItem("패스워드를 입력하세요"))
            return
        if self.mainFunctions.db_login(pwd):
            QMessageBox.about(self, "로그인 성공", "로그인 성공")
            self.ui.pwdEdit.setEnabled(False)
            self.ui.loginBtn.setEnabled(False)
            self.ui.flagBtn.setEnabled(True)
            self.ui.listWidget.addItem(QListWidgetItem("로그인 성공"))
        else:
            QMessageBox.about(self, "로그인 실패", "패스워드를 다시 입력하세요")
            self.ui.listWidget.addItem(QListWidgetItem("비밀번호가 틀렸습니다. 다시 입력하세요"))


    def flagBtn_clicked(self):
        code = self.ui.stockEdit.text()
        if code == '':
            QMessageBox.about(self, "실패", "종목 코드를 입력하세요")
            self.listWidget.addItem(QListWidgetItem("종목 코드를 입력하세요"))
            return
        stock_name = self.mainFunctions.is_stock(code)
        if stock_name is None:
            QMessageBox.about(self, "실패", "종목 코드를 다시 입력하세요")
            self.ui.listWidget.addItem(QListWidgetItem("종목 코드를 다시 입력하세요. 코드에 해당하는 종목이 없습니다."))
            self.ui.testingBtn.setEnabled(False)
        else:
            self.ui.flagLabel.setText(stock_name)
            QMessageBox.about(self, "입력 시작", "종목 데이터 전송을 시작하겠습니다.  OK를 눌러주세요")
            self.mainFunctions.db_insert_stock(code)
            data_range = self.mainFunctions.get_stock_date_range(code)
            QMessageBox.about(self, "입력 성공", "종목 데이터를 DB에 저장했습니다.")
            self.ui.listWidget.addItem(QListWidgetItem("종목 데이터 전송 성공. DB에 데이터가 저장되었습니다."))
            self.ui.flagLabel.setText(stock_name+" ( "+data_range[0].strftime("%Y-%m-%d")+" ~ "+data_range[1].strftime("%Y-%m-%d")+" )")
            self.ui.testingBtn.setEnabled(True)

    def scope_changed(self,int):
        if self.ui.scopeCheck.isChecked():
            self.ui.endScopeSpin.setEnabled(True)
            self.ui.stepScopeSpin.setEnabled(True)
        else:
            self.ui.endScopeSpin.setEnabled(False)
            self.ui.stepScopeSpin.setEnabled(False)

    def testingBtn_clicked(self):
        scopes = []
        start_date = self.ui.startDateEdit.date()
        end_date = self.ui.endDateEdit.date()

        if start_date>=end_date:
            QMessageBox.about(self, "실패", "날짜를 잘못 입력했습니다.")
            self.ui.listWidget.addItem(QListWidgetItem("날짜를 다시 입력하세요. 종료일이 시작일보다 커야합니다."))
            return

        if self.ui.scopeCheck.isChecked():
            start_value = self.ui.startScopeSpin.value()
            end_value = self.ui.endScopeSpin.value()
            if start_value>end_value:
                QMessageBox.about(self, "실패", "Scope를 잘못 입력했습니다.")
                self.ui.listWidget.addItem(QListWidgetItem("Scope를 다시 입력하세요. 첫 번째 Scope 값이 두 번째 Scope 값보다 작아야 합니다."))
                return
            elif start_value == end_value:
                scopes.append(start_value)
            else:
                scopes = np.arange(start_value, end_value, self.ui.stepScopeSpin.value())
        else:
            scopes.append(self.ui.startScopeSpin.value())

        slip = self.ui.startSlipSpin.value()

        QMessageBox.about(self, "시작", "BackTesting 시작")
        result = self.mainFunctions.backtesting(self.ui.stockEdit.text(), start_date.toPyDate().strftime("%Y-%m-%d"), end_date.toPyDate().strftime("%Y-%m-%d"), scopes,slip)
        self.show_chart(result)
        QMessageBox.about(self, "성공", "BackTesting 완료")
        self.ui.listWidget.addItem(QListWidgetItem("BackTesting을 완료하였습니다."))

    def show_chart(self, data):
        self.ui.widget.canvas.ax.clear()
        axes = data.plot(ax=self.ui.widget.canvas.ax, grid=True)
        lines = axes.get_lines()
        fmt = DateFormatter('%Y-%m-%d')
        datacursor(lines, formatter=lambda **kwargs: 'Return : {y:.4f}'.format(**kwargs) + '\ndate: ' + fmt(kwargs.get('x')))
        self.ui.widget.canvas.draw()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    myapp = Main()
    myapp.show()
    sys.exit(app.exec_())
