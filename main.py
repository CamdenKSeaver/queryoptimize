"""
Test canonicalTree with input1.txt
"""

from QueryParser import parseFile
from TreeClasses import canonicalTree,stepsOneTwo

# Parse the input file
print("Parsing input1.txt...\n")
tables, query = parseFile('input1.txt')

# Build canonical tree
print("Building canonical tree...\n")
tree = canonicalTree(tables, query)

print("\n" + "=" * 60)
print("CANONICAL TREE:")
print("=" * 60)
canonical = canonicalTree(tables, query)
canonical.print_tree()

print("\n" + "=" * 60)
print("AFTER STEPS ONE & TWO:")
print("=" * 60)
stepsOneTwo(canonical)
canonical.print_tree()

print("\n✅ Done! Check canonical_tree.png")