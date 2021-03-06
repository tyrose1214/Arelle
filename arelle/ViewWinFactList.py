'''
Created on Oct 5, 2010

@author: Mark V Systems Limited
(c) Copyright 2010 Mark V Systems Limited, All rights reserved.
'''
from arelle import ViewWinTree, ModelDtsObject, XbrlConst

def viewFacts(modelXbrl, tabWin, lang=None):
    modelXbrl.modelManager.showStatus(_("viewing facts"))
    view = ViewFactList(modelXbrl, tabWin, lang)
    view.treeView["columns"] = ("sequence", "contextID", "unitID", "decimals", "precision", "language", "value")
    view.treeView.column("#0", width=200, anchor="w")
    view.treeView.heading("#0", text=_("Label"))
    view.treeView.column("sequence", width=40, anchor="e", stretch=False)
    view.treeView.heading("sequence", text=_("Seq"))
    view.treeView.column("contextID", width=100, anchor="w", stretch=False)
    view.treeView.heading("contextID", text="contextRef")
    view.treeView.column("unitID", width=75, anchor="w", stretch=False)
    view.unitDisplayID = False # start displaying measures
    view.treeView.heading("unitID", text="Unit")
    view.treeView.column("decimals", width=50, anchor="center", stretch=False)
    view.treeView.heading("decimals", text=_("Dec"))
    view.treeView.column("precision", width=50, anchor="w", stretch=False)
    view.treeView.heading("precision", text=_("Prec"))
    view.treeView.column("language", width=36, anchor="w", stretch=False)
    view.treeView.heading("language",text=_("Lang"))
    view.treeView.column("value", width=200, anchor="w", stretch=False)
    view.treeView.heading("value", text=_("Value"))
    view.treeView["displaycolumns"] = ("sequence", "contextID", "unitID", "decimals", "precision", \
                                       "language", "value")
    view.blockSelectEvent = 1
    view.blockViewModelObject = 0
    view.view()
    view.treeView.bind("<<TreeviewSelect>>", view.treeviewSelect, '+')
    view.treeView.bind("<Enter>", view.treeviewEnter, '+')
    view.treeView.bind("<Leave>", view.treeviewLeave, '+')

    # intercept menu click before pops up to set the viewable tuple (if tuple clicked)
    view.treeView.bind( view.modelXbrl.modelManager.cntlr.contextMenuClick, view.setViewTupleChildMenuItem, '+' )
    menu = view.contextMenu()
    if menu is not None:
        view.menu.insert_cascade(0, label=_("View Tuple Children"), underline=0, command=view.viewTuplesGrid)
        view.menu.entryconfigure(0, state='disabled')
        view.menuAddExpandCollapse()
        view.menuAddClipboard()
        view.menuAddLangs()
        view.menuAddLabelRoles(includeConceptName=True)
        view.menuAddUnitDisplay()
    
class ViewFactList(ViewWinTree.ViewTree):
    def __init__(self, modelXbrl, tabWin, lang):
        super(ViewFactList, self).__init__(modelXbrl, tabWin, "Fact List", True, lang)
        
    def setViewTupleChildMenuItem(self, event=None):
        if event is not None and self.menu is not None:
            #self.menu.delete(0, 0) # remove old filings
            menuRow = self.treeView.identify_row(event.y) # this is the object ID
            modelFact = self.modelXbrl.modelObject(menuRow)
            if modelFact is not None and modelFact.isTuple:
                self.menu.entryconfigure(0, state='normal')
                self.viewedTupleId = menuRow
            else:
                self.menu.entryconfigure(0, state='disabled')
                self.viewedTupleId = None
                
    def viewTuplesGrid(self):
        from arelle.ViewWinTupleGrid import viewTuplesGrid
        viewTuples = viewTuplesGrid(self.modelXbrl, self.tabWin, self.viewedTupleId, self.lang)
        self.modelXbrl.modelManager.showStatus(_("Ready..."), clearAfter=2000)
        viewTuples.select()  # bring new grid to foreground
                
    def view(self):
        self.id = 1
        self.tag_has = {}
        for previousNode in self.treeView.get_children(""): 
            self.treeView.delete(previousNode)
        self.setColumnsSortable(initialSortCol="sequence")
        self.viewFacts(self.modelXbrl.facts, "", 1)
        
    def viewFacts(self, modelFacts, parentNode, n):
        for modelFact in modelFacts:
            try:
                concept = modelFact.concept
                if concept is not None:
                    lbl = concept.label(self.labelrole, lang=self.lang, linkroleHint=XbrlConst.defaultLinkRole)
                    objectIds = (modelFact.objectId(),concept.objectId())
                else:
                    lbl = modelFact.qname
                    objectIds = (modelFact.objectId())
                node = self.treeView.insert(parentNode, "end", modelFact.objectId(self.id), 
                                            text=lbl,
                                            tags=("odd" if n & 1 else "even",))
                for tag in objectIds:
                    self.tag_has.setdefault(tag,[]).append(node)
                self.treeView.set(node, "sequence", str(self.id))
                if concept is not None and not modelFact.concept.isTuple:
                    self.treeView.set(node, "contextID", modelFact.contextID)
                    if modelFact.unitID:
                        self.treeView.set(node, "unitID", modelFact.unitID if self.unitDisplayID else modelFact.unit.value)
                    self.treeView.set(node, "decimals", modelFact.decimals)
                    self.treeView.set(node, "precision", modelFact.precision)
                    self.treeView.set(node, "language", modelFact.xmlLang)
                    self.treeView.set(node, "value", modelFact.effectiveValue.strip())
                self.id += 1;
                n += 1
                self.viewFacts(modelFact.modelTupleFacts, node, n)
            except AttributeError:  # not a fact or no concept
                pass

    def treeviewEnter(self, *args):
        self.blockSelectEvent = 0

    def treeviewLeave(self, *args):
        self.blockSelectEvent = 1

    def treeviewSelect(self, *args):
        if self.blockSelectEvent == 0 and self.blockViewModelObject == 0:
            self.blockViewModelObject += 1
            self.modelXbrl.viewModelObject(self.treeView.selection()[0])
            self.blockViewModelObject -= 1
        
    def viewModelObject(self, modelObject):
        if self.blockViewModelObject == 0:
            self.blockViewModelObject += 1
            try:
                if isinstance(modelObject, ModelDtsObject.ModelRelationship):
                    conceptId = modelObject.toModelObject.objectId()
                else:
                    conceptId = modelObject.objectId()
                #items = self.treeView.tag_has(conceptId)
                items = self.tag_has.get(conceptId,[])
                if len(items) > 0 and self.treeView.exists(items[0]):
                    self.treeView.see(items[0])
                    self.treeView.selection_set(items[0])
            except (AttributeError, KeyError):
                    self.treeView.selection_set(())
            self.blockViewModelObject -= 1
       
