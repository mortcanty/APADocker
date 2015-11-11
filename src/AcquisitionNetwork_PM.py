import os;
import matplotlib.pyplot as plt; #only necessary when plotting the graph is needed
import networkx as nx;
import csv;
import math;
import xlrd;

#import easy to use xml parser called minidom:
from xml.dom.minidom import parseString;

class Path:
	_edgeList=[];
	_nodeList=[];
	_length=0.0;
	
	def __init__(self,copyObject=None):		
		if copyObject is not None:
			self._edgeList=list(copyObject._edgeList);
			self._nodeList=list(copyObject._nodeList);
			self._length=copyObject._length;
		else:
			self._edgeList=[];
			self._nodeList=[];
			self._length=0.0;
	
	def setStartNode(self,node):
		self._nodeList=[node];
		self._nodeEdgeList=[];
		self._length=0.0;
		
	def getLength(self):
		return self._length;
	
	def getEdgeList(self):
		return self._edgeList;
			
	def extend(self,edge):
		self._edgeList.append(edge);
		self._nodeList.append(edge[1]);
		self._length=self._length+edge[2]["weight"];
	
	def trackBackToNode(self,node):
		while self._nodeList[len(self._nodeList)-1]!=node:				
			self._nodeList.pop();
			edge=self._edgeList.pop();	
			self._length=self._length-edge[2]["weight"];			
			
	def isInNodeList(self,currentNode):
		return currentNode in self._nodeList;
		
	def getDisplayStr(self,displayEdgeSemantic=True):
		result="";
		if len(self._edgeList)>0:
			result=self._edgeList[0][0];
			for edge in self._edgeList:
				if displayEdgeSemantic:
					result=result+" -"+str(edge[2]["semantic"])[0:3]+"- ";
				else:
					result=result+" - ";
				result=result+str(edge[1]);			
				
		return result;
	
	def highlightAndDraw(self,outputXMLFile="/apa/data/output/PM_disp.graphml",templateFile="/apa/data/PMTemplate.graphml",color="#0099CC"):
		#read Template into dom
		fileHandleIn=open(templateFile, 'r');
		data = fileHandleIn.read();
		fileHandleIn.close();
		
		#write path length into green box
		data=data.replace("Path Unattractiveness","U="+str(round(self.getLength(),2)));
		
		#write path type into second green box
		data=data.replace("Path Type",self._edgeList[0][2]["semantic"]);
		
		dom = parseString(data);
				
		#store XML-Id for every node
		xmlNodeId=dict();
		
		#color nodes of this path		
		for xmlTag in dom.getElementsByTagName('node'):			
			xmlTagString=xmlTag.toxml();
			for index,node in enumerate(self._nodeList):				
				if xmlTagString.find(">"+str(node)+"<")!=-1:
					#node being found that has to be colored					
					xmlNodeId[node]=str(xmlTag.getAttribute("id"));
					
					#uncomment the following lines in case you want to color nodes according to their position in the path
					# if index==1:
						# #color first node
						# if self._edgeList[0][2]["semantic"]=="import":
							# color="#0099CC";
						# else: 
							# color="#0099CC";
					# elif index==len(self._nodeList)-1:
						# #color last node
						# color="#0099CC";
					# else:
						# #color a node on the path
						# color="#0099CC";
						
					xmlTag.getElementsByTagName("data")[0].getElementsByTagName("y:Fill")[0].setAttribute("color",color);
		
		#color nodes
		for edge in self._edgeList:
			if xmlNodeId.has_key(edge[0]) and xmlNodeId.has_key(edge[1]):
				fromNode=xmlNodeId[edge[0]];			
				toNode=xmlNodeId[edge[1]];
				semantic=edge[2]["semantic"];
				for xmlTag in dom.getElementsByTagName('edge'):				
					if str(xmlTag.getAttribute("source"))==fromNode and str(xmlTag.getAttribute("target"))==toNode:
						xmlEdgeSemantic="";
						for dataTag in xmlTag.getElementsByTagName("data"):
							if dataTag.getAttribute("key")=="d12":
								xmlEdgeSemantic=dataTag.firstChild.data;					
						if xmlEdgeSemantic==semantic:
							#edge being found that has to be colored					
							xmlTag.getElementsByTagName("y:LineStyle")[0].setAttribute("color",color);						
		
		fileHandleOut=open(outputXMLFile,'w');
		dom.writexml(fileHandleOut);
		fileHandleOut.close();
		
		
	
