import re

def parseFile(filename):
    file =open(filename, 'r', encoding='utf-8')
    content =file.read()
    file.close()
    
    allLines= content.split('\n')
    linesWithoutComments = []
    for line in allLines:
        if not line.strip().startswith('--'):
            linesWithoutComments.append(line)
    content ='\n'.join(linesWithoutComments)
    
    parts = content.split('SELECT')
    schemaPart =parts[0]
    
    tables = []
    
    
    i = 0
    while i < len(schemaPart):
        # Find next table name
        tableNameIndex = re.search(r'(\w+)\s*\(',schemaPart[i:])
        if not tableNameIndex:
            break
        # This was actually like the hardest part
        #i seperated the tables by counting the parenthesis since pks and uniques also have () next to them, this was like the 4th method I thought of trying to do
        # Get start position
        tableStart = i + tableNameIndex.start()
        openParenIdx = schemaPart.find('(', tableStart)
        
        #Count parentheses 
        #adds 1 when ( and subtracts 1 when ) 
        #when it reaches 0 it must be the closing ) for the table
        parenCount= 0
        closeParenIdx = openParenIdx
        for j in range(openParenIdx, len(schemaPart)):
            if schemaPart[j] == '(':
                parenCount+= 1
            elif schemaPart[j] ==')':
                parenCount -=1
                if parenCount== 0:
                    closeParenIdx = j
                    break
        
        #grab the whole section of the one table
        tableDefinition= schemaPart[tableStart:closeParenIdx+ 1]
        
        startParen = tableDefinition.find('(')
        tableName = tableDefinition[:startParen].strip()
        
        endParen = tableDefinition.rfind(')')
        tableContent = tableDefinition[startParen+1:endParen]
        #just regex for the pks and uniques for each table
        primaryKeys = []
        primaryKeyMatch = re.search(r'PRIMARY\s+KEY\s*\(([^)]+)\)', tableContent, re.IGNORECASE)
        if primaryKeyMatch:
            keysString = primaryKeyMatch.group(1)
            keysList = keysString.split(',')
            for key in keysList:
                primaryKeys.append(key.strip())
            tableContent = re.sub(r',?\s*PRIMARY\s+KEY\s*\([^)]+\)', '', tableContent, flags=re.IGNORECASE)
        
        uniqueKeys = []
        uniqueKeyMatch = re.search(r'UNIQUE\s*\(([^)]+)\)', tableContent, re.IGNORECASE)
        if uniqueKeyMatch:
            keysString = uniqueKeyMatch.group(1)
            keysList = keysString.split(',')
            for key in keysList:
                uniqueKeys.append(key.strip())
            tableContent = re.sub(r',?\s*UNIQUE\s*\([^)]+\)', '', tableContent, flags=re.IGNORECASE)
        
        #grab each attribute from comma seperated syntasx
        attributes = []
        attributeList = tableContent.split(',')
        for attribute in attributeList:
            cleanAttribute = attribute.strip()
            if cleanAttribute:
                attributes.append(cleanAttribute)
        
        tableInfo = {
            'name': tableName,
            'attributes': attributes,
            'primaryKeys': primaryKeys,
            'uniqueKeys': uniqueKeys
        }
        tables.append(tableInfo)
        
        #set the index to the end of the table I just did
        i = closeParenIdx + 1
    
    query = parseQuery(content)
    
    return tables, query







def parseQuery(content):

    selectIndex = content.upper().find('SELECT')
    queryPart = content[selectIndex:]
    query = {
        'select': [],
        'from': [],
        'where': [],
        'groupBy': None,
        'having': None,
        'orderBy': None
    }
    


    
    whereIdx = queryPart.upper().find('WHERE')
    groupByIdx = queryPart.upper().find('GROUP BY')
    havingIdx = queryPart.upper().find('HAVING')
    orderByIdx = queryPart.upper().find('ORDER BY')
    

    fromIdx = queryPart.upper().find('FROM')
    selectClause = queryPart[6:fromIdx].strip() 
    #grab all the attributes should be separted by commas
    selectParts = selectClause.split(',')
    for part in selectParts:
        part = part.strip()
        
        if '(' in part and ')' in part:
            funcStart = part.find('(')
            funcName = part[:funcStart].strip()
            argStart = part.find('(') + 1
            argEnd = part.find(')')
            argument = part[argStart:argEnd].strip()
            
            query['select'].append({
                'function': funcName,
                'argument': argument
            })
        else:
            if '.' in part:
                dotIdx = part.find('.')
                tablePart = part[:dotIdx].strip()
                attrPart = part[dotIdx+1:].strip()
                query['select'].append({
                    'table': tablePart,
                    'attribute': attrPart
                })
            else:
                query['select'].append({
                    'table': None,
                    'attribute': part
                })
    
