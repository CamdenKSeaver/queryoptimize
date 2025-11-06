from QueryParser import parseFile
from TreeClasses import canonicalTree, stepsOneTwo, step3

# Parse input
tables, query = parseFile('input1.txt')

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
tree.print_tree()

# Apply step 3
print("\n" + "=" * 60)
print("AFTER STEP 3 (Reorder by selectivity):")
print("=" * 60)
tree = step3(tree, tables, query)  
tree.print_tree()

print("\n✅ Done!")