class AcquisitionNetwork(nx.MultiDiGraph):
	_currentEdgeId=0;
	_pathList=[];
	_layout=None;
	
	def __init__(self):
		self._currentEdgeId=0;
		self._pathList=[];
		nx.MultiDiGraph.__init__(self);
		
	def add_edge(self,fromNode,toNode,currentWeight,currentDP,currentCosts,currentEdgeSemantic,inspectorateActivityType):
		self._currentEdgeId=self._currentEdgeId+1;
		nx.MultiDiGraph.add_edge(self,fromNode,toNode,weight=currentWeight,detectionprobability=currentDP,costs=currentCosts,semantic=currentEdgeSemantic,id=self._currentEdgeId,inspectorateactivitytype=inspectorateActivityType);
		
	def addCellValueToGraph(self,val,fromNode,toNode,edgeSemantic,germanCountryProfileUsed=True):
		if germanCountryProfileUsed:
			val=val.replace(",","."); #replacement necessary due to German version of MS Excel
		valArray=val.split(" ");
		if len(valArray)==4 and valArray[0]!="" and valArray[1]!="":				
			currentWeight=float(valArray[0]);				
			currentDP=float(valArray[1]);
			currentCosts=float(valArray[2]);
			inspectorateActivityType=valArray[3];
			self.add_edge(fromNode,toNode,currentWeight,currentDP,currentCosts,edgeSemantic,inspectorateActivityType);
	
	def parseXSLXFile(self,filename="/apa/data/APA.xlsx"):
		xlsxFileHandle=xlrd.open_workbook(filename);
		xlSheet=xlsxFileHandle.sheet_by_name("Adjacency Matrix");		
		numTables=4;
		fromRow=[1,18,35,52];
		toRow=[16,33,50,67];
		fromCol=[1,1,1,1]
		toCol=[16,16,16,16];
				
		for k in range(0,numTables):
			edgeSemantic=xlSheet.cell_value(rowx=fromRow[k]-1,colx=fromCol[k]-1);
			for rowIndex in range(fromRow[k],toRow[k]):
				fromNode=xlSheet.cell_value(rowx=rowIndex,colx=fromCol[k]-1);
				for colIndex in range(fromCol[k],toCol[k]):
					toNode=xlSheet.cell_value(rowx=fromRow[k]-1,colx=colIndex);
					val=xlSheet.cell_value(rowx=rowIndex,colx=colIndex);
					self.addCellValueToGraph(val,fromNode,toNode,edgeSemantic);
						
	def parseCSVFile(self,filename=["/apa/data/import.csv","/apa/data/diversion.csv","/apa/data/clandestine_processing.csv","/apa/data/misuse.csv"],delim=";",edgeSemantic=""):
		if isinstance(filename,list):
			#if list is given, call function again with listitems accordingly
			for fn in filename:
				self.parseCSVFile(fn,delim,edgeSemantic);
				
		else:
			#read file into adjacencyMatrix
			adjacencyMatrix=[];
			fileHandle=open(filename, 'r');
			csvReader = csv.reader(fileHandle, delimiter=delim, quotechar='|');
			for row in csvReader:
				adjacencyMatrix.append(row);		
			fileHandle.close();
			
			#get title of the adjacency matrix
			if edgeSemantic=="":
				edgeSemantic=adjacencyMatrix[0][0];
			
			#add nodes to graph from first row of matrix 
			self.add_nodes_from(adjacencyMatrix[0][1:len(adjacencyMatrix[0])]);
			
			#add adjacencyMatrix to graph
			for rowindex in range(1,len(adjacencyMatrix)):
				for colindex in range(1,len(adjacencyMatrix[rowindex])):				
					val=adjacencyMatrix[rowindex][colindex];
					self.addCellValueToGraph(val,adjacencyMatrix[rowindex][0],adjacencyMatrix[0][colindex],edgeSemantic);
						
	def replaceEdgeByMultiplicity(self,fromNode,toNode,currentEdgeSemantic,newNumber,divideCosts=True,generateInspectorateActivities=True):
		edgesToBeReplaced=dict();
		for key in self.edge[fromNode][toNode]:
			if self.edge[fromNode][toNode][key]["semantic"]==currentEdgeSemantic:
				edgesToBeReplaced[key]=self.edge[fromNode][toNode][key];
		
		for key in edgesToBeReplaced.keys():				
			edge=edgesToBeReplaced[key];
			currentWeight=edge["weight"];			
			currentDP=edge["detectionprobability"];
			currentCosts=edge["costs"];		
			currentInspectorateActivityType=edge["inspectorateactivitytype"];
			
			if divideCosts:
				currentCosts=currentCosts/newNumber;				
			
			self.remove_edge(fromNode,toNode,key);
				
			for i in range(0,newNumber):
				if generateInspectorateActivities:
					self.add_edge(fromNode,toNode,currentWeight,currentDP,currentCosts,currentEdgeSemantic,currentInspectorateActivityType+str(i));		
				else:
					self.add_edge(fromNode,toNode,currentWeight,currentDP,currentCosts,currentEdgeSemantic,currentInspectorateActivityType);		
			
	def calcAllPaths(self,source="Origin",dests=["DU Enrichment Product","DU Fuel Feed","DU Fuel","DU Reprocessed Material"],resetPathList=True,cutOff=None):
		#transform dests to list if a string is given
		if isinstance(dests,str):
			dests=[dests];			
		#use depth first search to obtain a list of all paths from source to dest(s)
		if resetPathList:
			self.clearPathList();
		edgeList=[];
		currentPath=Path();
		currentPath.setStartNode(source);		
		edgeList=self.out_edges(source,data=True);
		while edgeList!=[]:
			currentEdge=edgeList.pop();			
			currentNode=currentEdge[1]; #end-node of current edge
			
			#track back currentPath until starting Node of currentEdge is found
			currentPath.trackBackToNode(currentEdge[0]);			
				
			if not currentPath.isInNodeList(currentNode):
				#append current edge if no cycle is found
				currentPath.extend(currentEdge);
				
				if currentNode in dests:
					#stop path if dest is found and add the path to the resulting list
					self._pathList.append(Path(currentPath));					
				else:				
					#add further edges to edgeList
					edgeList.extend(self.out_edges(currentNode,data=True));					
	
	def getPathList(self):
		return self._pathList;
	
	def sortPathListByAttractiveness(self,reverseArg=False):
		self._pathList.sort(key=lambda path:path.getLength(),reverse=reverseArg);
	
	def getPathListDisplayMode(self,displayEdgeSemantic=True):
		pldisp=[];
		for p in self._pathList:
			pdisp=p.getDisplayStr(displayEdgeSemantic);
			if pdisp not in pldisp:
				pldisp.append(pdisp);
			elif displayEdgeSemantic:
				print("!!! duplicate found !!!");
		return pldisp;
		
	def getDistinctEdgeCount(self,typefilter=None,):
		#count distinct edges in _pathlist
		edgeList=[];
		for p in self._pathList:
			for e in p.getEdgeList():
				if edgeList.count(e)<1 and (typefilter==None or e[2]["semantic"] in typefilter):					
					edgeList.append(e);
		return len(edgeList);	
	
	def getInspectorateActivityHash(self):
		activityHash=dict();
		for p in self._pathList:
			for e in p.getEdgeList():
				activity=e[2]["inspectorateactivitytype"];
				effort=e[2]["costs"];
				oneminusbeta=e[2]["detectionprobability"];
				#print(str(activity)+":"+str(effort)+":"+str(oneminusbeta));
				if not activityHash.has_key(activity):					
					activityHash[activity]={"name":activity,"effort":effort,"1-beta":oneminusbeta};			
					
		return activityHash;
	
	def getDistinctActivityCount(self,typefilter=None,):
		#count distinct edges in _pathlist
		activityList=[];
		for p in self._pathList:
			for e in p.getEdgeList():
				inspectorateActivityType=str(e[2]["inspectorateactivitytype"]);				
				if activityList.count(inspectorateActivityType)<1 and (typefilter==None or e[2]["semantic"] in typefilter):					
					activityList.append(inspectorateActivityType);
		#for i,a in enumerate(activityList):
		#	print(str(i)+";"+a);
		return len(activityList);	
		
	def clearPathList(self):
		self._pathList=[];
	
	def parseLayoutFromCSV(self,fileName="positions.csv",delim=";"):
		self._layout=dict();
		fileHandle=open(fileName, 'r');
		csvReader = csv.reader(fileHandle, delimiter=delim, quotechar='|');
		for row in csvReader:
			self._layout[row[0]]=[float(row[2]),float(row[1])];			
		fileHandle.close();
		
	def draw(self):
		plt.figure(1,figsize=(12,12))
		nx.draw_networkx(self,self._layout);
		plt.show();

