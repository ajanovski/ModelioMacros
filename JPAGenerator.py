###############################################################################
#
#    Copyright (C) 2021 Vangel V. Ajanovski
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################

#
# JPAGenerator 1.3
# Generates Java JPA annotated code for selected persistent entity classes
#
# Author:  Vangel V. Ajanovski (https://ajanovski.info)
#
# Applicable on: Class
# Note: The macro does not support ManyToMany links
#
# Version history:
# 1.0		2017-03-29	First Version
# 1.1		2019-12-13	Schema support
# 1.2		2020-05-20	FK support
# 1.3		2021-03-25  Use persist-name on relations for custom-named FK
# 1.4		2021-08-09	Support for length persistence attribute


import os
import errno

def toDBName(ime):
	name=ime.encode("ascii","ignore")
	out=""
	for i in range(len(name)-1):
		out=out+str.lower(name[i])
		if name[i]==str.lower(name[i]) and name[i+1]==str.upper(name[i+1]):
			out=out+"_"
	out=out+str.lower(name[len(name)-1])
	return out



def getKeyAttrib(element):
	if (isinstance(element, Class)):
		for at in element.getOwnedAttribute():
			stereotypes = at.getExtension()
			if (stereotypes.size() > 0):
				for stereotype in stereotypes:
					if stereotype.getName()=="Identifier" and stereotype.getOwner().getOwnerModule().getName()=="PersistentProfile" :
						return at



def capt(ime):
	name=ime.encode("ascii","ignore")
	return str.upper(name[0])+name[1:]



def displayNote(outFile,element):
	outFile.write("/*\n")
	for desc in element.getDescriptor():
		outFile.write (desc.getContent().encode('utf8')+"\n")
	outFile.write("*/\n")


def persistentName(element):
	vrednost = ""
	for z in element.getTag():
		if z.getDefinition().getName()=="persistent.entity.persistentName":
			vrednost = z.getActual()[0].getValue()
	if vrednost and not(vrednost==""):
		return vrednost
	else:
		return toDBName(element.getName())


def persistentRelationShipName(element):
	vrednost = ""
	for z in element.getAssociation().getTag():
		if z.getDefinition().getName()=="persisten.relationship.persistentName":
			vrednost = z.getActual()[0].getValue()
	if vrednost and not(vrednost==""):
		return vrednost
	else:
		return persistentName(getKeyAttrib(element.getTarget()))


def displayStereotypes(outFile,element):	
	stereotypes = element.getExtension()
	if (stereotypes.size() > 0):
		# for each extended stereotype
		for stereotype in stereotypes:
			if stereotype.getName()=="Entity" and stereotype.getOwner().getOwnerModule().getName()=="PersistentProfile":
				outFile.write("@Entity\n")
				shemata = ""
				for z in element.getTag():
					if z.getDefinition().getName()=="persistent.entity.schema":
						shemata = z.getActual()[0].getValue()
				outFile.write("@Table (schema=\"" + shemata +"\", name=\"" + persistentName(element) + "\")\n")



def checkIdAttrib(element):	
	stereotypes = element.getExtension()
	if (stereotypes.size() > 0):
		for stereotype in stereotypes:
			if (stereotype.getName()=="Identifier"):
				return True
	return False



def javaTypes(tip,nullable):
	if tip==Modelio.getInstance().getModelingSession().getModel().getUmlTypes().getSTRING():
		return "String"
	if tip==Modelio.getInstance().getModelingSession().getModel().getUmlTypes().getLONG():
		if nullable=="false":
			return "long"
		else:
			return "Long"
	if tip==Modelio.getInstance().getModelingSession().getModel().getUmlTypes().getBOOLEAN():
		return "Boolean"
	if tip==Modelio.getInstance().getModelingSession().getModel().getUmlTypes().getDATE():
		return "Date"
	if tip==Modelio.getInstance().getModelingSession().getModel().getUmlTypes().getFLOAT():
		return "Float"
	if tip==Modelio.getInstance().getModelingSession().getModel().getUmlTypes().getINTEGER():
		if nullable=="false":
			return "int"
		else:
			return "Integer"
	if tip==Modelio.getInstance().getModelingSession().getModel().getUmlTypes().getBYTE():
		return "byte[]"



