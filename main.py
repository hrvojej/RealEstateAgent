
from PyQt5 import QtCore, QtWidgets, QtGui
try:
    # Include in try/except block if you're also targeting Mac/Linux
    from PyQt5.QtWinExtras import QtWin
    myappid = 'Jona.NjuskaloPostar.WebApp.001'
    QtWin.setCurrentProcessExplicitAppUserModelID(myappid)
except ImportError:
    pass
from PyQt5.QtGui import QPixmap, QDesktopServices, QIcon
from PyQt5.QtCore import QUrl, QObject, pyqtSignal, QRunnable, pyqtSlot, QTimer, QThreadPool, QSize
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QMessageBox, QVBoxLayout, QWidget, QHBoxLayout, QLabel, QLineEdit, QPushButton, \
    QProgressBar, QApplication, QDialog, QToolBar, QAction
import getPandas
from getURLPage import GetPage
from sendEmail import SendToGmail
import pandas as pd
import traceback, sys
from secondsConversion import display_time
from datetime import datetime, timedelta
import time
import webbrowser
import re # DON'T DELETE THIS
import resources
pd.options.mode.chained_assignment = None  # default='warn'


class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)

class Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.kwargs['progress_callback'] = self.signals.progress

    @pyqtSlot()
    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, obj=None, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.worker = None
        self.stop_ruleVar = 0

        self.centralwidget = QtWidgets.QWidget(self)
        self.label = QtWidgets.QLabel()
        self.lineEdit = QtWidgets.QLineEdit("https://www.njuskalo.hr/prodaja-stanova/zagreb")
        self.siteURL = self.lineEdit.text()
        print(self.siteURL)
        self.go = QtWidgets.QPushButton()
        self.go.clicked.connect(self.gourl)
        self.lineEdit.returnPressed.connect(self.gourl)
        self.tabWidget = QtWidgets.QTabWidget()

        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.lineEdit, 0, 1, 1, 1)
        self.gridLayout.addWidget(self.go, 0, 2, 1, 1)
        self.gridLayout.addWidget(self.tabWidget, 1, 0, 1, 3)

        # Tabs
        self.tabWidget.setEnabled(True)

        #Web tab
        self.webview = Browser()
        self.tabWidget.addTab(self.webview, "")

        #Datatab
        self.centralwidgetDT = QtWidgets.QWidget(self)

        self.lineEditDT = QtWidgets.QLineEdit(self.centralwidgetDT)
        self.pdtable = QtWidgets.QTableView(self.centralwidgetDT)
        self.comboBoxDT = QtWidgets.QComboBox(self.centralwidgetDT)
        self.labelDT = QtWidgets.QLabel(self.centralwidgetDT)

        self.gridLayoutDT = QtWidgets.QGridLayout(self.centralwidgetDT)
        self.gridLayoutDT.addWidget(self.labelDT, 0, 0, 1, 1)
        self.gridLayoutDT.addWidget(self.lineEditDT, 0, 1, 1, 1)
        self.gridLayoutDT.addWidget(self.comboBoxDT, 0, 2, 1, 1)
        self.gridLayoutDT.addWidget(self.pdtable, 1, 0, 1, 3)
        self.tabWidget.addTab(self.centralwidgetDT, "")

        self.pdtable.horizontalHeader().setCascadingSectionResizes(True)
        self.pdtable.horizontalHeader().setStretchLastSection(True)

        # Pandas model
        self.model = getPandas.PandasTableModel(pd.DataFrame())
        self.go.clicked.connect(self.getPageInfo)
        self.lineEdit.returnPressed.connect(self.getPageInfo)

        #Proxy model for filter
        self.proxy = QtCore.QSortFilterProxyModel(self)

        self.lineEditDT.textChanged.connect(self.on_lineEdit_textChanged)
        self.comboBoxDT.currentIndexChanged.connect(self.on_comboBox_currentIndexChanged)

        self.horizontalHeader = self.pdtable.horizontalHeader()
        self.horizontalHeader.sectionClicked.connect(self.on_view_horizontalHeader_sectionClicked)

