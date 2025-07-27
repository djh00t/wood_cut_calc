#!/usr/bin/env python3
"""Test the joining algorithm fix."""

def ceiling_divide(a, b):
    """Integer ceiling division."""
    return int(-(-a // b))

def _can_join_pieces_simple(cut, inventory):
    """Simplified version of the joining function for testing."""
    joining_options = []
    
    required_length = cut['length']
    required_width = cut['width'] 
    required_depth = cut['depth']
    
    for item in inventory:
        item_length = item.get('length', 0)
        item_width = item.get('width', 0) 
        item_depth = item.get('depth', item.get('height', 0))
        
        print(f"\nTesting item {item['id']}: {item_length}×{item_width}×{item_depth}")
        print(f"Required: {required_length}×{required_width}×{required_depth}")
        
        # Check if we can join pieces along width dimension
        if (item_length >= required_length and
            item_depth >= required_depth):
            
            print(f"  ✓ Length and depth constraints satisfied")
            
            # Round up to ensure we have enough material
            pieces_needed_rounded = ceiling_divide(required_width, item_width)
            print(f"  Width pieces needed: {required_width} ÷ {item_width} = {pieces_needed_rounded} (rounded up)")
            
            # Check if this is practical
            if pieces_needed_rounded >= 2 and pieces_needed_rounded <= 20:
                print(f"  ✓ Within practical limits (2-20 pieces)")
                joining_option = {
                    'base_item': item,
                    'pieces_needed': pieces_needed_rounded,
                    'join_direction': 'width',
                    'resulting_dimensions': {
                        'length': item_length,
                        'width': item_width * pieces_needed_rounded,
                        'depth': item_depth
                    },
                    'cost_multiplier': pieces_needed_rounded
                }
                joining_options.append(joining_option)
                print(f"  ✓ Added width joining option")
            else:
                print(f"  ❌ Outside practical limits: {pieces_needed_rounded}")
        else:
            print(f"  ❌ Length/depth constraints not satisfied")
            print(f"    Length: {item_length} >= {required_length} = {item_length >= required_length}")
            print(f"    Depth: {item_depth} >= {required_depth} = {item_depth >= required_depth}")
        
        # Check if we can join pieces along depth dimension  
        if (item_length >= required_length and
            item_width >= required_width):
            
            print(f"  ✓ Length and width constraints satisfied for depth joining")
            
            pieces_needed_rounded = ceiling_divide(required_depth, item_depth)
            print(f"  Depth pieces needed: {required_depth} ÷ {item_depth} = {pieces_needed_rounded} (rounded up)")
            
            if pieces_needed_rounded >= 2 and pieces_needed_rounded <= 20:
                print(f"  ✓ Depth joining within limits")
                joining_option = {
                    'base_item': item,
                    'pieces_needed': pieces_needed_rounded,
                    'join_direction': 'depth',
                    'resulting_dimensions': {
                        'length': item_length,
                        'width': item_width,
                        'depth': item_depth * pieces_needed_rounded
                    },
                    'cost_multiplier': pieces_needed_rounded
                }
                joining_options.append(joining_option)
                print(f"  ✓ Added depth joining option")
            else:
                print(f"  ❌ Depth joining outside limits: {pieces_needed_rounded}")
        else:
            print(f"  ❌ Length/width constraints not satisfied for depth joining")
    
    return joining_options

if __name__ == "__main__":
    # Test data matching our project 5 scenario
    cut = {
        'length': 1800,    # 1800mm length
        'width': 700,      # 700mm width 
        'depth': 90,       # 90mm thickness/depth
        'allow_joining': 1
    }

    inventory_item = {
        'id': 22,
        'length': 2400,    # 2400mm length
        'width': 45,       # 45mm width
        'height': 90,      # 90mm thickness
        'depth': 90        # Also set depth for compatibility
    }

    print('=== Testing Project 5 Joining Scenario ===')
    print(f'Cut needs: {cut["length"]}×{cut["width"]}×{cut["depth"]}mm')
    print(f'Available: {inventory_item["length"]}×{inventory_item["width"]}×{inventory_item["height"]}mm')

    joining_options = _can_join_pieces_simple(cut, [inventory_item])

    print(f'\n=== Results ===')
    print(f'Found {len(joining_options)} joining option(s):')
    for i, option in enumerate(joining_options):
        print(f'  Option {i+1}: {option["join_direction"]} joining')
        print(f'    Pieces needed: {option["pieces_needed"]}')
        print(f'    Resulting size: {option["resulting_dimensions"]}')
        print(f'    Cost multiplier: {option["cost_multiplier"]}')