def printAttrib(element,attribStream,methodStream):
	if checkIdAttrib(element):
		methodStream.append("\t@Id\n");
		methodStream.append("\t@GeneratedValue(strategy = GenerationType.IDENTITY)\n\n");
		vunique="true"
		vnullable="false"
	else:
		vunique="false"
		vnullable="true"
		for cons in element.getConstraintDefinition():
			for tag in cons.getTag():
				dt=tag.getDefinition()
				if (dt.getName()=="SQLConstraint.isNotNull"):
					for da in tag.getActual():
						if da.getValue()=="TRUE": 
							vnullable = "false"
						else:
							vnullable = "true"
				if (dt.getName()=="SQLConstraint.isUnique"):
					for da in tag.getActual():
						if da.getValue()=="TRUE": 
							vunique = "true"
						else:
							vnullable = "false"
	attribStream.append("\tprivate " + javaTypes(element.getType(),vnullable) +  " "+element.getName()+";\n");
	nullString = ""
	if vnullable=="false":
		nullString = ", nullable = "+vnullable
	uniqueString = ""
	if vunique=="true":
		uniqueString = ", unique = "+vunique
	precisionString = ""
	for tag in element.getTag():
		dt=tag.getDefinition()
		if (dt.getName()=="persistent.property.length"):
			for da in tag.getActual():
				precisionString = precisionString + ", length = " + da.getValue()
	
	if javaTypes(element.getType(),vnullable)=="Date":
		methodStream.append("\t@Temporal(TemporalType.TIMESTAMP)\n")
	methodStream.append("\t@Column(name = \"" + toDBName(element.getName()) + "\"" + uniqueString + nullString + precisionString + ")\n")
	methodStream.append("\tpublic " + javaTypes(element.getType(),vnullable) + " get" + capt(element.getName()) + "() {\n");
	methodStream.append("\t\treturn this."+element.getName()+";\n");
	methodStream.append("\t}\n\n");
	methodStream.append("\tpublic void set" + capt(element.getName()) +"(" + javaTypes(element.getType(),vnullable) + " " + element.getName() + ") {\n");
	methodStream.append("\t\tthis." + element.getName() + "=" + element.getName() + ";\n");
	methodStream.append("\t}\n\n")


def printAssoc(parel,element,attribStream,methodStream):
	if element.getMultiplicityMin()=="0":
		vnullable="true"
	else:
		vnullable="false"
	if element.getMultiplicityMax()=="1":
		attribStream.append("\tprivate " + element.getTarget().getName() +  " " + element.getName() + ";\n");
		methodStream.append("\t@ManyToOne(fetch = FetchType.LAZY)\n");
		methodStream.append("\t@JoinColumn(name = \"" + persistentRelationShipName(element) +"\", nullable = " + vnullable + ", foreignKey = @ForeignKey(name = \"fk_" + persistentName(parel)+ "_"+ persistentName(element.getTarget())+ "\"))\n");
		methodStream.append("\tpublic " + element.getTarget().getName() + " get" + capt(element.getName())+"() {\n");
		methodStream.append("\t\treturn this."+element.getName() + ";\n");
		methodStream.append("\t}\n\n");
		methodStream.append("\tpublic void set" + capt(element.getName()) + "(" + element.getTarget().getName()  + " "+element.getName()+") {\n");
		methodStream.append("\t\tthis."+element.getName()+"="+element.getName()+";\n");
		methodStream.append("\t}\n\n");
	if element.getMultiplicityMax()=="*":
		attribStream.append("\tprivate List<" + element.getTarget().getName() +  "> "+element.getName()+" = new ArrayList<"+ element.getTarget().getName() +">();\n");
		methodStream.append("\t@OneToMany(fetch = FetchType.LAZY, mappedBy = \""+element.getOpposite().getName()+"\")\n");
		methodStream.append("\tpublic List<" + element.getTarget().getName() + "> get"+capt(element.getName())+"() {\n");
		methodStream.append("\t\treturn this."+element.getName()+";\n");
		methodStream.append("\t}\n\n");
		methodStream.append("\tpublic void set"+capt(element.getName()) + "(List<" + element.getTarget().getName()  + "> "+element.getName()+") {\n");
		methodStream.append("\t\tthis."+element.getName()+"="+element.getName()+";\n");
		methodStream.append("\t}\n\n");



def make_sure_path_exists(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise



def packageFullName(element):
	pn = element.getOwner()
	fullname = pn.getName()
	while isinstance(pn.getOwner().getOwner(), Package):
		pn=pn.getOwner()
		fullname = pn.getName()+"."+fullname
	return fullname
  


projectPath=Modelio.getInstance().getContext().getProjectSpacePath().toString()
genPath=Modelio.getInstance().getModuleService().getPeerModule("JavaDesigner").getConfiguration().getParameterValue("GenerationPath")
copyPath=Modelio.getInstance().getModuleService().getPeerModule("JavaDesigner").getConfiguration().getParameterValue("CopyrightFile")
fullpath = unicode.replace(genPath,"$(Project)",projectPath)

print "-------------------"
for el in selectedElements:
	print el.getName();
	if (isinstance(el, Class)):
		pfullname = packageFullName(el)
		pathfullname = fullpath+"/"+unicode.replace(pfullname,".","/")
		print " - "+pathfullname
		make_sure_path_exists(pathfullname)
		srcFile = open( pathfullname +"/" + el.getName() + ".java", "w")
		copyFile = open(copyPath, "r")
		for line in copyFile:
			srcFile.write(line)
		copyFile.close()
		srcFile.write( "package " + pfullname + ";\n\n" )
		srcFile.write( "import java.util.*;\n" )
		srcFile.write( "import javax.persistence.*;\n\n" )
		displayNote(srcFile, el)
		displayStereotypes(srcFile, el)
		srcFile.write( "public class "+el.getName()+" implements java.io.Serializable {\n")
		attributes = []
		methods = []
		for at in el.getOwnedAttribute():
			printAttrib(at,attributes, methods)
		for at in el.getOwnedEnd():
			printAssoc(el,at,attributes, methods)
		srcFile.writelines(attributes);
		srcFile.write( "\n\n")
		srcFile.writelines(methods);
		srcFile.write( "}\n")
		srcFile.close()
print "=========================="
print fullpath
print "=========================="