def TestDifferentPathRestrictions():	
	
	#version 1 (all paths without restrictions)
	#construct
	pm=AcquisitionNetwork();	
	#parse adjacency matrices
	pm.parseCSVFile();	
	
	#replace single reactor misuse edge by 17 reactor edges
	pm.replaceEdgeByMultiplicity("IU Fuel","Irradiated Fuel","misuse",17,divideCosts=True);
	
	#for natural uranium replace reactor misuse edge by 11 edges
	pm.replaceEdgeByMultiplicity("NU Fuel","Irradiated Fuel","misuse",11,divideCosts=True);
	
	#for direct use fuel replace reactor there is no need to replace it as there is only one reactor	
	
	length=0;
	pm.calcAllPaths("Origin","DU Enrichment Product");		
	length=length+len(pm.getPathList());
	print(str(len(pm.getPathList()))+" paths from 'Origin' to 'DU Enrichment Product'");
	
	pm.calcAllPaths("Origin","DU Fuel Feed");
	length=length+len(pm.getPathList());
	print(str(len(pm.getPathList()))+" paths from 'Origin' to 'DU Fuel Feed'");
		
	pm.calcAllPaths("Origin","DU Fuel");
	length=length+len(pm.getPathList());
	print(str(len(pm.getPathList()))+" paths from 'Origin' to 'DU Fuel'");
		
	pm.calcAllPaths("Origin","DU Reprocessed Material");
	length=length+len(pm.getPathList());
	print(str(len(pm.getPathList()))+" paths from 'Origin' to 'DU Reprocessed Material'");	
	
	print("version 1:	"+str(length)+" paths in total\n\n");	
	
	
	
	
	
	#version 2 (no reactor multiplicity)
	#construct
	pm=AcquisitionNetwork();	
	#parse adjacency matrices
	pm.parseCSVFile();	
		
	length=0;
	pm.calcAllPaths("Origin","DU Enrichment Product");		
	length=length+len(pm.getPathList());
	print(str(len(pm.getPathList()))+" paths from 'Origin' to 'DU Enrichment Product'");
	
	pm.calcAllPaths("Origin","DU Fuel Feed");
	length=length+len(pm.getPathList());
	print(str(len(pm.getPathList()))+" paths from 'Origin' to 'DU Fuel Feed'");
		
	pm.calcAllPaths("Origin","DU Fuel");
	length=length+len(pm.getPathList());
	print(str(len(pm.getPathList()))+" paths from 'Origin' to 'DU Fuel'");
		
	pm.calcAllPaths("Origin","DU Reprocessed Material");
	length=length+len(pm.getPathList());
	print(str(len(pm.getPathList()))+" paths from 'Origin' to 'DU Reprocessed Material'");	
	
	print("version 2:	"+str(length)+" paths in total\n\n");	
	
	
	
	
	
	
	#version 3 (stop searching, if any DU node is reached)
	#construct
	pm=AcquisitionNetwork();	
	#parse adjacency matrices
	pm.parseCSVFile();	
	
	pm.calcAllPaths();
	
	print("version 3:	"+str(len(pm.getPathList()))+" paths in total\n\n");	
	
	
	
	
	#version 4 (ignore different edge semantics)
	#construct
	pm=AcquisitionNetwork();	
	#parse adjacency matrices
	pm.parseCSVFile();	
	
	pm.calcAllPaths();
	
	print("version 4:	"+str(len(pm.getPathListDisplayMode(False)))+" paths in total\n\n");	