######## NOTIFICATION TAB

        self.notifwidget = QtWidgets.QWidget(self)
        self.gridLayout_2 = QtWidgets.QGridLayout(self.notifwidget)
        self.gridLayout_2.columnStretch(0)

        ### TEXT LINES

        #  0 line - First Label
        self.label0NT = QtWidgets.QLabel(self.notifwidget)
        self.gridLayout_2.addWidget(self.label0NT, 0, 0, 1, 2)
        self.label0NT.setText("Obavijesti me kada se pojavi oglas koji zadovoljava uvijete:")
        self.label0NT.setFixedHeight(20)

        # 1,0 - combobox
        self.comboBoxNT = QtWidgets.QComboBox(self.notifwidget)
        self.comboBoxNT.setObjectName("comboBoxNT")
        self.gridLayout_2.addWidget(self.comboBoxNT, 1, 0, 1, 2)

        # 1,2 - label
        self.label1NT = QtWidgets.QLabel(self.notifwidget)
        self.gridLayout_2.addWidget(self.label1NT, 1, 2, 1, 1)

        # 1,3 - lineEdit
        self.lineEditNT = QtWidgets.QLineEdit(self.notifwidget)
        self.lineEditNT.setAlignment(QtCore.Qt.AlignLeft)
        self.gridLayout_2.addWidget(self.lineEditNT, 1, 3, 1, 2)


        # 2,0 - combobox
        self.comboBoxNT_2 = QtWidgets.QComboBox(self.notifwidget)
        self.comboBoxNT_2.setObjectName("comboBoxNT_2")
        self.gridLayout_2.addWidget(self.comboBoxNT_2, 2, 0, 1, 2)

        #2,2 - label
        self.label1NT_2 = QtWidgets.QLabel(self.notifwidget)
        self.gridLayout_2.addWidget(self.label1NT_2, 2, 2, 1, 1)

        # 2,3 - lineEdit
        self.lineEditNT_2 = QtWidgets.QLineEdit(self.notifwidget)
        self.gridLayout_2.addWidget(self.lineEditNT_2, 2, 3, 1, 2)

        # 3,0 - combobox
        self.comboBoxNT_3 = QtWidgets.QComboBox(self.notifwidget)
        self.comboBoxNT_3.setObjectName("comboBoxNT_3")
        self.gridLayout_2.addWidget(self.comboBoxNT_3, 3, 0, 1, 2)

        # 3,2 - label
        self.label1NT_3 = QtWidgets.QLabel(self.notifwidget)
        self.gridLayout_2.addWidget(self.label1NT_3, 3, 2, 1, 1)

        # 3,3 - lineEdit
        self.lineEditNT_3 = QtWidgets.QLineEdit(self.notifwidget)
        self.gridLayout_2.addWidget(self.lineEditNT_3, 3, 3, 1, 2)

        ### INTEGER LINES
        # 4,0  - combobox
        self.comboBoxNT_4 = QtWidgets.QComboBox(self.notifwidget)
        self.comboBoxNT_4.setObjectName("comboBoxNT_4")
        self.gridLayout_2.addWidget(self.comboBoxNT_4, 4, 0, 1, 2)

        # 4,2 - label
        self.label1NT_4 = QtWidgets.QLabel(self.notifwidget)
        self.gridLayout_2.addWidget(self.label1NT_4, 4, 2, 1, 1)

        # 4,3 - lineEdit (int)
        self.lineEditNT_4 = QtWidgets.QLineEdit(self.notifwidget)
        self.gridLayout_2.addWidget(self.lineEditNT_4, 4, 3, 1, 1)

        # 4,4 - label
        self.label1NT_5 = QtWidgets.QLabel(self.notifwidget)
        self.label1NT_5.setAlignment(QtCore.Qt.AlignCenter)
        self.gridLayout_2.addWidget(self.label1NT_5, 4, 4, 1, 1)

        # 4,5 - lineEdit (int)
        self.lineEditNT_5 = QtWidgets.QLineEdit(self.notifwidget)
        self.gridLayout_2.addWidget(self.lineEditNT_5, 4, 5, 1, 1)

        # 5,0  - combobox
        self.comboBoxNT_5 = QtWidgets.QComboBox(self.notifwidget)
        self.gridLayout_2.addWidget(self.comboBoxNT_5, 5, 0, 1, 2)

        # 5,2 - label
        self.label1NT_6 = QtWidgets.QLabel(self.notifwidget)
        self.gridLayout_2.addWidget(self.label1NT_6, 5, 2, 1, 1)

        # 5,3 - lineEdit (int)
        self.lineEditNT_7 = QtWidgets.QLineEdit(self.notifwidget)
        self.gridLayout_2.addWidget(self.lineEditNT_7, 5, 3, 1, 1)

        # 5,4 - label
        self.label1NT_7 = QtWidgets.QLabel(self.notifwidget)
        self.label1NT_7.setAlignment(QtCore.Qt.AlignCenter)
        self.gridLayout_2.addWidget(self.label1NT_7, 5, 4, 1, 1)

        # 5,5 - lineEdit (int)
        self.lineEditNT_6 = QtWidgets.QLineEdit(self.notifwidget)
        self.gridLayout_2.addWidget(self.lineEditNT_6, 5, 5, 1, 1)

        # 6,0  - combobox
        self.comboBoxNT_6 = QtWidgets.QComboBox(self.notifwidget)
        self.gridLayout_2.addWidget(self.comboBoxNT_6, 6, 0, 1, 2)

        # 6,2 - label
        self.label1NT_8 = QtWidgets.QLabel(self.notifwidget)
        self.gridLayout_2.addWidget(self.label1NT_8, 6, 2, 1, 1)

        # 6,3 - line edit (int)
        self.lineEditNT_9 = QtWidgets.QLineEdit(self.notifwidget)
        self.gridLayout_2.addWidget(self.lineEditNT_9, 6, 3, 1, 1)

        # 6,4 - label
        self.label1NT_9 = QtWidgets.QLabel(self.notifwidget)
        self.label1NT_9.setAlignment(QtCore.Qt.AlignCenter)
        self.gridLayout_2.addWidget(self.label1NT_9, 6, 4, 1, 1)

        # 6,5  - line edit (int)
        self.lineEditNT_8 = QtWidgets.QLineEdit(self.notifwidget)
        self.gridLayout_2.addWidget(self.lineEditNT_8, 6, 5, 1, 1)

        ## DATETIME LINE
        # 7,0 - combobox
        self.comboBoxNT_8 = QtWidgets.QComboBox()
        # self.gridLayout_2.addWidget(self.comboBoxNT_8, 7, 0, 1, 2)
        #
        # # 7,2 - label
        # self.label1NT_19 = QtWidgets.QLabel(self.notifwidget)
        # self.gridLayout_2.addWidget(self.label1NT_19, 7, 2, 1, 1)
        #
        # # 7,3 - datetime from
        # self.dateTimeEditNT = QtWidgets.QDateTimeEdit(self.notifwidget)
        # self.dateTimeEditNT.setDateTime(QtCore.QDateTime.currentDateTime().addSecs(-(self.frequency)))
        # self.gridLayout_2.addWidget(self.dateTimeEditNT, 7, 3, 1, 1)
        #
        # # 7,4 - label
        # self.label1NT_20 = QtWidgets.QLabel(self.notifwidget)
        # self.label1NT_20.setAlignment(QtCore.Qt.AlignCenter)
        # self.gridLayout_2.addWidget(self.label1NT_20, 7, 4, 1, 1)
        #
        # # 7,5 - datetime end
        # self.dateTimeEditNT_2 = QtWidgets.QDateTimeEdit(self.notifwidget)
        # self.dateTimeEditNT_2.setDateTime(QtCore.QDateTime.currentDateTime())
        # self.gridLayout_2.addWidget(self.dateTimeEditNT_2, 7, 5, 1, 1)

        # 8,0 - label
        self.label1NT_22 = QtWidgets.QLabel(self.notifwidget)
        self.label1NT_22.setObjectName("label1NT_22")
        self.gridLayout_2.addWidget(self.label1NT_22, 8, 0, 1, 2)
        self.label1NT_22.setText("Dohvati nove oglase svakih: ")

        # 8,2 - combobox - minutes list
        self.comboBoxNT_MIN = QtWidgets.QComboBox(self.notifwidget)
        comboBoxNT_MIN_list = [str(x) for x in range(5, 125, 5)]
        self.comboBoxNT_MIN.clear()
        self.comboBoxNT_MIN.addItems(comboBoxNT_MIN_list)
        self.gridLayout_2.addWidget(self.comboBoxNT_MIN, 8, 2, 1, 1)

        # 8,3 - label
        self.label1NT_27 = QtWidgets.QLabel(self.notifwidget)
        self.label1NT_27.setObjectName("label1NT_27")
        self.gridLayout_2.addWidget(self.label1NT_27, 8, 3, 1, 1)

        #### sati
        # 9,0 - label
        self.label1NT_23 = QtWidgets.QLabel(self.notifwidget)
        self.gridLayout_2.addWidget(self.label1NT_23, 9, 0, 1, 2)
        self.label1NT_23.setText("Neka se ovo pravilo izvršava idućih:")

        # 9,2 - combobox - sati
        self.comboBoxNT_HOUR = QtWidgets.QComboBox(self.notifwidget)
        comboBoxNT_HOUR_list = [str(x) for x in range(2,125,2)]
        self.comboBoxNT_HOUR.clear()
        self.comboBoxNT_HOUR.addItems(comboBoxNT_HOUR_list)
        self.gridLayout_2.addWidget(self.comboBoxNT_HOUR, 9, 2, 1, 1)

        # 9,3 - label
        self.label1NT_28 = QtWidgets.QLabel(self.notifwidget)
        self.label1NT_28.setObjectName("label1NT_28")
        self.gridLayout_2.addWidget(self.label1NT_28, 9, 3, 1, 1)

        # EMAIL
        # 10,0 - label
        self.label1NT_26 = QtWidgets.QLabel(self.notifwidget)
        self.gridLayout_2.addWidget(self.label1NT_26, 10, 0, 1, 2)
        self.label1NT_26.setText("Obavijesti me na ovu E-mail adresu:")

        # 10,2 - Email adresa input
        self.lineEditNT_Email = QtWidgets.QLineEdit(self.notifwidget)
        self.gridLayout_2.addWidget(self.lineEditNT_Email, 10, 2, 1, 1)

        # 10,3 - Lozinka label
        self.userEmailPsswdLabel = QtWidgets.QLabel(self.notifwidget)
        self.userEmailPsswdLabel.setText("Lozinka za email adresu:")
        self.userEmailPsswdLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        # self.userEmailPsswdLabel.setMinimumWidth(400)
        self.gridLayout_2.addWidget(self.userEmailPsswdLabel, 10, 3, 1, 1)

        #10,4 - Lozinka input
        self.lineEditNT_EmailPsswd = QtWidgets.QLineEdit(self.notifwidget)
        self.lineEditNT_EmailPsswd.setEchoMode(QLineEdit.Password)
        self.lineEditNT_EmailPsswd.setMinimumWidth(200)
        self.gridLayout_2.addWidget(self.lineEditNT_EmailPsswd, 10, 4, 1, 2)
        # loading image
        self.userEmailWarningLB = QtWidgets.QLabel(self.notifwidget)

        # 10,5 Image warning
        self.emailWarningIMG = QPixmap(':/icons/emailWarning.ico')
        self.userEmailWarningLB.setPixmap(self.emailWarningIMG)
        # Optional, resize label to image size
        self.userEmailWarningLB.resize(self.emailWarningIMG.width(),
                          self.emailWarningIMG.height())

        # warning image info on hover
        self.userEmailWarningLB.move(0, 0)
        self.userEmailWarningLB.setStyleSheet("border :3px solid black;")
        self.userEmailWarningLB.setToolTip("Mora biti omogućen pristup za Manje sigurne aplikacije (Less secure apps opcija na vašem Google računu), molimo vas kliknite na <b>\"Upute\"</b> na meniju kako biste saznali zašto ili kliknite na <b>\"Omogući manje sigurne aplikacije\"</b> na meniju i odmah uključite tu opciju ako ne želite čitati upute.")
        self.userEmailWarningLB.setToolTipDuration(10000000)
        self.gridLayout_2.addWidget(self.userEmailWarningLB, 10, 6, 1, 1)


        # 11 INFO
        boldLabel = QtGui.QFont()
        boldLabel.setBold(True)
        self.label.setFont(boldLabel)
        # 11,0 - label

        self.ruleTimes = QtWidgets.QLabel(self.notifwidget)
        self.ruleTimes.setText("")
        self.ruleTimes.setFont(boldLabel)
        self.gridLayout_2.addWidget(self.ruleTimes, 11, 2, 1, 4)
        self.ruleTimes.setFixedHeight(20)
        self.ruleTimes.setMinimumWidth(400)

        # 12 PRAVILO
        # 12,0 - label
        self.start = QtWidgets.QLabel(self.notifwidget)
        self.start.setText("Pravilo nije pokrenuto.")
        self.start.setFont(boldLabel)
        self.gridLayout_2.addWidget(self.start, 12, 2, 1, 2)
        self.start.setFixedHeight(20)
        self.start.setMinimumWidth(400)


        # 12,1 - label
        self.countToNext = QtWidgets.QLabel(self.notifwidget)
        self.countToNext.setText("Brojač.")
        self.countToNext.setFont(boldLabel)
        self.gridLayout_2.addWidget(self.countToNext, 12, 3, 1, 2)
        self.countToNext.setFixedHeight(20)


        # 13 - BUTTONS (POKRENI - ZAUSTAVI)
        self.testEmailBT = QPushButton("Pošalji test mail")
        self.testEmailBT.pressed.connect(self.testEmail)
        self.gridLayout_2.addWidget(self.testEmailBT, 13, 2, 1, 1)
        self.startRule = QPushButton("Pokreni")
        self.gridLayout_2.addWidget(self.startRule,13,3,1,1)
        self.endRule = QPushButton("Zaustavi")
        self.gridLayout_2.addWidget(self.endRule,13,4,1,1)

        self.tabWidget.addTab(self.notifwidget, "Obaviještavanje")
        self.setCentralWidget(self.centralwidget)

        # Create a statusbar.
        self.status = self.statusBar()
        self.progress = QProgressBar()
        self.status.addPermanentWidget(self.progress)

        # Menu
        toolbar = QToolBar("Glavni Toolbar")
        toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(toolbar)

        # UPUTE
        uputeAction = QAction("Upute", self)
        uputeAction.triggered.connect(self.openUrl)
        uputeAction.setCheckable(True)
        toolbar.addAction(uputeAction)

        dopustiManjeSigurne = QAction("Omogući manje sigurne aplikacije", self)
        dopustiManjeSigurne.triggered.connect(self.openUrlManjeSigurne)
        dopustiManjeSigurne.setCheckable(True)
        toolbar.addAction(dopustiManjeSigurne)

        # O aplikaciji
        aboutAction = QAction("O aplikaciji", self)
        aboutAction.triggered.connect(self.aboutapp)
        aboutAction.setCheckable(True)
        toolbar.addAction(aboutAction)

        # Thread and timer
        self.threadpool = QThreadPool()
        self.startRule.pressed.connect(self.start_rule)
        self.endRule.pressed.connect(self.stop_rule)
        self.timer = QTimer()
        self.timer.setInterval(1000)

        self.retranslateUi()
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(self)

    def aboutapp(self):
        QMessageBox.about(self, "Njuškalo Poštar info", "Aplikacija za dohvat, analizu i obaviještavanje na temelju"
                                                        " podataka sa njuškalo.hr stranice. <br>"
                                                        "Trebate više informacije, želite izraditi sličnu aplikaciju, želite licencirati enterprise verziju aplikacije ili imate neki drugi upit - obratite se na hrvojej@gmail.com"
                            )
        return

    def openUrl(self, url):
        QDesktopServices.openUrl(QUrl("https://njuskalo-postar-dokumentacija.readthedocs.io/hr/latest/contents.html"))

    def openUrlManjeSigurne(self):
        QDesktopServices.openUrl(QUrl("https://njuskalo-postar-dokumentacija.readthedocs.io/hr/latest/contents.html#kako-dopustiti-manje-sigurnim-aplikacijama-da-mi-salju-email"))

    def testEmail(self):
        sendtoEmail = self.lineEditNT_Email.text()
        emailPsswd = self.lineEditNT_EmailPsswd.text()
        if not sendtoEmail or not emailPsswd:
            QMessageBox.about(self, "Email polje ili lozinka je prazno!", "Niste unijeli email adresu i/ili lozinku.")
            return
        SendToGmail(destination=sendtoEmail, df=self.pageDF[0:10], serverLogin=sendtoEmail,
                    serverPss=emailPsswd)
        QMessageBox.about(self, "Mail poslan!", "Poslano je prvih 10 stanova iz <br> \"Podaci iz web stranice\". Provjerite email koji ste unijeli.")
        self.testEmailBT.setText("Test mail poslan")
        return


    def convert(self,seconds):
        seconds = seconds % (24 * 3600)
        days = seconds // (24 * 3600)
        hour = seconds // 3600
        seconds %= 3600
        minutes = seconds // 60
        seconds %= 60
        return "%d:%d:%02d:%02d" % (days, hour, minutes, seconds)

    def progress_fn(self, n):
        self.progress.setValue(n)
        if self.stop_ruleVar == 0:
            self.start.setText("Izvršeno " + str(n) + "%")

    def start_rule(self):
        worker = Worker(self.execute_rule)  # Any other args, kwargs are passed to the run function
        worker.signals.progress.connect(self.progress_fn)
        self.threadpool.start(worker)

    def execute_rule(self, progress_callback):
        sendtoEmail = self.lineEditNT_Email.text()
        emailPsswd = self.lineEditNT_EmailPsswd.text()
        if not sendtoEmail or not emailPsswd:
            QMessageBox.about(self, "Email polje ili lozinka je prazno!", "Niste unijeli email adresu i/ili lozinku.")
            self.timer.stop()
            return
        self.timer.start()
        self.startRule.setEnabled(False)
        self.start.setText("Pravilo pokrenuto.")
        self.counter = int(self.comboBoxNT_HOUR.currentText()) * 3600
        self.frequency = int(self.comboBoxNT_MIN.currentText()) * 60
        freq = self.frequency
        counter = self.counter
        self.ruleTimes.setText("Izvršavam pravilo još -  " +str(display_time(counter, 4)))
        for n in range(1, counter+1):
            if self.stop_ruleVar == 1:
                self.timer.stop()
                progress_callback.emit(0)
                self.startRule.setEnabled(True)
                self.stop_ruleVar = 0
                return
            if freq == 1:
                freq = self.frequency
            else:
                freq -= 1
            counter -= 1
            time.sleep(1)
            if n % self.frequency == 0 and  self.stop_ruleVar != 1:
                self.countToNext.setText("Dohvaćam nove podatke i šaljem obavijest.")
                self.getInfoFromForm()

                if not self.filteredpageDF.empty:
                    SendToGmail(destination=sendtoEmail, df=self.filteredpageDF, serverLogin=sendtoEmail,
                             serverPss=emailPsswd)
                prog_prct = (n / self.counter)*100
                progress_callback.emit(prog_prct)
            if self.stop_ruleVar != 1:
                self.countToNext.setText("Dohvaćam nove podatke za " + str(self.convert(int(freq))))
            if counter == 0:
                self.start.setText("Zadatak izvršen.")
                self.countToNext.setText("")
                progress_callback.emit(100)
                self.timer.stop()
                self.startRule.setEnabled(True)
        return

    def stop_rule(self):
        self.start.setText("Zadatak zaustavljen.")
        self.ruleTimes.setText("")
        self.countToNext.setText("")
        self.stop_ruleVar = 1

    def shutdown(self):
        if self.worker:  # set self.worker=None in your __init__ so it's always defined.
            self.worker.kill()
        self.stop_ruleVar = 1

