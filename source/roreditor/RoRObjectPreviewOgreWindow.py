#Thomas Fischer 31/05/2007, thomas@thomasfischer.biz
from ShapedControls import ShapedWindow
import wx, math, glob
import ogre.renderer.OGRE as ogre
from wxogre.OgreManager import *
from wxogre.wxOgreWindow import *
from ror.SimpleTruckRepresentation import *
from ror.odefparser import *
from ror.rorcommon import *
from ror.settingsManager import rorSettings
from roreditor.RoRConstants import *
from roreditor.RoRVirtualKeys import *

class TreeDropTarget(wx.PyDropTarget):
	def __init__(self, window):
		wx.PyDropTarget.__init__(self)
		self.do = wx.FileDataObject()
		self.SetDataObject(self.do)

	def OnEnter(self, x, y, d):
		print "OnEnter: %d, %d, %d\n" % (x, y, d)
		return wx.DragCopy

	def OnDragOver(self, x, y, d):
		print "OnDragOver: %d, %d, %d\n" % (x, y, d)
		return wx.DragCopy

	def OnLeave(self):
		print "OnLeave\n"

	def OnDrop(self, x, y):
		print "OnDrop: %d %d\n" % (x, y)
		return True

	def OnData(self, x, y, d):
		print "OnData: %d, %d, %d\n" % (x, y, d)
		self.GetData()
		print "%s\n" % self.do.GetFilenames()
		return d

#class SpinControlOverlayElementFactory(ogre.OverlayElementFactory):
#	pass

class ObjectPreviewOgreWindow(wxOgreWindow):
	# BUG: Memory eater, partially fixed, I need to check clearing variables on exceptions
	def __init__(self, parent, name, **kwargs):
		log().debug("ObjectPreviewOgreWindow is initialising...")
		self.rordir = rorSettings().rorFolder
		self.parent = parent
		self.objnode = None
		self.objentity = None
		self.camalpha = 0
		self.radius = 40
		self.dragging = False
		self.mode = None
		self.logovisible = True
		self.wheelRadius = 0
		self.sceneManager = None
		wxOgreWindow.__init__(self, parent, -1, name, **kwargs)
		# bind mouse and keyboard
		self.Bind(wx.EVT_MOUSE_EVENTS, self.onMouseEvent)
		self.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)
#		droptarget = TreeDropTarget(self)
#		self.SetDropTarget(droptarget)
		log().debug("ObjectPreviewOgreWindow created")

	def SceneInitialisation(self):
		log().debug("SceneInitialisation")
		initResources()
		self.createSceneManager()

	def createSceneManager(self, type="object"):
		log().debug("createSceneManager")
		#get the scenemanager
		self.mode = type
		uuid = randomID()
		if self.mode == "object":
			self.sceneManager = getOgreManager().createSceneManager(ogre.ST_GENERIC)
		elif self.mode == "terrain":
			self.sceneManager = getOgreManager().createSceneManager(ogre.ST_EXTERIOR_CLOSE)

		# create a camera
		self.camera = self.sceneManager.createCamera(str(randomID()) + 'Camera')
		self.camera.lookAt(ogre.Vector3(0, 0, 0))
		self.camera.setPosition(ogre.Vector3(0, 0, 100))
		self.camera.nearClipDistance = 1
		self.camera.setAutoAspectRatio(True)

		# create the Viewport"
		self.viewport = self.renderWindow.addViewport(self.camera, 0, 0.0, 0.0, 1.0, 1.0)
		self.viewport.backgroundColour = ogre.ColourValue(0, 0, 0)
		self.viewport.setOverlaysEnabled(False) #disable terrain Editor overlays on this viewport

		#create objects
		self.populateScene()
		
	def populateScene(self):
		log().debug("populating Scene")
		self.sceneManager.AmbientLight = ogre.ColourValue(0.7, 0.7, 0.7)
		self.sceneManager.setShadowTechnique(ogre.ShadowTechnique.SHADOWTYPE_STENCIL_ADDITIVE);
		self.sceneManager.setSkyDome(True, 'mysimple/terraineditor/previewwindowsky', 4.0, 8.0)

		#self.MainLight = self.sceneManager.createLight('MainLight')
		#self.MainLight.setPosition (ogre.Vector3(20, 80, 130))

		# add some fog
