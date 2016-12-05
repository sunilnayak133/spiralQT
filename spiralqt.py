#spiralstairs with PyQt5 for Maya 2017
#Author - Sunil S Nayak
import PySide2.QtCore as qc
import PySide2.QtGui as qg
import PySide2.QtWidgets as qw
import functools 
import maya.cmds as mc

class spiralUI(qw.QDialog):

    def __init__(self):
        #init the main dialog
        qw.QDialog.__init__(self)
        #set window title
        self.setWindowTitle('Spiral Stair Generator')
        self.setFixedWidth(400)

        #init the fields
        #height range min, max
        self.hrm = qw.QDoubleSpinBox()
        self.hrM = qw.QDoubleSpinBox()

        self.hrm.setRange(0.0,1000.0)
        self.hrM.setRange(0.0,2000.0)

        #init sliders,
        #connect to slideApply function to make dynamic editing possible

        #number of turns
        self.nt = qw.QSlider(qc.Qt.Horizontal)
        self.nt.setMinimum(1)
        self.nt.setMaximum(10)
        self.nt.valueChanged.connect(self.slideApply)
        self.nt.setValue(3)
        #number of steps
        self.ns = qw.QSlider(qc.Qt.Horizontal)
        self.ns.setMinimum(10)
        self.ns.setMaximum(100)
        self.ns.valueChanged.connect(self.slideApply)
        self.ns.setValue(50)
        #radius - divide by 10
        self.r = qw.QSlider(qc.Qt.Horizontal)
        self.r.setMinimum(7)
        self.r.setMaximum(25)
        self.r.valueChanged.connect(self.slideApply)
        self.r.setValue(10)
        #step gap - divide by 1000
        self.stgp = qw.QSlider(qc.Qt.Horizontal)
        self.stgp.setMinimum(1)
        self.stgp.setMaximum(999)
        self.stgp.valueChanged.connect(self.slideApply)


        #apply button, link to apply function
        btnapp = qw.QPushButton('Apply')
        btnapp.clicked.connect(functools.partial(self.apply))
        #Form layout - add all widgets with labels
        self.setLayout(qw.QFormLayout())
        self.layout().addRow('Height Range: Min:',self.hrm)
        self.layout().addRow('Max:',self.hrM)
        self.layout().addRow('Number of Turns:', self.nt)
        self.layout().addRow('Number of Steps:', self.ns)
        self.layout().addRow('Radius:',self.r)
        self.layout().addRow('Step Gap:',self.stgp)
        self.layout().addRow('',btnapp)

    #apply function
    #takes values from UI and builds staircase
    #params - nothing
    #return - nothing
    def apply(self):
        #check if stairs already exist
        sl = mc.ls('stairObject')
        if(len(sl)!=0):
            #delete old stair object if it exists
            mc.delete(sl)
            mc.delete('spineObject')
            mc.delete('spiralstairs')

        #obtain values from UI
        hr = [self.hrm.value(),self.hrM.value()]
        nt = self.nt.value()
        r = float(self.r.value())/10.0
        st = self.ns.value()
        sg = (1000.0 - float(self.stgp.value()))/1000.0

        #build staircase and move it to the right position
        self.staircase = self.spiralst(st,hr[1]-hr[0],nt,r,sg)
        mc.move(0,hr[0],0,self.staircase)

    #pieslice function
    #takes args from spiralst function and builds one stair (by slicing a cylinder suitably)
    #params - pStAn - Start Angle of pieslice,
    #         pEnAn - End Angle of pieslice
    #         pR    - Radius of pieslice
    #         pH    - Height of pieslice
    #return - name of the pieslice that's created
    def pieslice(self,pStAn, pEnAn, pR, pH = 0.1):
        cyl = mc.polyCylinder(h = pH, r = pR, n = 'stairObject')
        cx = mc.objectCenter(x = True)
        cy = mc.objectCenter(y = True)
        cz = mc.objectCenter(z = True)

        h = pH
        #cut the cylinder, and separate different parts
        cut = mc.polyCut(cyl, 
                   cutPlaneCenter = [cx,h/2,cz],
                   cutPlaneRotate = [0,pStAn,0],
                   extractFaces = True, 
                   extractOffset = [0,0,0])
        cut = mc.polyCut(cyl, 
                   cutPlaneCenter = [cx,h/2,cz],
                   cutPlaneRotate = [0,pEnAn,0],
                   extractFaces = True, 
                   extractOffset = [0,0,0])
        obj = mc.polySeparate(cyl)
        names = []
        for i in range(len(obj)):
            mc.rename(obj[i],'part'+str(i))
            names.append('part'+str(i))   
        
        #fill hole of the required pieslice             
        mc.polyCloseBorder(names[2])
        #delete useless parts from the now separated cylinder
        mc.delete(names[0:2] + names[3:4], s=True)
        return names[2]


    #spiralst function
    #function to make the spiral staircase
    #params - pNS - Number of stairs
    #         pH  - Height of staircase
    #         pNT - Number of turns
    #         pR  - Radius of stair
    #         pSG - Gap % (<1) between consecutive stairs
    #return - the staircase object
    def spiralst(self,pNS, pH, pNT, pR,pSG):
        stepangle = float(pNT*360)/float(pNS)
        stepht = float(pH)/float(pNS)
        currentangle = 0
        currentht = 0
        #build first stair and add it to the list of stairs
        stair = self.pieslice(stepangle+0.5, 0.5, pR, stepht*pSG)
        stairlist = [stair]
        #make more stairs by rotating and translating duplicates of the first stair
        for i in range(1,pNS):
            newstair = mc.duplicate(stair, n = "stair"+str(i))
            currentht += stepht
            currentangle+=stepangle
            mc.move(0,currentht,0,newstair)
            mc.rotate(0,currentangle,0,newstair)
            stairlist.append(newstair)
        #make a spine for the staircase and move it to the right position            
        spine = mc.polyCylinder(h = pH, r = 0.05,n='spineObject')
        mc.move(0,pH/2,0, spine)
        stairlist.append(spine)

        #unite all the elements of stairlist and return that union
        staircase = mc.polyUnite(*stairlist, n = "spiralstairs")
        return staircase

    #slideApply function
    #function to make dynamic editing possible
    #params - nothing
    #return - nothing
    def slideApply(self):
        sl = mc.ls('stairObject')
        if(len(sl)==0):
            return
        else:
            self.apply()


#create UI
s = spiralUI()
#show UI
s.show()