def TestOutput(numThreshold=10,stopWhenDUNodeReached=True,reactorMultiplicity=False,templateFile="apa/data/PMTemplate.graphml"):
	#construct
	pm=AcquisitionNetwork();	
	#parse adjacency matrices
	#pm.parseCSVFile();	
	pm.parseXSLXFile();
	
	if reactorMultiplicity:
		#replace single reactor misuse edge by 17 reactor edges
		pm.replaceEdgeByMultiplicity("IU Fuel","Irradiated Fuel","misuse",17,divideCosts=True);
		#for natural uranium replace reactor misuse edge by 11 edges
		pm.replaceEdgeByMultiplicity("NU Fuel","Irradiated Fuel","misuse",11,divideCosts=True);
	
	#find paths
	if stopWhenDUNodeReached:
		pm.calcAllPaths("Origin",["DU Enrichment Product","DU Fuel Feed","DU Fuel","DU Reprocessed Material"]);
	else:
		pm.calcAllPaths("Origin","DU Enrichment Product",resetPathList=False);
		pm.calcAllPaths("Origin","DU Fuel Feed",resetPathList=False);
		pm.calcAllPaths("Origin","DU Fuel",resetPathList=False);
		pm.calcAllPaths("Origin","DU Reprocessed Material",resetPathList=False);
	
	numPaths=len(pm.getPathList());	
	print(str(numPaths)+" paths found in total");	
	
	#ignore numThreshold if 'all' is passed
	if numThreshold=="all":
		num2BeExported=numPaths;
	else:
		num2BeExported=min(numThreshold,numPaths);
		
	#sort paths according to their attractiveness
	pm.sortPathListByAttractiveness();
	
	#output paths to .graphml-files
	for i,path in enumerate(pm.getPathList()[0:num2BeExported]):		
		iStr=str(i+1).zfill(int(math.ceil(math.log10(num2BeExported+1))));
