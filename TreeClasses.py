import re
class QuerySegment:
    def __init__(self):
        self.children =[]
        self.parent=None

    def __repr__(self):
        return f"{self.__class__.__name__}"
    
    def addChild(self,child):
        self.children.append(child)
        child.parent = self


class Table(QuerySegment):
    def __init__(self,tableName,alias=None):
        super().__init__()
        self.tableName =tableName
        self.alias = alias if alias else tableName

    
    def __repr__(self):
        if self.alias != self.tableName:
            return f"{self.tableName} {self.alias}"
        return self.tableName
    



class Where(QuerySegment):
    def __init__(self, condition):
        super().__init__()
        self.condition = condition
    

    def __repr__(self):
        return f"σ {self.condition}"
    
class Select(QuerySegment):
    def __init__(self, attributes):
        super().__init__()
        self.attributes = attributes
    
    def __repr__(self):
        attrs = ', '.join(self.attributes)
        return f"π {attrs}"



class CrossProduct(QuerySegment):
    def __init__(self):
        super().__init__()
    def __repr__(self):
        return "x"
class Join(QuerySegment):

    def __init__(self,condition =None):
        super().__init__()
        self.condition = condition
    def __repr__(self):
        if self.condition:
            return f"⋈ {self.condition}"
        return "⋈"
    
class QueryTree:
    def __init__(self, root=None):
        self.root = root
    
    def print_tree(self, node=None, prefix="", is_last=True):
        if node is None:
            node = self.root
        
        if node is None:
            return
        connector = "└── " if is_last else "├── "
        print(prefix + connector + str(node))
        if is_last:
            new_prefix = prefix + "    "
        else:
            new_prefix = prefix + "│   "
        


        for i, child in enumerate(node.children):
            is_last_child = (i == len(node.children) - 1)
            self.print_tree(child, new_prefix, is_last_child)
    


#creates the first tree
def canonicalTree(tables,query):
    tableNames =[]
    for table in query['from']:
        tableNames.append(Table(table['table'],table['alias']))
    currentNode = tableNames[0]
    if len(tableNames) > 1:
        #starts with the first two table to x and then it adds one at a time after for the formatiing
        currentNode = CrossProduct()
        currentNode.addChild(tableNames[0])
        currentNode.addChild(tableNames[1])
        for i in range(2, len(tableNames)):
            nextCross = CrossProduct()
            nextCross.addChild(currentNode)
            nextCross.addChild(tableNames[i])
            currentNode = nextCross
    
#add the where clause
    if query["where"]:
        finalWhere = ""
        for i, where in enumerate(query["where"]):
            finalWhere += where['condition']
            if where['operator']:
                finalWhere += f" {where['operator']} "
        where = Where(finalWhere)
        where.addChild(currentNode)
        currentNode = where

#select should be parent node
    columns = []
    for column in query['select']:
        columns.append(column['attribute'])
    select = Select(columns)
    select.addChild(currentNode)

    return QueryTree(select)

#TODO:
#WHEN IT IS LIKE OR (__AND____ AND___AND) the () needs to be one node instead of splitting them

#I apologize in advance, reading selection has always made me think of SELECT so I just say where so I dont get confused
def stepsOneTwo(tree):
    whereNode = tree.root.children[0]
    combinedWhere = whereNode.condition
    wheres = combinedWhere.split(' AND ')
#like a basic leetcode problem just removing a node and pushing them up
    crossProductRoot = whereNode.children[0]
    tree.root.children[0] = crossProductRoot
    crossProductRoot.parent = tree.root
#grab what table aliases r used in the where statement to put it in the tree where both those tables r below in the tree
    for where in wheres:
        where = where.strip()
        tablesUsed = list(set(re.findall(r'([A-Z_]+)\.', where)))
        if len(tablesUsed) ==1:
            tableNode = getTableNode(tree.root, tablesUsed[0])
            if tableNode:
                insertNode(tableNode,where)
        elif len(tablesUsed) >= 2:
            targetNode = findLowestNodeWithTables(tree.root, tablesUsed)
            if targetNode:
                insertNode(targetNode, where)
    return tree

#helper recursive search down the tree to find where I need to put the Where statements
def getTableNode(node,alias):
    if isinstance(node, Table) and node.alias == alias:
        return node
    
    for child in node.children:
        result = getTableNode(child, alias)
        if result:
            return result
    
    return None