#########################################

    def gourl(self):
        self.siteURL = self.lineEdit.text()
        self.webview.load(QUrl(self.siteURL))

    def getPageInfo(self):
        self.siteURL = self.lineEdit.text()
        getPage = GetPage(self.siteURL,
                          "data",
                          "page")
        self.pageDF = getPage.getAdInfo()
        if self.pageDF.empty:
            msg = QMessageBox()
            msg.setWindowTitle("Greška!")
            msg.setText("Unosite isključivo stranice koje na početku imaju https://www.njuskalo.hr/prodaja-stanova/ i koje postoje na njuskalo.hr")
            msg.setIcon(QMessageBox.Critical)
            msg.exec_()

        # print(self.pageDF.columns)
        self.model = getPandas.PandasTableModel(self.pageDF)
        self.pdtable.setModel(self.model)
        self.pdtable.doubleClicked.connect(self.OpenLink)

        self.proxy.setSourceModel(self.model)
        self.pdtable.setModel(self.proxy)
        self.comboBoxDT.clear()
        self.comboBoxDT.addItems(self.pageDF.columns)

        # Combo TEXT boxes
        comboBoxNT_listText = ['Naslov', 'Tip', 'Lokacija', 'ID', 'URL', 'TipOglasa']
        self.comboBoxNT.clear()
        self.comboBoxNT.addItems(comboBoxNT_listText)
        self.comboBoxNT.setCurrentText(comboBoxNT_listText[0])
        self.comboBoxNT_2.clear()
        self.comboBoxNT_2.addItems(comboBoxNT_listText)
        self.comboBoxNT_2.setCurrentText(comboBoxNT_listText[1])
        self.comboBoxNT_3.clear()
        self.comboBoxNT_3.addItems(comboBoxNT_listText)
        self.comboBoxNT_3.setCurrentText(comboBoxNT_listText[2])

        # Combo NUM boxes
        comboBoxNT_listNums = ['Kvadratura', 'CijenaKN', 'CijenaEUR']
        self.comboBoxNT_4.clear()
        self.comboBoxNT_4.addItems(comboBoxNT_listNums)
        self.comboBoxNT_4.setCurrentText(comboBoxNT_listNums[0])
        self.comboBoxNT_5.clear()
        self.comboBoxNT_5.addItems(comboBoxNT_listNums)
        self.comboBoxNT_5.setCurrentText(comboBoxNT_listNums[1])
        self.comboBoxNT_6.clear()
        self.comboBoxNT_6.addItems(comboBoxNT_listNums)
        self.comboBoxNT_6.setCurrentText(comboBoxNT_listNums[2])

        # DATETIME Boxes
        self.comboBoxNT_8.clear()
        self.comboBoxNT_8.addItems(['VrijemeObjave'])
        self.comboBoxNT_8.setCurrentText('VrijemeObjave')

    def mk_int_0(self,s):
        s = s.strip()
        return int(s) if s else 0

    def mk_int_max(self,s):
        s = s.strip()
        return int(s) if s else 1073741824

    def getInfoFromForm(self):
        userQuery = []
        # Combobox - text lines
        userFormQuery = {}
        ## Pandas dataframe filtering dictionary
        datetimeFormat = '%d.%m.%Y %H:%M:%S'
        self.startTime = (datetime.now() - timedelta(seconds=int(self.comboBoxNT_MIN.currentText()) * 60)).strftime(datetimeFormat)
        self.endTime = datetime.now().strftime(datetimeFormat)
        # Text values
        userFormQuery[self.comboBoxNT.currentText()] = self.lineEditNT.text()
        userFormQuery[self.comboBoxNT_2.currentText()] = self.lineEditNT_2.text()
        userFormQuery[self.comboBoxNT_3.currentText()] = self.lineEditNT_3.text()
        # Int values
        userFormQuery[self.comboBoxNT_4.currentText()] = [self.mk_int_0(self.lineEditNT_4.text()),self.mk_int_max(self.lineEditNT_5.text())]
        userFormQuery[self.comboBoxNT_5.currentText()] = [self.mk_int_0(self.lineEditNT_7.text()),self.mk_int_max(self.lineEditNT_6.text())]
        userFormQuery[self.comboBoxNT_6.currentText()] = [self.mk_int_0(self.lineEditNT_9.text()),self.mk_int_max(self.lineEditNT_8.text())]
        # DateTime values
        userFormQuery[self.comboBoxNT_8.currentText()] = [self.startTime, self.endTime]
        self.filteredpageDF = pd.DataFrame()
        self.filteredpageDF = self.pageDF

        for key, value in list(userFormQuery.items()):
            if 'str' in str(type(value)):
                if not value: del userFormQuery[key]

        commands = []
        for key, value in userFormQuery.items():
            if 'list' in str(type(value)):
                if 'int' in str(type(value[0])):
                    command = "self.pageDF[\"{}\"] > {}) & (self.pageDF[\"{}\"] < {}".format(key,value[0],key,value[1])
                    commands.append((command))
                else : # This part takes care of datetime comparison - list contains 2 datetime strings
                    command = "self.pageDF[\"{}\"] > \"{}\") & (self.pageDF[\"{}\"] < \"{}\"".format(key, value[0], key,
                                                                                             value[1])
                    commands.append((command))
            if 'str' in str(type(value)):
                command = "self.pageDF[\"{}\"].str.contains(\"{}\", flags=re.IGNORECASE)".format(key, value)
                commands.append((command))

        commandFinal = ''
        for command in commands:
            commandFinal = commandFinal + ("({}) & ".format(command))

        commandFinal ="self.pageDF["+commandFinal[:-3]+"]"

        self.filteredpageDF = eval(commandFinal)
        # Cast datetime to str in desired format for showing on front end
        # self.pageDF['VrijemeObjave'] = pd.to_datetime(self.pageDF['VrijemeObjave'], format='%d.%m.%Y %H:%M:%S').dt.strftime('%d.%m.%Y %H:%M:%S')
        # print(self.filteredpageDF.shape)
        # if not self.filteredpageDF.empty:
        #     self.filteredpageDF['VrijemeObjave'] = pd.to_datetime(self.filteredpageDF['VrijemeObjave'],
        #                                                   format='%d.%m.%Y %H:%M:%S').dt.strftime('%d.%m.%Y %H:%M:%S')
    def OpenLink(self, item):
        for index in self.pdtable.selectionModel().selectedIndexes():
            value = str(self.pageDF.iloc[index.row()][index.column()])
            if value.startswith("http://") or value.startswith("https://"):
                webbrowser.open(value)

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("main", "Njuškalo Poštar"))
        self.label.setText(_translate("main", "Unesite URL:"))
        self.go.setText(_translate("main", "Kreni"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.webview), _translate("main", "Web stranica"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.centralwidgetDT),
                                  _translate("main", "Podaci iz web stranice"))
        self.labelDT.setText(_translate("main", " Pretraga: "))
        self.comboBoxDT.setPlaceholderText(_translate("main", "Odaberite"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.notifwidget), _translate("main", "Obaviještavanje"))
        self.label1NT_4.setText(_translate("main", "između:"))
        self.label1NT_28.setText(_translate("main", "sati"))
        self.label1NT_8.setText(_translate("main", "između:"))
        self.label1NT_27.setText(_translate("main", "minuta"))
        self.label1NT_5.setText(_translate("main", "i"))
        self.label1NT_7.setText(_translate("main", "i"))
        self.label1NT.setText(_translate("main", "sadrži tekst:"))
        self.label1NT_9.setText(_translate("main", "i"))
        self.label1NT_6.setText(_translate("main", "između:"))
        self.label1NT_3.setText(_translate("main", "sadrži tekst:"))
        self.label1NT_2.setText(_translate("main", "sadrži tekst:"))


    @QtCore.pyqtSlot(int)
    def on_view_horizontalHeader_sectionClicked(self, logicalIndex):
        self.logicalIndex   = logicalIndex
        self.menuValues     = QtWidgets.QMenu(self)
        self.signalMapper   = QtCore.QSignalMapper(self)

        self.comboBoxDT.blockSignals(True)
        self.comboBoxDT.setCurrentIndex(self.logicalIndex)
        self.comboBoxDT.blockSignals(True)

        valuesUnique = [self.model.item(row, self.logicalIndex).text()
                            for row in range(self.model.rowCount())
                            ]

        actionAll = QtWidgets.QAction("All", self)
        actionAll.triggered.connect(self.on_actionAll_triggered)
        self.menuValues.addAction(actionAll)
        self.menuValues.addSeparator()

        for actionNumber, actionName in enumerate(sorted(list(set(valuesUnique)))):
            action = QtWidgets.QAction(actionName, self)
            self.signalMapper.setMapping(action, actionNumber)
            action.triggered.connect(self.signalMapper.map)
            self.menuValues.addAction(action)

        self.signalMapper.mapped.connect(self.on_signalMapper_mapped)

        headerPos = self.pdtable.mapToGlobal(self.horizontalHeader.pos())

        posY = headerPos.y() + self.horizontalHeader.height()
        posX = headerPos.x() + self.horizontalHeader.sectionViewportPosition(self.logicalIndex)

        self.menuValues.exec_(QtCore.QPoint(posX, posY))

    @QtCore.pyqtSlot()
    def on_actionAll_triggered(self):
        filterColumn = self.logicalIndex
        filterString = QtCore.QRegExp( "",
                                       QtCore.Qt.CaseSensitive,
                                       QtCore.QRegExp.RegExp
                                        )
        self.proxy.setFilterRegExp(filterString)
        self.proxy.setFilterKeyColumn(filterColumn)

    @QtCore.pyqtSlot(int)
    def on_signalMapper_mapped(self, i):
        stringAction = self.signalMapper.mapping(i).text()
        filterColumn = self.logicalIndex
        filterString = QtCore.QRegExp(  stringAction,
                                        QtCore.Qt.CaseInsensitive,
                                        QtCore.QRegExp.FixedString
                                        )
        self.proxy.setFilterRegExp(filterString)
        self.proxy.setFilterKeyColumn(filterColumn)

    @QtCore.pyqtSlot(str)
    def on_lineEdit_textChanged(self, text):
        search = QtCore.QRegExp(    text,
                                    QtCore.Qt.CaseInsensitive,
                                    QtCore.QRegExp.RegExp
                                    )

        self.proxy.setFilterRegExp(search)

    @QtCore.pyqtSlot(int)
    def on_comboBox_currentIndexChanged(self, index):
        self.proxy.setFilterKeyColumn(index)

class Browser(QWebEngineView):   #(QWebView):
    windowList = []
    def createWindow(self, QWebEnginePage_WebWindowType):
        new_webview = Browser()
        new_window  = MainWindow()
        new_window.setCentralWidget(new_webview)
        new_window.show()
        self.windowList.append(new_window)
        return new_webview


if __name__ == "__main__":
    import sys
    app  = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setWindowIcon(QtGui.QIcon(':/icons/postman.ico'))

    # app.setStyleSheet("style.css")
    main = MainWindow()
    app.aboutToQuit.connect(main.shutdown)  # connect to the shutdown method on the window.
    main.show()
    main.resize(400, 600)
    sys.exit(app.exec_())
