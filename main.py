import copy
from QueryParser import parseFile
from TreeClasses import canonicalTree, stepsOneTwo, step3,step4,combineWheres,step5,optimizedSqlQuery


# Parse input
tables, query = parseFile('input2.txt')

# Build canonical tree

print("Canonical Tree")
print()
tree = canonicalTree(tables, query)
tree.print_tree()
#i start copying the tree to merge all the where conditions into one line so its easier to read
print()
print("Step 1 and 2 Cascade of selections and push selections down")
print()
tree = stepsOneTwo(tree)
treecopy = copy.deepcopy(tree)
combineWheres(treecopy.root)
treecopy.print_tree()

print()
print("Step 3 selections with smallest selectivity")
print()

tree = step3(tree, tables, query)
treecopy = copy.deepcopy(tree)
combineWheres(treecopy.root)
treecopy.print_tree()
print()
print("Step 4 Replace x with Joins")
print()
tree = step4(tree)
treecopy = copy.deepcopy(tree)
combineWheres(treecopy.root)
treecopy.print_tree()

print()
print("Step 5 push projections Down")
print()
combineWheres(tree.root)
tree = step5(tree)


tree.print_tree()
print()
print("Optimimzed Query for ec")

print()
print(optimizedSqlQuery(tree,query))