#place node in the tree
def insertNode(tableNode, where):
    newWhere = Where(where)
    parent = tableNode.parent
    for i, child in enumerate(parent.children):
        if child == tableNode:
            parent.children[i] = newWhere
            break
    newWhere.parent = parent
    newWhere.addChild(tableNode)

#helper to find the lowest node in the tree that has the tables that the where condition has underneath it
def findLowestNodeWithTables(node, tables):

    found_here = None
    for child in node.children:
        found = findLowestNodeWithTables(child, tables)
        if found:
            return found
    if isinstance(node, CrossProduct):
        aliasesHere = getAliasesUnderNode(node)
        if all(alias in aliasesHere for alias in tables):

            found_here = node
    return found_here

#get all the tables aliases under the node
def getAliasesUnderNode(node):
    aliases = set()
    if isinstance(node, Table):
        aliases.add(node.alias)
        
    for child in node.children:
        aliases.update(getAliasesUnderNode(child))
    return aliases

def step3(tree,tables,query):
    wheres = []
    getWheres(tree.root,wheres)
    aliasMap = {}
    for table in query['from']:
            aliasMap[table['alias']] = table['table']
    wheres = whereSelectivityOrder(wheres,tables,aliasMap)

    whereNodes = []
    xParents = []
    #grab the tables in the where condition to find where to place it in the tree
    for where in wheres:
        tablesUsed = list(set(re.findall(r'([A-Z_]+)\.', where.condition)))
        if len(tablesUsed) == 1:
            whereNodes.append(where)
        else:
            xParents.append(where)
    for where in whereNodes:
        removeWhereNode(where)
    #insert node where the table node is with the where
    for where in whereNodes:
        tablesUsed = re.findall(r'([A-Z_]+)\.', where.condition)
        tableNode = getTableNode(tree.root, tablesUsed[0])
        if tableNode:
            insertNode(tableNode, where.condition)
    
    return tree

#best is = with pk then = with unique then just =
#then any range
#then any disjunctive condition
def selectivity(where,tables,aliasMap):
    condition = re.search(r'([A-Z_]+)\.([A-Z_]+)',where)
    alias = condition.group(1)
    attribute = condition.group(2)
    if 'OR' in where.upper():
        return 5
    tableName = aliasMap.get(alias, alias)
    tableSchema = None
    for table in tables:
        if table['name'] == tableName:
            tableSchema = table
            break
    if '=' in where and '>' not in where and '<' not in where and '!' not in where:
        if attribute in tableSchema['primaryKeys']:
            return 1
        if attribute in tableSchema['uniqueKeys']:
            return 2
        return 3
    if '<>' in where:
        return 5
    
    return 4
    


#just ordering them so I can move the the most selective ones first
def whereSelectivityOrder(wheres,tables,aliasMap):
    for where in wheres:
        where.selectivity = selectivity(where.condition,tables,aliasMap)
    wheres.sort(key=lambda w: w.selectivity)
    return wheres


def getWheres(node,wheres):
    if isinstance(node,Where):
        wheres.append(node)
    for child in node.children:
        getWheres(child,wheres)



def removeWhereNode(whereNode):
    child = whereNode.children[0] if whereNode.children else None
    parent = whereNode.parent
    

    for i, c in enumerate(parent.children):
        if c == whereNode:
            
            parent.children[i] = child
            child.parent = parent
            break
    whereNode.parent = None
    whereNode.children = []
#turn into joins which was actully 100x easier than the others
def step4(tree):
    crossProducts = []
    findCrossProducts(tree.root,crossProducts)
    for x in crossProducts:
        #going to assume my earlier code works right so any parent of a x that is a where should be good to go
        if isinstance(x.parent,Where):
            #swap out x for join and make sure parents and children transfer right
            condition = x.parent.condition
            join = Join(condition)
            whereParent = x.parent.parent
            whereParent.children[0] = join
            join.parent = whereParent
            join.children = x.children[:]
            for child in join.children:
                child.parent = join

    return tree
            
            



#helper step4 recursive search thru tree for x
def findCrossProducts(node, crossProducts):
    if isinstance(node, CrossProduct):
        crossProducts.append(node)
    for child in node.children:
        findCrossProducts(child, crossProducts)


#so i realized i need to combine the wheres
def combineWheres(node):
    if not node.children:
        return
    while isinstance(node,Where) and isinstance(node.children[0],Where):
        child = node.children[0]
        combinedWhere = f"({node.condition}) AND ({child.condition})"
        node.condition = combinedWhere

        node.children = child.children
        for parent in node.children:
            parent.parent = node
        
    for child in node.children:
        combineWheres(child)

