import wx
import wx.grid


SORT_ASC = 'asc'
SORT_DESC = 'desc'
SORT_NONE = 'none'


class SmartGrid(wx.grid.Grid):
    def __init__(self, parent):
        super(SmartGrid, self).__init__(parent)

        self.data = []
        self.columnHorzAlignment = []
        self.columnVertAlignment = []
        self.columnValueFormatters = []

        self.SetRowLabelSize(0)
        self.Bind(wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self.OnGridLabelLeftClick)
        self.Bind(wx.grid.EVT_GRID_LABEL_LEFT_DCLICK, self.OnGridLabelLeftDoubleClick)
        self.GetGridColLabelWindow().Bind(wx.EVT_PAINT, self.OnGridColLabelWindowPaint)

    def CreateGrid(self, selMode, numRows, numCols=0, columnsSetup=None):
        if columnsSetup:
            numCols = len(columnsSetup)

        super(SmartGrid, self).CreateGrid(numRows, numCols, selMode)

        if columnsSetup:
            for index, setup in enumerate(columnsSetup):
                self.SetColLabelValue(index, setup.get('label'))
                self.columnHorzAlignment.append(setup.get('horz_alignment', wx.ALIGN_LEFT))
                self.columnVertAlignment.append(setup.get('vert_alignment', wx.ALIGN_CENTER_VERTICAL))
                self.columnValueFormatters.append(setup.get('formatter', lambda x: x))

        self.columnsSortDirections = [SORT_NONE] * numCols
        self.columnsSortOrder = []

    def ClearGrid(self):
        super(SmartGrid, self).ClearGrid()
        self.data = []

    def OnGridLabelLeftClick(self, event):
        self.updateSorting(event.GetCol(), not event.ShiftDown())

    def OnGridLabelLeftDoubleClick(self, event):
        self.updateSorting(event.GetCol(), not event.ShiftDown())

    def getCmpFunction(self):
        def compare(x, y):
            for i in self.columnsSortOrder:
                direction = self.columnsSortDirections[i]
                if x[i] != y[i]:
                    if direction == SORT_ASC:
                        return 1 if x[i] > y[i] else -1  # TODO azaza custom comparator ftw
                    elif direction == SORT_DESC:
                        return 1 if x[i] < y[i] else -1
                    else:
                        return 0
            return 0
        return compare

    def updateSorting(self, columnIndex, startOver):
        currentDirection = self.columnsSortDirections[columnIndex]
        if startOver:
            self.columnsSortDirections = [SORT_NONE] * self.GetNumberCols()
            self.columnsSortOrder = []
        self.columnsSortDirections[columnIndex] = SORT_ASC if currentDirection in [SORT_NONE, SORT_DESC] else SORT_DESC
        if columnIndex in self.columnsSortOrder:
            self.columnsSortOrder.remove(columnIndex)
        self.columnsSortOrder.append(columnIndex)
        self.data.sort(cmp=self.getCmpFunction())
        for rowIndex, values in enumerate(self.data):
            self.fillRow(rowIndex, values)
        self.Refresh()

    def AddRow(self, values):
        self.data.append(values)
        self.data.sort(cmp=self.getCmpFunction())
        rowIndex = self.data.index(values)
        self.InsertRows(rowIndex, 1)
        self.fillRow(rowIndex, values)
        return rowIndex

    def fillRow(self, rowIndex, values):
        for columnIndex in xrange(self.GetNumberCols()):
            cellValue = self.columnValueFormatters[columnIndex](values[columnIndex])
            self.SetCellValue(rowIndex, columnIndex, unicode(cellValue))
            self.SetCellAlignment(rowIndex, columnIndex, horiz=self.columnHorzAlignment[columnIndex], vert=self.columnVertAlignment[columnIndex])

    def OnGridColLabelWindowPaint(self, event):
        dc = wx.PaintDC(self.GetGridColLabelWindow())
        gc = wx.GraphicsContext.Create(dc)
        gc.PushState()

        paintedWidth = -self.GetViewStart()[0] * self.GetScrollPixelsPerUnit()[0]
        for columnIndex in xrange(self.GetNumberCols()):
            columnWidth = self.GetColSize(columnIndex)
            columnHeaderRect = (paintedWidth, 0, columnWidth, 32)
            dc.SetBrush(wx.Brush(colour=wx.WHITE, style=wx.TRANSPARENT))
            dc.DrawRectangle(
                columnHeaderRect[0] - int(columnIndex != 0),
                columnHeaderRect[1],
                columnHeaderRect[2] + int(columnIndex != 0),
                columnHeaderRect[3])
            paintedWidth += columnWidth

            dc.SetTextForeground(wx.BLACK)
            font = dc.GetFont()
            font.SetWeight(wx.FONTWEIGHT_BOLD)
            dc.SetFont(font)
            dc.DrawLabel(self.GetColLabelValue(columnIndex), columnHeaderRect, wx.ALIGN_CENTER | wx.ALIGN_TOP)

            sortDirection = self.columnsSortDirections[columnIndex]
            triangleConfiguration = []
            tX = columnHeaderRect[0] + 3
            tY = columnHeaderRect[1] + 3
            if sortDirection == SORT_ASC:
                triangleConfiguration = [(tX + 3, tY), (tX + 6, tY + 4), (tX, tY + 4)]
            elif sortDirection == SORT_DESC:
                triangleConfiguration = [(tX, tY), (tX + 6, tY), (tX + 3, tY + 4)]
            if triangleConfiguration:
                gc.PushState()
                gc.SetBrush(gc.CreateBrush(wx.Brush(wx.BLACK, wx.SOLID)))
                gc.SetPen(wx.Pen(wx.BLACK, 0.5))
                path = gc.CreatePath()
                path.MoveToPoint(*triangleConfiguration[0])
                path.AddLineToPoint(*triangleConfiguration[1])
                path.AddLineToPoint(*triangleConfiguration[2])
                path.AddLineToPoint(*triangleConfiguration[0])
                gc.DrawPath(path)
                gc.PopState()

        gc.PopState()
