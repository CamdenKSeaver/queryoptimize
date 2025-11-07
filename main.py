import copy
from QueryParser import parseFile
from TreeClasses import canonicalTree, stepsOneTwo, step3,step4,combineWheres


# Parse input
tables, query = parseFile('input2.txt')

# Build canonical tree
print("=" * 60)
print("CANONICAL TREE:")
print("=" * 60)
tree = canonicalTree(tables, query)
tree.print_tree()

# Apply steps 1 & 2
print("\n" + "=" * 60)
print("AFTER STEPS 1 & 2 (Push selections down):")
print("=" * 60)
tree = stepsOneTwo(tree)
treecopy = copy.deepcopy(tree)
combineWheres(treecopy.root)
treecopy.print_tree()

# Apply step 3
print("\n" + "=" * 60)
print("AFTER STEP 3 (Reorder by selectivity):")
print("=" * 60)
tree = step3(tree, tables, query)  
combineWheres(tree.root)
tree.print_tree()

# Apply step 4
print("\n" + "=" * 60)
print("AFTER STEP 4 (Replace Cross Product + Selection with Join):")
print("=" * 60)
tree = step4(tree)
tree.print_tree()


