#!/usr/bin/env python3
"""Test script to verify timber joining functionality."""

import sqlite3
import sys
from pathlib import Path

# Add the parent directory to the path so we can import the app
sys.path.append(str(Path(__file__).parent))

from wood_cut_calc.cutting_algorithms import generate_basic_plan


def test_joining():
    """Test the timber joining functionality."""
    
    # Get the cut that needs joining
    conn = sqlite3.connect('wood_cut_calc.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get the 90x90x2400 cut
    cursor.execute("SELECT * FROM cuts WHERE id = 34")
    cut = cursor.fetchone()
    
    if not cut:
        print("Cut not found!")
        return
        
    cuts = [dict(cut)]
    print(f"Cut requirements: {cuts[0]['length']}x{cuts[0]['width']}x{cuts[0]['depth']}")
    print(f"Allow joining: {cuts[0]['allow_joining']}")
    
    # Get all inventory
    cursor.execute("SELECT * FROM inventory")
    inventory = [dict(row) for row in cursor.fetchall()]
    
    # Filter to relevant inventory (90x45x2400 pieces)
    relevant_inventory = [item for item in inventory 
                         if item['length'] == 2400 and item['width'] == 90 and item['height'] == 45]
    
    print(f"Relevant inventory items: {len(relevant_inventory)}")
    for item in relevant_inventory:
        print(f"  - {item['product_name']}: {item['length']}x{item['width']}x{item['height']} @ ${item['price']}")
    
    # Test with joining enabled
    print("\n=== Testing WITH joining enabled ===")
    result = generate_basic_plan(cuts, inventory, allow_joining=True)
    
    if result.get('solutions'):
        solution = result['solutions'][0]
        print(f"Total cost: ${solution['total_cost']:.2f}")
        if 'material_cost' in solution:
            print(f"Material cost: ${solution['material_cost']:.2f}")
            print(f"Shipping cost: ${solution['shipping_cost']:.2f}")
        
        print("Shopping list:")
        for item_id, item_data in solution['shopping_list'].items():
            item = item_data['item']
            print(f"  - {item.get('product_name', 'Unknown')}: {item_data['quantity']}x @ ${item_data['total_price']:.2f}")
            print(f"    Dimensions: {item['length']}x{item['width']}x{item.get('height', item.get('depth'))}")
            if item.get('is_joined'):
                print(f"    *** This is a VIRTUAL joined piece ***")
                print(f"    Base item ID: {item.get('base_item_id')}")
                print(f"    Pieces needed: {item.get('pieces_needed')}")
                print(f"    Join direction: {item.get('join_direction')}")
    else:
        print("No solutions found!")
    
    # Test with joining disabled
    print("\n=== Testing WITHOUT joining enabled ===")
    result_no_join = generate_basic_plan(cuts, inventory, allow_joining=False)
    
    if result_no_join.get('solutions'):
        solution = result_no_join['solutions'][0]
        print(f"Total cost: ${solution['total_cost']:.2f}")
        print("Shopping list:")
        for item_id, item_data in solution['shopping_list'].items():
            item = item_data['item']
            print(f"  - {item.get('product_name', 'Unknown')}: {item_data['quantity']}x @ ${item_data['total_price']:.2f}")
    else:
        print("No solutions found without joining!")
    
    conn.close()

if __name__ == "__main__":
    test_joining()
