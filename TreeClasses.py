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
    #had to get some help on this one https://stackoverflow.com/questions/20242479/printing-a-tree-data-structure-in-python
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
    #starts with the first two table to x and then it adds one at a time after for the formatiing
    if len(tableNames) > 1:
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

                finalWhere +=f" {where['operator']} "
        where = Where(finalWhere)
        where.addChild(currentNode)
        currentNode= where
#select should be parent node
    columns = []
    for column in query['select']:
        if 'function' in column:
            columns.append(f"{column['function']}({column['argument']})")
            
        elif 'table' in column and column['table']:

            columns.append(f"{column['table']}.{column['attribute']}")
        else:
            columns.append(column['attribute'])
    select =Select(columns)
    select.addChild(currentNode)

    return QueryTree(select)
#TODO:
#WHEN IT IS LIKE OR (__AND____ AND___AND) the () needs to be one node instead of splitting them do not forget pls

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
        where =where.strip()
        tablesUsed = list(set(re.findall(r'([A-Za-z_]+)\.', where, re.IGNORECASE)))
        if len(tablesUsed) ==1:
            tableNode = getTableNode(tree.root, tablesUsed[0])
            if tableNode:

                insertNode(tableNode,where)
        elif len(tablesUsed)>= 2:
            targetNode = findLowestNodeWithTables(tree.root, tablesUsed)


            if targetNode:
                insertNode(targetNode, where)
    return tree

#helper recursive search down the tree to find where I need to put the Where statements
def getTableNode(node,alias):
    if isinstance(node, Table) and node.alias.upper() == alias.upper():
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


#this could not have possibly taken more trial and error
def step3(tree, tables, query):
    wheres = []
    getWheres(tree.root, wheres)
    aliasMap = {}
    for table in query['from']:
        aliasMap[table['alias'].upper()] = table['table'].upper()
    
    #get all the wheres in the tree and categorize
    singleTableWheres = []
    multiTableWheres = []
    
    for where in wheres:
        tablesUsed = list(set(re.findall(r'([A-Za-z_]+)\.', where.condition, re.IGNORECASE)))

        if len(tablesUsed) == 1:

            singleTableWheres.append(where)
        else:
            multiTableWheres.append(where)
    
#selectivbity
    for where in singleTableWheres:
        where.selectivity = selectivity(where.condition, tables, aliasMap)
    singleTableWheres.sort(key=lambda w: w.selectivity)
    
    #all the single table ones dont matter for now when reorganizing
    for where in singleTableWheres:
        removeWhereNode(where)
    


    tableNodes = []
    collectTableNodes(tree.root, tableNodes)
    
    aliasToTable = {}
    for tableNode in tableNodes:
        aliasToTable[tableNode.alias.upper()] = tableNode
    #start to rebuild tree but start with the ones who have the best selectivity where condtions so the joins are in the right spot
    if singleTableWheres:
        tablesUsed = re.findall(r'([A-Za-z_]+)\.', singleTableWheres[0].condition, re.IGNORECASE)
        startAlias = tablesUsed[0].upper()
        startTable = aliasToTable[startAlias]
    else:
        startTable = tableNodes[0]
    usedTables = {startTable}
    currentNode = startTable
    

    remainingTables = [table for table in tableNodes if table not in usedTables]
    
    while remainingTables:
        nextTable = None
        
        #find the order of tables to join off of
        for where in multiTableWheres:
            #basically checks all the where conditions, if they have 2 tables in it, then check if one of them has already been placed in the tree
            #if it has then add it to that one
            #else save it later
            tablesInJoin = list(set(re.findall(r'([A-Za-z_]+)\.', where.condition, re.IGNORECASE)))
            tablesInJoinUpper = [t.upper() for t in tablesInJoin]
            
            usedAliases = {t.alias.upper() for t in usedTables}

            remainingAliases = {t.alias.upper() for t in remainingTables}
            hasUsed = any(alias in usedAliases for alias in tablesInJoinUpper)
            hasRemaining = any(alias in remainingAliases for alias in tablesInJoinUpper)
            
            #handles if one of the tables has already been placed
            if hasUsed and hasRemaining:
                for alias in tablesInJoinUpper:
                    if alias in remainingAliases:
                        nextTable = aliasToTable[alias]
                        break
                if nextTable:
                    break
        if not nextTable:
            nextTable = remainingTables[0]
        
        #add that table to tree
        newCross = CrossProduct()
        newCross.addChild(currentNode)
        newCross.addChild(nextTable)
        currentNode = newCross
        usedTables.add(nextTable)
        remainingTables.remove(nextTable)
    tree.root.children[0] = currentNode
    currentNode.parent = tree.root
    
    #place back all the extra wheres
    for where in singleTableWheres:
        tablesUsed = re.findall(r'([A-Za-z_]+)\.', where.condition, re.IGNORECASE)
        alias = tablesUsed[0].upper()
        if alias in aliasToTable:
            tableNode = aliasToTable[alias]
            insertNode(tableNode, where.condition)
    for where in multiTableWheres:
        tablesUsed = list(set(re.findall(r'([A-Za-z_]+)\.', where.condition, re.IGNORECASE)))
        targetNode = findLowestNodeWithTables(tree.root, tablesUsed)
        if targetNode:
            insertNode(targetNode, where.condition)
    
    return tree