#grab from the from to the where
    fromStart = fromIdx + 4
    if whereIdx != -1:
        fromEnd = whereIdx
    elif groupByIdx != -1:
        fromEnd = groupByIdx
    elif orderByIdx != -1:
        fromEnd = orderByIdx
    else:
        fromEnd = len(queryPart)
    
    fromClause = queryPart[fromStart:fromEnd].strip()
    fromParts = fromClause.split(',')
    #grab each alias and table for each schema
    for part in fromParts:
        part = part.strip()
        tokens = part.split()
        if len(tokens) == 2:
            query['from'].append({
                'table': tokens[0],
                'alias': tokens[1]
            })
        elif len(tokens) == 1:
            query['from'].append({
                'table': tokens[0],
                'alias': tokens[0]
            })
    
    if whereIdx != -1:
        whereStart = whereIdx + 5
        if groupByIdx != -1:
            whereEnd = groupByIdx
        elif havingIdx != -1:
            whereEnd = havingIdx
        elif orderByIdx != -1:
            whereEnd = orderByIdx
        else:
            whereEnd = len(queryPart)
        
        whereClause = queryPart[whereStart:whereEnd].strip()
        if whereClause.endswith(';'):
            whereClause = whereClause[:-1].strip()
        whereClause = ' '.join(whereClause.split())
        

        whereUpper = whereClause.upper()
        conditions = []
        lastIdx = 0
        
        while lastIdx < len(whereClause):
            andIdx = whereUpper.find(' AND ', lastIdx)
            orIdx = whereUpper.find(' OR ', lastIdx)
            
            if andIdx == -1 and orIdx == -1:
                conditions.append({
                    'condition': whereClause[lastIdx:].strip(),
                    'operator': None
                })
                break
            elif andIdx == -1:
                conditions.append({
                    'condition': whereClause[lastIdx:orIdx].strip(),
                    'operator': 'OR'
                })
                lastIdx = orIdx + 4 
            elif orIdx == -1:
                conditions.append({
                    'condition': whereClause[lastIdx:andIdx].strip(),
                    'operator': 'AND'
                })
                lastIdx = andIdx + 5
            else:
                if andIdx < orIdx:
                    conditions.append({
                        'condition': whereClause[lastIdx:andIdx].strip(),
                        'operator': 'AND'
                    })
                    lastIdx = andIdx + 5
                else:
                    conditions.append({
                        'condition': whereClause[lastIdx:orIdx].strip(),
                        'operator': 'OR'
                    })
                    lastIdx = orIdx + 4
        
        query['where'] = conditions
#group by parse
    if groupByIdx != -1:
        groupByStart = groupByIdx + 8 
        if havingIdx != -1:
            groupByEnd = havingIdx
        elif orderByIdx != -1:
            groupByEnd = orderByIdx
        else:
            groupByEnd = len(queryPart)
        
        groupByClause = queryPart[groupByStart:groupByEnd].strip()
        if groupByClause.endswith(';'):
            groupByClause = groupByClause[:-1].strip()
        
        columns = groupByClause.split(',')
        query['groupBy'] = [col.strip() for col in columns]
    #having parse
    if havingIdx != -1:
        havingStart = havingIdx + 6 
        if orderByIdx != -1:
            havingEnd = orderByIdx
        else:
            havingEnd = len(queryPart)
        
        havingClause = queryPart[havingStart:havingEnd].strip()
        if havingClause.endswith(';'):
            havingClause = havingClause[:-1].strip()
        
        query['having'] = havingClause
    
#order by parse
    if orderByIdx != -1:
        orderByStart = orderByIdx + 8
        orderByEnd = len(queryPart)
        
        orderByClause = queryPart[orderByStart:orderByEnd].strip()
        if orderByClause.endswith(';'):
            orderByClause = orderByClause[:-1].strip()
        
        orderByParts = orderByClause.split(',')
        query['orderBy'] = []
        
        for part in orderByParts:
            part = part.strip()
            if 'DESC' in part.upper():
                attribute = part.replace('DESC', '').replace('desc', '').strip()
                query['orderBy'].append({
                    'attribute': attribute,
                    'direction': 'DESC'
                })
            elif 'ASC' in part.upper():
                attribute = part.replace('ASC', '').replace('asc', '').strip()
                query['orderBy'].append({
                    'attribute': attribute,
                    'direction': 'ASC'
                })
        #should be defaulted to asc
            else:
                query['orderBy'].append({
                    'attribute': part,
                    'direction': 'ASC'
                })
    
    return query

tables, query = parseFile('input1.txt')

