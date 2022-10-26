
import sys

from PyQt5.QtWidgets import * 
                            
from PyQt5.QtSvg import QGraphicsSvgItem, QSvgRenderer


#bounds toevoegen en testen.

class SvgItem(QGraphicsSvgItem):

    def __init__(self, renderer, parent=None):
        super().__init__(parent)
        self.setSharedRenderer(renderer)

    def mousePressEvent(self, event: 'QtWidgets.QGraphicsSceneMouseEvent'):
        point = event.pos().x()
        print(f'svg item:{ point} - mousePressEvent()')
        super().mousePressEvent(event)
        
        #contains(


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        

        renderer = QSvgRenderer('./gui/StoperaNAP.drawio.svg')
        item = SvgItem(renderer)

        self.scene = QGraphicsScene()
        self.scene.addItem(item)

        self.view = QGraphicsView()
        self.view.setScene(self.scene)
        self.setCentralWidget(self.view)
        
        namedSvg = SvgItem(renderer)
        
        if renderer.elementExists("pump1953"):
            namedSvg.setElementId("pump1953")
            print("jaaa")
            




app = QApplication(sys.argv)

w = MainWindow()
w.setGeometry(1024, 831, 1024, 831 )
w.show()

app.exec()