def collectTableNodes(node, tableNodes):
    if isinstance(node, Table):
        tableNodes.append(node)
    for child in node.children:
        collectTableNodes(child, tableNodes)

#best is = with pk then = with unique then just =
#then any range
#then any disjunctive condition
def selectivity(where, tables, aliasMap):
    condition = re.search(r'([A-Za-z_]+)\.([A-Za-z_]+)', where, re.IGNORECASE)
    if not condition:
        return 5
    
    alias = condition.group(1).upper()
    attribute = condition.group(2).upper()
    if 'OR' in where.upper():
        return 5
    tableName = aliasMap.get(alias, alias)
    tableSchema = None
    
    for table in tables:
        if table['name'].upper() == tableName.upper():
            tableSchema = table
            break
    
    if not tableSchema:
        return 5
    
    primaryKeys = [k.upper() for k in tableSchema['primaryKeys']]
    uniqueKeys = [k.upper() for k in tableSchema['uniqueKeys']]
    
    if '=' in where and '>' not in where and '<' not in where and '!' not in where:
        if attribute in primaryKeys:
            return 1
        if attribute in uniqueKeys:
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
    changed = True
    while changed:
        changed = False
        crossProducts = []
        findCrossProducts(tree.root, crossProducts)
        
        for x in crossProducts:
            if isinstance(x.parent, Where):
                condition = x.parent.condition
                join = Join(condition)
                whereParent = x.parent.parent
                
                for i, child in enumerate(whereParent.children):
                    if child == x.parent:
                        whereParent.children[i] = join
                        break
                
                join.parent = whereParent
                join.children = x.children[:]
                for child in join.children:
                    child.parent = join
                
                changed = True
                break
        
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
        for grandchild in node.children:
            grandchild.parent = node
        
    for child in node.children:
        combineWheres(child)


def step5(tree):
    finalAttributes = set(a for a in tree.root.attributes)
    #check if its an agg
    for attr in tree.root.attributes:
        if '(' in attr and ')' in attr:
            argMatch = re.search(r'\(([^)]+)\)', attr)
            if argMatch:
                argument = argMatch.group(1)
                finalAttributes.add(argument)
        else:
            finalAttributes.add(attr)
    addProjectionsDownTree(tree.root, finalAttributes)
    return tree