#		print("write file /apa/output/OutputPath"+iStr+".graphml");
		path.highlightAndDraw("/apa/data/output/OutputPath"+iStr+".graphml",templateFile);
	
	return pm;
	
def Test():
	pm=AcquisitionNetwork();
	pm.parseCSVFile();
		
	pm.calcAllPaths("Origin","DU Enrichment Product");
	pm.sortPathListByAttractiveness();
	pl1=pm.getPathList();
	print(str(len(pl1))+" paths from 'Origin' to 'DU Enrichment Product'");
	
	pm.calcAllPaths("Origin","DU Fuel Feed");
	pm.sortPathListByAttractiveness();
	pl2=pm.getPathList();
	print(str(len(pl2))+" paths from 'Origin' to 'DU Fuel Feed'");
		
	pm.calcAllPaths("Origin","DU Fuel");
	pm.sortPathListByAttractiveness();
	pl3=pm.getPathList()
	print(str(len(pl3))+" paths from 'Origin' to 'DU Fuel'");
	
	pm.calcAllPaths("Origin","DU Reprocessed Material");
	pm.sortPathListByAttractiveness();
	pl4=pm.getPathList();
	print(str(len(pl4))+" paths from 'Origin' to 'DU Reprocessed Material'");	
	
	pl=pl1+pl2+pl3+pl4;	
	print(str(len(pl))+" paths in total");
	
	pm.calcAllPaths();
	pm.sortPathListByAttractiveness();
	pl=pm.getPathList();
	print(str(len(pl))+" paths in total when stopping at the first DU-node");
	
	
	print("\n\n\n");
	#check for duplicates
	c=0;
	for i,p in enumerate(pl):
		c=c+1;
		if c%100==0:
			print(str(c)+" paths checked");
		for j,op in enumerate(pl):
			if i!=j and p.getEdgeList()==op.getEdgeList():
				print("duplicate found");	

if __name__ == '__main__':
	pm=TestOutput('all',templateFile='/apa/data/PMTemplateWithOrigin.graphml')
	pm.draw()