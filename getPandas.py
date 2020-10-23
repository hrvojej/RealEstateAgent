from PyQt5 import QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel


class PandasTableModel(QtGui.QStandardItemModel):
    def __init__(self, data, parent=None):
        QtGui.QStandardItemModel.__init__(self, parent)
        self._data = data
        for row in data.values.tolist():
            data_row = [ QtGui.QStandardItem("{}".format(x)) for x in row ]
            self.appendRow(data_row)
        return

    def rowCount(self, parent=None):
        return len(self._data.values)

    def columnCount(self, parent=None):
        return self._data.columns.size

    def headerData(self, x, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._data.columns[x]
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return self._data.index[x]
        return None

    def data(self, index, role):
        if role == Qt.ForegroundRole:
            value = str(self._data.iloc[index.row()][index.column()])
            if value.startswith("https://") or value.startswith("http://"):
                return QtGui.QColor("blue")
        elif role == Qt.DisplayRole:
            if index.column() == 5 or index.column() == 6:
                val = self._data.iloc[index.row()][index.column()]
                if not isinstance(val, int):
                    val = int(val)
                return '{:,}'.format(val).replace(',', '.')

            else:
                return str(self._data.iloc[index.row(), index.column()])
        elif role == Qt.EditRole:
                return str(self._data.iloc[index.row(), index.column()])