#		self.sceneManager.setFog(ogre.FOG_EXP, ogre.ColourValue.White, 0.0000002)

		# create a floor Mesh
		plane = ogre.Plane()
		plane.normal = ogre.Vector3(0, 1, 0)
		plane.d = 200
		uuid = str(randomID())
		ogre.MeshManager.getSingleton().createPlane(uuid + 'FloorPlane', "General", plane, 20000000.0, 20000000.0,
													20, 20, True, 1, 50.0, 50.0, ogre.Vector3(0, 0, 1),
													ogre.HardwareBuffer.HBU_STATIC_WRITE_ONLY,
													ogre.HardwareBuffer.HBU_STATIC_WRITE_ONLY,
													True, True)

		# create floor entity
		entity = self.sceneManager.createEntity(uuid + 'floor', uuid + 'FloorPlane')
		entity.setMaterialName('mysimple/terraineditor/previewwindowfloor')
		self.sceneManager.getRootSceneNode().createChildSceneNode().attachObject(entity)

		if self.logovisible:
			uuid = str(randomID())
			self.logowheelnode = self.sceneManager.getRootSceneNode().createChildSceneNode(uuid + "logonode")
			self.logowheelentity = self.sceneManager.createEntity(uuid + 'logoentity', "logowheel.mesh")
			self.logowheelentity.setMaterialName('mysimple/terrainselect')
			self.logowheelnode.attachObject(self.logowheelentity)
			self.logowheelnode.rotate(ogre.Vector3(1, 0, 0), ogre.Degree(-90), relativeTo=ogre.Node.TransformSpace.TS_WORLD)
			self.logowheelnode.rotate(ogre.Vector3(0, 1, 0), ogre.Degree(90), relativeTo=ogre.Node.TransformSpace.TS_WORLD)
			self.logowheelnode.setScale(0.025, 0.025, 0.025)

			uuid = str(randomID())
			self.logotextnode = self.sceneManager.getRootSceneNode().createChildSceneNode(uuid + "logonode")
			self.logotextentity = self.sceneManager.createEntity(uuid + 'logoentity', "logotext.mesh")
			self.logotextentity.setMaterialName('mysimple/transblue')
			self.logotextnode.attachObject(self.logotextentity)
			self.logotextnode.rotate(ogre.Vector3(1, 0, 0), ogre.Degree(-90), relativeTo=ogre.Node.TransformSpace.TS_WORLD)
			self.logotextnode.rotate(ogre.Vector3(0, 1, 0), ogre.Degree(90), relativeTo=ogre.Node.TransformSpace.TS_WORLD)
			self.logotextnode.setScale(0.025, 0.025, 0.025)

		else:
			pass
			#self.logotextnode.setVisible(False)
			#self.logowheelnode.setVisible(False)
		log().debug("Scene populated")

	def loadFile(self, filename):
		self.filename = filename
		filenameonly, extension = os.path.splitext(filename)
		uuid = randomID()

		#hide logo
		self.logovisible = False
		self.wheelRadius = 0 
		try:
			if extension.lower() in VALIDSTRUCKS:
				self.free()
				self.createSceneManager("object")
				uuid = randomID()
				self.objnode, self.objentity, manualobject = createTruckMesh(self.sceneManager, filename, uuid)
				#print "aaa", self.objnode.getPosition()
			elif extension.lower() in [".odef"]:
				self.free()
				self.createSceneManager("object")
				self._loadOdef(filename, uuid)
			elif extension.lower() in [".mesh"]:
				self.free()
				self.createSceneManager("object")
				self.loadmesh(filename, uuid)
			elif extension.lower() in [".terrn"]:
				self.free()
				self.createSceneManager("terrain")
				terrain = RoRTerrain(filename)
				cfgfile = os.path.join(os.path.dirname(filename), terrain.TerrainConfig)
				self.objnode = self.sceneManager.getRootSceneNode().createChildSceneNode(uuid + "objnode")
				(x, z) = self.getTerrainSize(cfgfile)
				self.terrainsize = (x, z)
				print "terrain size: ", x, z
				self.objnode.setPosition(x / 2, 0, z / 2)
				self.sceneManager.setWorldGeometry(cfgfile)
				del terrain
		except:
			self.free()
			raise 
		
	def getTerrainSize(self, filename):
		lines = loadResourceFile(filename)
		x = 1500
		z = 1500
		for line in lines:
			if line.lower().strip()[:11] == 'pageworldx=':
				x = int(line.lower().strip()[11:])
			if line.lower().strip()[:11] == 'pageworldz=':
				z = int(line.lower().strip()[11:])
		return (x, z)
		
	def _loadOdef(self, filename, uuid):
		try:
			odef = odefClass(filename)
		except Exception, err:
			odef = None
			log().error("error while processing odef file %s" % filename)
			log().error(str(err))
			raise
		# create mesh
		self.objnode = self.sceneManager.getRootSceneNode().createChildSceneNode(uuid + "objnode")
		self.objentity = self.sceneManager.createEntity(uuid + 'objentity', odef.meshName)
		self.objnode.attachObject(self.objentity)
		self.objnode.rotate(ogre.Vector3(1, 0, 0), ogre.Degree(-90), relativeTo=ogre.Node.TransformSpace.TS_WORLD)
		#self.objnode.setPosition(0,0,0)
		self.objnode.setScale(odef.scale)

	def loadmesh(self, meshname, uuid):
		# create mesh
		self.objnode = self.sceneManager.getRootSceneNode().createChildSceneNode(uuid + "objnode")
		self.objentity = self.sceneManager.createEntity(uuid + 'objentity', meshname)
		self.objnode.attachObject(self.objentity)
		self.objnode.rotate(ogre.Vector3(1, 0, 0), ogre.Degree(-90), relativeTo=ogre.Node.TransformSpace.TS_WORLD)


	def free(self):
		# Lepes:
		#   clearScene: Empties the entire scene, inluding all SceneNodes, Entities, Lights, BillboardSets etc.
		#   Cameras are not deleted at this stage since they are still referenced by viewports,
		#   which are not destroyed during this process. 		
		if not (self.sceneManager is None):
			self.sceneManager.clearScene()
			self.renderWindow.removeAllViewports()
			self.sceneManager.destroyAllCameras()