#helper for step 5 to add the attributes down the tree from where the node it is needed
def addProjectionsDownTree(node, attributes):
    if isinstance(node, Join):
        joinAtts = set()
        
        attrInCondit = re.findall(r'(\w+\.\w+)', node.condition)
        for attr in attrInCondit:
            joinAtts.add(attr)
     
        
        for child in node.children:
            childTables = getAliasesUnderNode(child)
            attributesToAdd = set()
            for attr in attributes:
                parts = attr.split('.')
                if len(parts) == 2:
                    tableAlias = parts[0]
                    if any(tableAlias.upper() == t.upper() for t in childTables):
                        attributesToAdd.add(attr)
            

            for attr in joinAtts:
                parts = attr.split('.')
                if len(parts) == 2:
                    tableAlias = parts[0]
                    if any(tableAlias.upper() == t.upper() for t in childTables):
                        attributesToAdd.add(attr)
            insertProjection(child, attributesToAdd)
    
    if isinstance(node, Where):
        if node.children and not isinstance(node.children[0], Table):
            whereAtts = set()
            attrInCondit = re.findall(r'(\w+\.\w+)', node.condition)
            for attr in attrInCondit:
                whereAtts.add(attr)
            
            childTables = getAliasesUnderNode(node.children[0])
            attributesToAdd = set()
            for attr in whereAtts:
                parts = attr.split('.')
                if len(parts) == 2:
                    tableAlias = parts[0]
                    if any(tableAlias.upper() == t.upper() for t in childTables):
                        attributesToAdd.add(attr)
            
            if attributesToAdd:
                insertProjection(node.children[0], attributesToAdd)
    
    for child in node.children:
        addProjectionsDownTree(child, attributes)




def insertProjection(child, attributesToAdd):
    if isinstance(child, Select):
        return
    projection = Select(list(attributesToAdd))
    for i, pChild in enumerate(child.parent.children):
        if pChild == child:
            child.parent.children[i] = projection
            break
    
    projection.parent = child.parent
    projection.addChild(child)




def collectWhereAttributesFromSubtree(node):
    attributes = set()
    
    if isinstance(node, Where):
        whereAtts = set()

        attrInCondit = re.findall(r'(\w+\.\w+)', node.condition)
        for attr in attrInCondit:
            whereAtts.add(attr)
        attributes.update(whereAtts)
    
    for child in node.children:
        attributes.update(collectWhereAttributesFromSubtree(child))
    
    return attributes

def optimizedSqlQuery(tree, query):

    select_clause = "SELECT " + ", ".join(tree.root.attributes)
    from_clause ="FROM " +buildFromWithJoins(tree.root.children[0])

    from_clause = from_clause.replace("(", "").replace(")", "")
    wheres = []


    getWheres(tree.root, wheres)
    where_clause =""
    if wheres:
        where_clause = "WHERE "+ " AND ".join([w.condition for w in wheres])
    
    clauses = [select_clause, from_clause]
    if where_clause:
        clauses.append(where_clause)
    if query['groupBy']:

        clauses.append("GROUP BY " + ", ".join(query['groupBy']))
    if query['having']:
        clauses.append("HAVING " + query['having'])
    if query['orderBy']:
        order_parts = [f"{o['attribute']} {o['direction']}" for o in query['orderBy']]
        clauses.append("ORDER BY " + ", ".join(order_parts))

    
    return "\n".join(clauses) + ";"

def buildFromWithJoins(node):
    
    if isinstance(node, Table):
        if node.alias != node.tableName:
            return f"{node.tableName} {node.alias}"
        
        return node.tableName
    if isinstance(node, Join):
        left= buildFromWithJoins(node.children[0])

        right =buildFromWithJoins(node.children[1])
        return f"{left}\nJOIN {right} ON {node.condition}"
    if isinstance(node,CrossProduct):
        left = buildFromWithJoins(node.children[0])

        right = buildFromWithJoins( node.children[1])

        return f"{left}\nCROSS JOIN { right}"
    


    if isinstance(node, Select) or isinstance(node, Where):
        return buildFromWithJoins(node.children[0])
    