#			getOgreManager().removeRenderWindow(self)
			getOgreManager().destroySceneManager(self.sceneManager)
			self.sceneManager = None

		self.mode = None
		self.objentity = None
		self.objnode = None
	

# Lepes: is it really needed??
#		try:
#			self.sceneManager.destroyAllManualObjects()
#		except Exception, e:
#			log().exception(str(e))
#
#		try:
#			if self.logotextnode:
#				self.logotextnode.detachAllObjects()
#			if self.logowheelnode:
#				self.logowheelnode.detachAllObjects()
#			self.sceneManager.destroySceneNode(self.logotextnode.getName())
#			self.sceneManager.destroySceneNode(self.logowheelnode.getName())
#			self.sceneManager.destroyEntity(self.logotextentity)
#			self.sceneManager.destroyEntity(self.logowheelentity)
#		except Exception, e:
#			log().exception(str(e))
#		try:
#			#BUG: next line fails and goes to except
#			if not self.objnode is None:
#				self.objnode.detachAllObjects()
#				self.sceneManager.destroySceneNode(self.objnode.getName())
#		except Exception, e:
#			log().exception(str(e))
#
#		#try:
#			#BUG Entering this function alone seams to kill the application.
#			#self.sceneManager.destroyEntity(self.objentity)
#		#except Exception, e:
#			#log().exception(str(e))
#
#		self.renderWindow.removeAllViewports()
#		getOgreManager().destroySceneManager(self.sceneManager)
		


	def updateCamera(self):
		if not self.mode is None:
			self.radius = 20
			if self.logovisible:
				self.radius = 100
				pos = self.logotextnode.getPosition()
				lookheight = ogre.Vector3(0, 0, 0)
				self.logowheelnode.rotate(ogre.Vector3(1, 0, 0), ogre.Degree(1), relativeTo=ogre.Node.TransformSpace.TS_LOCAL)
			else:
				if self.mode == "object":
					if self.objentity is None:
						height = 20
					else:
						self.radius = self.objentity.getBoundingRadius() * 2
						height = self.objentity.getBoundingBox().getMaximum().z
					rotateheight = ogre.Vector3(0, height * 0.2, 0)
					pos = self.objnode.getPosition() + rotateheight + (self.objentity.getBoundingBox().getMinimum() + self.objentity.getBoundingBox().getMaximum()) / 2
					lookheight = ogre.Vector3(0, height / 2, 0)
				elif self.mode == "terrain":
					self.radius = self.terrainsize[0]
					rotateheight = ogre.Vector3(0, self.terrainsize[0] / 2, 0)
					pos = self.objnode.getPosition() + rotateheight
					lookheight = -rotateheight

			self.radius += self.wheelRadius
			dx = math.cos(self.camalpha) * self.radius
			dy = math.sin(self.camalpha) * self.radius
			self.camera.setPosition(pos - ogre.Vector3(dx, -5, dy))
			self.camera.lookAt(pos + lookheight)
			if self.dragging == False:
				self.camalpha += math.pi / 720
			if self.camalpha >= 360:
				self.camalpha -= 360

	def OnFrameStarted(self):
		if self.logovisible:
			self.logowheelnode.rotate(ogre.Vector3(1, 0, 0), ogre.Degree(1), relativeTo=ogre.Node.TransformSpace.TS_LOCAL)
		if self.objnode is not None:
			self.updateCamera()

	def onKeyDown(self, event):
		if event.m_keyCode == WXK_X:
			if self.objnode is not None:
				self.objnode.pitch(ogre.Degree(90))
		elif event.m_keyCode == WXK_Z:
			if self.objnode is not None:
				self.objnode.roll(ogre.Degree(90))
		elif event.m_keyCode == WXK_Y:
			if self.objnode is not None:
				self.objnode.yaw(ogre.Degree(90))
		event.Skip()
																				
	def onMouseEvent(self, event):
		# don't give focus on mouse move
		if event.RightDown() or event.LeftDown():
			self.SetFocus() #Gives focus for the mouseWheel works

		if event.RightDown(): #Precedes dragging
			self.StartDragX, self.StartDragY = event.GetPosition() #saves position of initial click
		elif event.Dragging() and event.RightIsDown(): #Dragging with RMB
			x, y = event.GetPosition()
			dx = self.StartDragX - x
			dy = self.StartDragY - y
			self.StartDragX, self.StartDragY = x, y
			self.camalpha -= float(dx) * (math.pi / 720) * 2
			self.updateCamera()
			self.dragging = True
		else:
			self.dragging = False
		
		if event.GetWheelRotation() != 0:
			if event.GetWheelRotation() > 0:
				self.wheelRadius -= 1.5   # move backwards
			else:
				self.wheelRadius += 1.5
			
		event.Skip()
	def Destroy(self):
		#super clase will clear
		pass

		
				
