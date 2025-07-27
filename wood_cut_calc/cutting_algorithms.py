# wood_cut_calc/cutting_algorithms.py
"""Advanced cutting plan optimization algorithms with cost optimization."""

import logging
from typing import Any, Dict, List, Optional, Tuple, TypedDict

logger = logging.getLogger(__name__)


class CutAssignment(TypedDict):
    """Assignment of a cut to a position on a sheet for SVG/cutting plan.

    Attributes:
        cut: The cut dictionary (part details).
        x: X position on the sheet (mm).
        y: Y position on the sheet (mm).
        rotated: Whether the cut is rotated.
        part_id: Part number or label for display.
        sheet_id: ID of the sheet this cut is assigned to.
    """
    cut: dict[str, Any]
    x: int
    y: int
    rotated: bool
    part_id: str
    sheet_id: str


class PlacedCut(TypedDict):
    """A cut that has been placed on a sheet with position information."""
    cut: dict[str, Any]
    x: int
    y: int
    width: int
    height: int
    rotated: bool
    part_id: str


class SheetLayout(TypedDict):
    """Layout information for a single sheet."""
    item: dict[str, Any]
    cuts: List[PlacedCut]
    waste_area: int
    utilization_percent: float
    cost_efficiency_score: float


class WildcardAssignment(TypedDict):
    """Assignment of wildcard dimensions to specific inventory dimensions."""
    cut_id: int
    width: int
    height: int


class OptimizedSolution(TypedDict):
    """A complete optimized cutting solution."""
    total_cost: float
    waste_percentage: float
    cost_per_cut: float
    shopping_list: Dict[str, Any]
    cutting_plan: Dict[str, List[SheetLayout]]
    assignments: List[CutAssignment]
    wildcard_assignments: List[WildcardAssignment]
    svg_diagrams: Dict[str, str]
    efficiency_metrics: Dict[str, Any]


def _expand_cuts_by_quantity(
    cuts: List[dict[str, Any]]
) -> List[dict[str, Any]]:
    """Expand cuts based on their quantity to create individual cut instances.
    
    Args:
        cuts: List of cut definitions with quantities.
        
    Returns:
        List of individual cuts (one per required piece).
    """
    expanded = []
    for cut in cuts:
        quantity = cut.get('quantity', 1)
        for i in range(quantity):
            expanded_cut = cut.copy()
            expanded_cut['instance_id'] = f"{cut['id']}-{i+1}"
            expanded_cut['quantity'] = 1  # Each instance is quantity 1
            expanded.append(expanded_cut)
    return expanded


def _filter_compatible_inventory(
    cuts: List[dict[str, Any]],
    inventory: List[dict[str, Any]]
) -> List[dict[str, Any]]:
    """Filter inventory to only items that could potentially fit any cut.
    
    Args:
        cuts: List of cut requirements.
        inventory: Available inventory items.
        
    Returns:
        Filtered inventory list.
    """
    if not cuts:
        return []
    
    compatible = []
    for item in inventory:
        # Check if this inventory item could fit at least one cut
        item_length = item.get('length', 0)
        item_width = item.get('width', 0)
        item_height = item.get('height', 0)
        
        # Check if item can fit any cut
        can_fit_any = False
        for cut in cuts:
            cut_length = cut['length']
            cut_width = cut.get('width', 0)
            cut_height = cut.get('height', cut.get('depth', 0))
            
            # Check normal orientation
            if (item_length >= cut_length and
                    item_width >= cut_width and
                    item_height >= cut_height):
                can_fit_any = True
                break
            
            # Check rotated orientation (swap width and height)
            if (item_length >= cut_length and
                    item_width >= cut_height and
                    item_height >= cut_width):
                can_fit_any = True
                break
        
        if can_fit_any:
            compatible.append(item)
    
    return compatible


def _calculate_cost_efficiency(item: dict[str, Any], cuts_area: int) -> float:
    """Calculate cost efficiency score for an item.
    
    Args:
        item: Inventory item.
        cuts_area: Total area of cuts that would be placed.
        
    Returns:
        Efficiency score (higher is better).
    """
    item_area = item.get('length', 0) * item.get('width', 0)
    if item_area == 0:
        return 0.0
    
    utilization = cuts_area / item_area
    price_per_area = (item.get('price', 0) / item_area
                      if item_area > 0 else float('inf'))
    
    # Score combines utilization and cost efficiency
    # Higher utilization and lower price per area = better score
    return utilization / (price_per_area + 0.001)  # Avoid division by zero


def _calculate_solution_efficiency(solution: dict[str, Any]) -> float:
    """Calculate overall efficiency score for a solution.
    
    Args:
        solution: Complete cutting plan solution.
        
    Returns:
        Efficiency score (higher is better).
    """
    total_cost = solution.get('total_cost', float('inf'))
    waste_percentage = solution.get('waste_percentage', 100.0)
    efficiency_metrics = solution.get('efficiency_metrics', {})
    avg_utilization = efficiency_metrics.get('average_utilization', 0.0)
    
    # Avoid division by zero
    if total_cost <= 0:
        return 0.0
    
    # Calculate composite efficiency score
    # Higher utilization = better (weight: 40%)
    # Lower waste = better (weight: 30%)
    # Lower cost = better (weight: 30%)
    utilization_score = avg_utilization / 100.0  # Normalize to 0-1
    waste_score = (100.0 - waste_percentage) / 100.0  # Normalize to 0-1
    cost_score = 1.0 / (total_cost + 1.0)  # Inverse cost (normalized)
    
    # Weighted composite score
    efficiency_score = (
        0.4 * utilization_score +
        0.3 * waste_score +
        0.3 * cost_score
    )
    
    return efficiency_score


def _can_cut_fit(
    cut: dict[str, Any],
    item: dict[str, Any],
    allow_rotation: bool = True
) -> List[Tuple[int, int, bool]]:
    """Check if a cut can fit in an inventory item.
    
    Args:
        cut: Cut requirements.
        item: Inventory item.
        allow_rotation: Whether to allow 90-degree rotation.
        
    Returns:
        List of (width, height, rotated) tuples for valid placements.
    """
    cut_length = cut['length']
    cut_width = cut.get('width', 0)
    cut_height = cut.get('height', cut.get('depth', 0))
    
    item_length = item.get('length', 0)
    item_width = item.get('width', 0)
    item_height = item.get('height', 0)
    
    # Debug logging for thickness validation
    if cut.get('id') and item.get('id'):
        logger.debug(f"Checking fit: Cut {cut.get('id')} ({cut_length}x{cut_width}x{cut_height}) "
                    f"vs Item {item.get('id')} ({item_length}x{item_width}x{item_height})")
    
    fits = []
    
    # Check normal orientation
    if (cut_length <= item_length and
        cut_width <= item_width and
            cut_height <= item_height):
        fits.append((cut_width, cut_height, False))
        if cut.get('id') and item.get('id'):
            logger.debug(f"  -> Normal orientation FITS")
    elif cut.get('id') and item.get('id'):
        reasons = []
        if cut_length > item_length:
            reasons.append(f"length {cut_length} > {item_length}")
        if cut_width > item_width:
            reasons.append(f"width {cut_width} > {item_width}")
        if cut_height > item_height:
            reasons.append(f"height {cut_height} > {item_height}")
        logger.debug(f"  -> Normal orientation FAILS: {', '.join(reasons)}")
    
    # Check rotated orientation (swap width and height)
    if (allow_rotation and
        cut_length <= item_length and
        cut_height <= item_width and
            cut_width <= item_height):
        fits.append((cut_height, cut_width, True))
        if cut.get('id') and item.get('id'):
            logger.debug(f"  -> Rotated orientation FITS")
    elif allow_rotation and cut.get('id') and item.get('id'):
        reasons = []
        if cut_length > item_length:
            reasons.append(f"length {cut_length} > {item_length}")
        if cut_height > item_width:
            reasons.append(f"height {cut_height} > {item_width}")
        if cut_width > item_height:
            reasons.append(f"width {cut_width} > {item_height}")
        logger.debug(f"  -> Rotated orientation FAILS: {', '.join(reasons)}")
    
    return fits


def _pack_cuts_on_sheet(
    cuts: List[dict[str, Any]],
    item: dict[str, Any],
    allow_rotation: bool = True
) -> Tuple[List[PlacedCut], int]:
    """Pack cuts onto a single sheet using a bottom-left-fill algorithm.
    
    Args:
        cuts: List of cuts to place.
        item: Inventory item (sheet) to place cuts on.
        allow_rotation: Whether to allow rotation.
        
    Returns:
        Tuple of (placed_cuts, waste_area).
    """
    sheet_width = item.get('width', 0)
    sheet_height = item.get('height', 0)
    sheet_area = sheet_width * sheet_height
    
    placed_cuts = []
    occupied_areas = []  # List of (x, y, width, height) rectangles
    
    for i, cut in enumerate(cuts):
        # Get possible orientations for this cut
        orientations = _can_cut_fit(cut, item, allow_rotation)
        if not orientations:
            continue  # Skip cuts that don't fit
        
        # Try each orientation
        best_position = None
        best_orientation = None
        
        for width, height, rotated in orientations:
            # Find the best position using bottom-left-fill
            position = _find_best_position(
                width, height, sheet_width, sheet_height, occupied_areas
            )
            if position:
                if (best_position is None or
                        _is_better_position(position, best_position)):
                    best_position = position
                    best_orientation = (width, height, rotated)
        
        if best_position and best_orientation:
            x, y = best_position
            width, height, rotated = best_orientation
            
            # Place the cut
            placed_cut = PlacedCut(
                cut=cut,
                x=x,
                y=y,
                width=width,
                height=height,
                rotated=rotated,
                part_id=f"{item['id']}.{len(placed_cuts) + 1:02d}"
            )
            placed_cuts.append(placed_cut)
            
            # Mark the area as occupied
            occupied_areas.append((x, y, width, height))
    
    # Calculate waste (LINEAR for wood cutting, not area-based)
    # For wood cutting, waste is primarily linear along the length
    total_cut_length = sum(cut['cut']['length'] for cut in placed_cuts)
    item_length = item.get('length', 0)
    linear_waste = max(0, item_length - total_cut_length)
    
    # For compatibility, also calculate area-based waste
    used_area = sum(cut['width'] * cut['height'] for cut in placed_cuts)
    waste_area = max(0, sheet_area - used_area)

    return placed_cuts, linear_waste  # Return linear waste for wood cutting


def _find_best_position(
    width: int,
    height: int,
    sheet_width: int,
    sheet_height: int,
    occupied_areas: List[Tuple[int, int, int, int]]
) -> Optional[Tuple[int, int]]:
    """Find the best position for a rectangle using bottom-left-fill strategy.
    
    Args:
        width: Width of rectangle to place.
        height: Height of rectangle to place.
        sheet_width: Total sheet width.
        sheet_height: Total sheet height.
        occupied_areas: List of (x, y, w, h) for already placed rectangles.
        
    Returns:
        (x, y) position or None if no valid position found.
    """
    # Check if the piece fits in the sheet at all
    if width > sheet_width or height > sheet_height:
        return None
    
    # Try positions from bottom-left, scanning upward then rightward
    for y in range(sheet_height - height + 1):
        for x in range(sheet_width - width + 1):
            if not _overlaps_with_occupied(
                x, y, width, height, occupied_areas
            ):
                return (x, y)
    
    return None


def _overlaps_with_occupied(
    x: int,
    y: int,
    width: int,
    height: int,
    occupied_areas: List[Tuple[int, int, int, int]]
) -> bool:
    """Check if a rectangle overlaps with any occupied areas.
    
    Args:
        x, y: Position of rectangle.
        width, height: Dimensions of rectangle.
        occupied_areas: List of occupied rectangles.
        
    Returns:
        True if there's an overlap.
    """
    for ox, oy, ow, oh in occupied_areas:
        if not (x >= ox + ow or x + width <= ox or
                y >= oy + oh or y + height <= oy):
            return True
    return False


def _is_better_position(
    pos1: Tuple[int, int],
    pos2: Tuple[int, int]
) -> bool:
    """Determine if position 1 is better than position 2.
    
    Uses lower-left preference for better positioning.
    
    Args:
        pos1: First position (x, y).
        pos2: Second position (x, y).
        
    Returns:
        True if pos1 is better.
    """
    x1, y1 = pos1
    x2, y2 = pos2
    
    # Prefer lower y position, then leftward x position
    if y1 != y2:
        return y1 < y2
    return x1 < x2


def _is_duplicate_solution(solution: dict[str, Any],
                           existing_solutions: List[dict[str, Any]]) -> bool:
    """Check if a solution is a duplicate of any existing solutions.
    
    Compares key metrics to determine if solutions are essentially the same.
    
    Args:
        solution: Solution to check.
        existing_solutions: List of existing solutions.
        
    Returns:
        True if solution is a duplicate.
    """
    if not existing_solutions:
        return False
        
    for existing in existing_solutions:
        # Check if this solution uses different inventory items
        solution_items = set()
        existing_items = set()

        # Extract inventory item IDs used in each solution
        for plan_name, sheet_list in solution.get('cutting_plan', {}).items():
            if isinstance(sheet_list, list):
                for sheet in sheet_list:
                    base_id = (sheet['item'].get('base_item_id') or
                               sheet['item'].get('id'))
                    solution_items.add(base_id)

        for plan_name, sheet_list in existing.get('cutting_plan', {}).items():
            if isinstance(sheet_list, list):
                for sheet in sheet_list:
                    base_id = (sheet['item'].get('base_item_id') or
                               sheet['item'].get('id'))
                    existing_items.add(base_id)

        # Get strategy names for debugging
        solution_metrics = solution.get('efficiency_metrics', {})
        existing_metrics = existing.get('efficiency_metrics', {})
        solution_strategy = solution_metrics.get('strategy', '')
        existing_strategy = existing_metrics.get('strategy', '')

        # Debug logging
        logger.info(f"Comparing {solution_strategy} vs {existing_strategy}:")
        logger.info(f"  Solution items: {solution_items}")
        logger.info(f"  Existing items: {existing_items}")
        logger.info(f"  Same items: {solution_items == existing_items}")
        logger.info(f"  Solution cost: ${solution['total_cost']:.2f}")
        logger.info(f"  Existing cost: ${existing['total_cost']:.2f}")
        logger.info(f"  Cost diff: ${abs(solution['total_cost'] - existing['total_cost']):.2f}")

        # If using different base inventory items, not a duplicate
        if solution_items != existing_items:
            logger.info(f"  -> Not duplicate: using different inventory items")
            continue

        # If strategies are different, allow more tolerance
        if solution_strategy != existing_strategy:
            # For different strategies, only consider duplicate if very similar
            cost_tolerance = 5.0  # $5 difference allowed
            waste_tolerance = 5.0  # 5% waste difference allowed
        else:
            # Same strategy should be more strict
            cost_tolerance = 0.01
            waste_tolerance = 0.1

        # Compare key metrics with appropriate tolerance
        cost_diff = abs(solution['total_cost'] - existing['total_cost'])
        same_cost = cost_diff < cost_tolerance
        waste_diff = abs(solution['waste_percentage'] -
                         existing['waste_percentage'])
        same_waste = waste_diff < waste_tolerance
        same_sheets = (len(solution['assignments']) ==
                       len(existing['assignments']))

        logger.info(f"  Same cost (tolerance ${cost_tolerance}): {same_cost}")
        logger.info(f"  Same waste (tolerance {waste_tolerance}%): {same_waste}")
        logger.info(f"  Same sheet count: {same_sheets}")

        if same_cost and same_waste and same_sheets:
            logger.info(f"  -> DUPLICATE detected")
            return True
        else:
            logger.info(f"  -> Not duplicate: different metrics")
    
    return False


def _can_join_pieces(cut: dict[str, Any], 
                     inventory: list[dict[str, Any]]) -> List[dict[str, Any]]:
    """Check if smaller pieces can be joined to meet cut requirements.
    
    Args:
        cut: Cut requirements.
        inventory: Available inventory items.
        
    Returns:
        List of joining combinations that could satisfy the cut.
    """
    joining_options = []
    
    required_length = cut['length']
    required_width = cut['width'] 
    required_depth = cut['depth']
    
    for item in inventory:
        item_length = item.get('length', 0)
        item_width = item.get('width', 0) 
        item_depth = item.get('depth', item.get('height', 0))
        
        # Option 1: Join pieces along width dimension only
        if (item_length >= required_length and
            item_depth >= required_depth):
            
            pieces_needed_width = int(-(-required_width // item_width))
            
            if pieces_needed_width >= 2 and pieces_needed_width <= 20:
                joining_option = {
                    'base_item': item,
                    'pieces_needed': pieces_needed_width,
                    'join_direction': 'width',
                    'resulting_dimensions': {
                        'length': item_length,
                        'width': item_width * pieces_needed_width,
                        'depth': item_depth
                    },
                    'cost_multiplier': pieces_needed_width,
                    'description': f'{pieces_needed_width} pieces joined width-wise'
                }
                joining_options.append(joining_option)
        
        # Option 2: Join pieces along depth dimension only  
        if (item_length >= required_length and
            item_width >= required_width):
            
            pieces_needed_depth = int(-(-required_depth // item_depth))
            
            if pieces_needed_depth >= 2 and pieces_needed_depth <= 20:
                joining_option = {
                    'base_item': item,
                    'pieces_needed': pieces_needed_depth,
                    'join_direction': 'depth',
                    'resulting_dimensions': {
                        'length': item_length,
                        'width': item_width,
                        'depth': item_depth * pieces_needed_depth
                    },
                    'cost_multiplier': pieces_needed_depth,
                    'description': f'{pieces_needed_depth} pieces laminated depth-wise'
                }
                joining_options.append(joining_option)
        
        # Option 3: Multi-dimensional joining (width AND depth)
        # This creates a grid of pieces: X wide × Y deep
        pieces_width = int(-(-required_width // item_width))
        pieces_depth = int(-(-required_depth // item_depth))
        
        if (item_length >= required_length and 
            pieces_width >= 2 and pieces_width <= 10 and
            pieces_depth >= 2 and pieces_depth <= 10):
            
            total_pieces = pieces_width * pieces_depth
            if total_pieces <= 40:  # Reasonable limit
                joining_option = {
                    'base_item': item,
                    'pieces_needed': total_pieces,
                    'join_direction': 'multi',
                    'pieces_width': pieces_width,
                    'pieces_depth': pieces_depth,
                    'resulting_dimensions': {
                        'length': item_length,
                        'width': item_width * pieces_width,
                        'depth': item_depth * pieces_depth
                    },
                    'cost_multiplier': total_pieces,
                    'description': f'{pieces_width}×{pieces_depth} grid ({total_pieces} pieces)'
                }
                joining_options.append(joining_option)
    
    return joining_options


def _expand_inventory_with_joining(inventory: list[dict[str, Any]], 
                                   cuts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Expand inventory to include virtual joined pieces.
    
    Args:
        inventory: Original inventory items.
        cuts: Cut requirements (to determine what joins to consider).
        
    Returns:
        Expanded inventory including virtual joined pieces.
    """
    expanded_inventory = inventory.copy()
    
    # For each cut, check what joining options exist
    for cut in cuts:
        # Only consider joining if this cut allows it
        if not cut.get('allow_joining', False):
            continue
            
        joining_options = _can_join_pieces(cut, inventory)
        
        for option in joining_options:
            # Create a virtual inventory item representing the joined piece
            base_item = option['base_item']
            virtual_item = base_item.copy()
            
            # Debug logging for joining
            logger.info(f"Creating joined piece from item {base_item.get('id')} "
                       f"({base_item.get('product_name', 'Unknown')}) - "
                       f"{option['pieces_needed']} pieces needed")
            logger.info(f"  Base dimensions: {base_item.get('length', 0)}x"
                       f"{base_item.get('width', 0)}x{base_item.get('height', 0)}mm")
            logger.info(f"  Join direction: {option['join_direction']}")
            logger.info(f"  Resulting dimensions: {option['resulting_dimensions']}")
            
            # Update dimensions to reflect joined piece
            result_dims = option['resulting_dimensions']
            virtual_item['length'] = result_dims['length']
            virtual_item['width'] = result_dims['width']
            # Use consistent naming - update both height and depth
            virtual_item['height'] = result_dims['depth']
            virtual_item['depth'] = result_dims['depth']
            
            # Update cost
            virtual_item['price'] = (
                base_item['price'] * option['cost_multiplier']
            )
            
            # Add identifier to show it's a joined piece
            virtual_item['id'] = (
                f"joined_{base_item['id']}_{option['pieces_needed']}x"
            )
            virtual_item['is_joined'] = True
            virtual_item['base_item_id'] = base_item['id']
            virtual_item['pieces_needed'] = option['pieces_needed']
            virtual_item['join_direction'] = option['join_direction']
            
            expanded_inventory.append(virtual_item)
    
    return expanded_inventory


def generate_basic_plan(
    cuts: list[dict[str, Any]],
    inventory: list[dict[str, Any]],
    allow_joining: bool = False,
) -> dict[str, Any]:
    """Generate optimized cutting plans with cost optimization.

    Args:
        cuts: List of cut dicts (may be sqlite3.Row, will be converted).
        inventory: List of inventory dicts (may be sqlite3.Row).

    Returns:
        Cutting plan solution dict with multiple optimized solutions.
    """
    # Convert all inputs to dicts if needed
    cuts = [dict(cut) if not isinstance(cut, dict) else cut for cut in cuts]
    inventory = [dict(item) if not isinstance(item, dict) else item
                 for item in inventory]
    
    if not cuts or not inventory:
        return {"solutions": []}
    
    logger.info(f"Generating optimized plans for {len(cuts)} cuts "
                f"using {len(inventory)} inventory items")
    
    # Expand cuts by quantity
    expanded_cuts = _expand_cuts_by_quantity(cuts)
    
    # Expand inventory with joining options if enabled
    if allow_joining:
        logger.info(
            "Timber joining enabled - expanding inventory with joining options"
        )
        working_inventory = _expand_inventory_with_joining(
            inventory, expanded_cuts
        )
    else:
        working_inventory = inventory
    
    # Filter inventory to compatible items only
    compatible_inventory = _filter_compatible_inventory(
        expanded_cuts, working_inventory
    )
    
    if not compatible_inventory:
        logger.warning("No compatible inventory items found for cuts")
        return {"solutions": []}
    
    # Generate multiple optimization strategies
    solutions = []
    
    # Strategy 1: Minimum Cost (prefer cheapest inventory items)
    solution1 = _generate_minimum_cost_solution(
        expanded_cuts, compatible_inventory
    )
    if solution1:
        logger.info("Strategy 1 (Minimum Cost) generated solution with "
                    "cost $%.2f", solution1['total_cost'])
        solutions.append(solution1)
    
    # Strategy 2: Prefer Timber Joining (filter to only timber items)
    timber_inventory = [item for item in compatible_inventory 
                       if 'Pine' in item.get('product_name', '') or 
                          '90' in item.get('product_name', '') or
                          '45' in item.get('product_name', '')]
    if timber_inventory:
        solution2 = _generate_minimum_cost_solution(
            expanded_cuts, timber_inventory
        )
        if solution2 and not _is_duplicate_solution(solution2, solutions):
            solution2['efficiency_metrics']['strategy'] = 'Timber Joining'
            logger.info("Strategy 2 (Timber Joining) generated unique solution "
                        "with cost $%.2f", solution2['total_cost'])
            solutions.append(solution2)
        elif solution2:
            logger.info("Strategy 2 (Timber Joining) generated duplicate solution")
        else:
            logger.info("Strategy 2 (Timber Joining) failed to generate solution")
    
    # Strategy 3: Prefer Plywood Lamination (filter to only plywood items)
    plywood_inventory = [item for item in compatible_inventory 
                        if 'Plywood' in item.get('product_name', '') or
                           'plywood' in item.get('product_name', '')]
    if plywood_inventory:
        solution3 = _generate_minimum_cost_solution(
            expanded_cuts, plywood_inventory
        )
        if solution3 and not _is_duplicate_solution(solution3, solutions):
            solution3['efficiency_metrics']['strategy'] = 'Plywood Lamination'
            logger.info("Strategy 3 (Plywood Lamination) generated unique solution "
                        "with cost $%.2f", solution3['total_cost'])
            solutions.append(solution3)
        elif solution3:
            logger.info("Strategy 3 (Plywood Lamination) generated duplicate solution")
        else:
            logger.info("Strategy 3 (Plywood Lamination) failed to generate solution")
    
    # Strategy 4: Prefer Different Length Timber (longest first)
    long_timber_inventory = [item for item in timber_inventory]
    long_timber_inventory.sort(key=lambda x: x.get('length', 0), reverse=True)
    if long_timber_inventory:
        solution4 = _generate_minimum_cost_solution(
            expanded_cuts, long_timber_inventory
        )
        if solution4 and not _is_duplicate_solution(solution4, solutions):
            solution4['efficiency_metrics']['strategy'] = 'Long Timber Preference'
            logger.info("Strategy 4 (Long Timber) generated unique solution "
                        "with cost $%.2f", solution4['total_cost'])
            solutions.append(solution4)
        elif solution4:
            logger.info("Strategy 4 (Long Timber) generated duplicate solution")
        else:
            logger.info("Strategy 4 (Long Timber) failed to generate solution")
    
    # Strategy 5: Prefer Different Length Timber (shortest first)
    short_timber_inventory = [item for item in timber_inventory]
    short_timber_inventory.sort(key=lambda x: x.get('length', 0))
    if short_timber_inventory:
        solution5 = _generate_minimum_cost_solution(
            expanded_cuts, short_timber_inventory
        )
        if solution5 and not _is_duplicate_solution(solution5, solutions):
            solution5['efficiency_metrics']['strategy'] = 'Short Timber Preference'
            logger.info("Strategy 5 (Short Timber) generated unique solution "
                        "with cost $%.2f", solution5['total_cost'])
            solutions.append(solution5)
        elif solution5:
            logger.info("Strategy 5 (Short Timber) generated duplicate solution")
        else:
            logger.info("Strategy 5 (Short Timber) failed to generate solution")
    
    # Strategy 6: Premium Quality Timber Only
    premium_inventory = [item for item in compatible_inventory 
                        if item.get('quality', '').lower() == 'premium']
    if premium_inventory:
        solution6 = _generate_minimum_cost_solution(
            expanded_cuts, premium_inventory
        )
        if solution6 and not _is_duplicate_solution(solution6, solutions):
            solution6['efficiency_metrics']['strategy'] = 'Premium Quality'
            logger.info("Strategy 6 (Premium Quality) generated unique solution "
                        "with cost $%.2f", solution6['total_cost'])
            solutions.append(solution6)
        elif solution6:
            logger.info("Strategy 6 (Premium Quality) generated duplicate solution")
        else:
            logger.info("Strategy 6 (Premium Quality) failed to generate solution")
    
    # Strategy 7: Tasmanian Oak (if available)
    oak_inventory = [item for item in compatible_inventory 
                    if 'Oak' in item.get('product_name', '') or
                       'Tasmanian' in item.get('product_name', '')]
    if oak_inventory:
        solution7 = _generate_minimum_cost_solution(
            expanded_cuts, oak_inventory
        )
        if solution7 and not _is_duplicate_solution(solution7, solutions):
            solution7['efficiency_metrics']['strategy'] = 'Tasmanian Oak'
            logger.info("Strategy 7 (Tasmanian Oak) generated unique solution "
                        "with cost $%.2f", solution7['total_cost'])
            solutions.append(solution7)
        elif solution7:
            logger.info("Strategy 7 (Tasmanian Oak) generated duplicate solution")
        else:
            logger.info("Strategy 7 (Tasmanian Oak) failed to generate solution")
    
    # Strategy 8: Single Supplier Optimization (Bunnings)
    bunnings_inventory = [item for item in compatible_inventory 
                         if item.get('supplier_id') == 1]  # Assuming Bunnings is ID 1
    if bunnings_inventory:
        solution8 = _generate_minimum_cost_solution(
            expanded_cuts, bunnings_inventory
        )
        if solution8 and not _is_duplicate_solution(solution8, solutions):
            solution8['efficiency_metrics']['strategy'] = 'Bunnings Only'
            logger.info("Strategy 8 (Bunnings Only) generated unique solution "
                        "with cost $%.2f", solution8['total_cost'])
            solutions.append(solution8)
        elif solution8:
            logger.info("Strategy 8 (Bunnings Only) generated duplicate solution")
        else:
            logger.info("Strategy 8 (Bunnings Only) failed to generate solution")
    
    # Limit to 8 solutions maximum to show more variety
    solutions = solutions[:8]
    
    # Sort solutions by total cost (cheapest first, most expensive last)
    if solutions:
        solutions.sort(key=lambda s: s.get('total_cost', float('inf')))
    
    # If no solutions generated, fall back to basic plan
    if not solutions:
        logger.warning("No optimized solutions found, "
                       "falling back to basic plan")
        return _generate_fallback_solution(cuts, inventory)
    
    logger.info("Generated %d optimized solutions "
                "(sorted by cost - cheapest first)", len(solutions))
    return {"solutions": solutions}


def _generate_minimum_cost_solution(
    cuts: List[dict[str, Any]],
    inventory: List[dict[str, Any]]
) -> Optional[dict[str, Any]]:
    """Generate solution optimized for minimum total cost."""
    # Sort inventory by price per area (ascending)
    sorted_inventory = sorted(
        inventory,
        key=lambda item: (item.get('price', 0) /
                          max(item.get('length', 1) * item.get('width', 1), 1))
    )
    
    return _generate_greedy_solution(cuts, sorted_inventory, "Minimum Cost")


def _generate_minimum_waste_solution(
    cuts: List[dict[str, Any]],
    inventory: List[dict[str, Any]]
) -> Optional[dict[str, Any]]:
    """Generate solution optimized for minimum waste."""
    # Sort inventory by area (ascending) to prefer smaller fitting sheets
    sorted_inventory = sorted(
        inventory,
        key=lambda item: item.get('length', 0) * item.get('width', 0)
    )
    
    return _generate_greedy_solution(cuts, sorted_inventory, "Minimum Waste")


def _generate_balanced_solution(
    cuts: List[dict[str, Any]],
    inventory: List[dict[str, Any]]
) -> Optional[dict[str, Any]]:
    """Generate solution balanced between cost and waste."""
    # Sort by a balanced score considering both cost and size
    def balanced_score(item):
        area = item.get('length', 0) * item.get('width', 0)
        price_per_area = item.get('price', 0) / max(area, 1)
        # Balance cost efficiency with size efficiency
        return price_per_area * 0.7 + (area / 1000000) * 0.3  # Normalize area
    
    sorted_inventory = sorted(inventory, key=balanced_score)
    return _generate_greedy_solution(
        cuts, sorted_inventory, "Balanced Cost-Waste"
    )


def _generate_max_utilization_solution(
    cuts: List[dict[str, Any]],
    inventory: List[dict[str, Any]]
) -> Optional[dict[str, Any]]:
    """Generate solution optimized for maximum material utilization."""
    # Try to find inventory items that closely match the cuts' total area
    total_cuts_area = sum(
        cut.get('length', 0) * cut.get('width', 0) for cut in cuts
    )
    
    def utilization_score(item):
        area = item.get('length', 0) * item.get('width', 0)
        # Prefer items whose area is close to but larger than cuts area
        if area < total_cuts_area:
            return float('inf')  # Too small
        return area - total_cuts_area  # Prefer smaller overage
    
    sorted_inventory = sorted(inventory, key=utilization_score)
    return _generate_greedy_solution(
        cuts, sorted_inventory, "Maximum Utilization"
    )


def _generate_bulk_efficiency_solution(
    cuts: List[dict[str, Any]],
    inventory: List[dict[str, Any]]
) -> Optional[dict[str, Any]]:
    """Generate solution that prefers fewer, larger sheets."""
    # Sort inventory by area (descending) to prefer larger sheets
    sorted_inventory = sorted(
        inventory,
        key=lambda item: item.get('length', 0) * item.get('width', 0),
        reverse=True
    )
    
    return _generate_greedy_solution(cuts, sorted_inventory, "Bulk Efficiency")


def _calculate_shipping_costs(
    used_sheets: List[dict[str, Any]]
) -> Tuple[float, dict[str, Any]]:
    """Calculate shipping costs grouped by supplier.
    
    Args:
        used_sheets: List of sheet layouts used in the solution.
        
    Returns:
        Tuple of (total_shipping_cost, shipping_by_supplier_dict).
    """
    shipping_by_supplier = {}
    total_shipping_cost = 0.0
    
    for sheet in used_sheets:
        item = sheet['item']
        supplier_id = item.get('supplier_id')
        
        if supplier_id and supplier_id not in shipping_by_supplier:
            # Each supplier charges shipping once per delivery
            shipping_cost = item.get('shipping_cost', 0.0)
            supplier_name = item.get(
                'supplier_name', f'Supplier {supplier_id}'
            )
            shipping_by_supplier[supplier_id] = {
                'supplier_id': supplier_id,
                'supplier_name': supplier_name,
                'shipping_cost': shipping_cost,
                'items': []
            }
            total_shipping_cost += shipping_cost
        
        # Add item to supplier's delivery
        if supplier_id:
            shipping_by_supplier[supplier_id]['items'].append(item.get('id'))
    
    return total_shipping_cost, shipping_by_supplier


def _generate_greedy_solution(
    cuts: List[dict[str, Any]],
    sorted_inventory: List[dict[str, Any]],
    strategy_name: str
) -> Optional[dict[str, Any]]:
    """Generate a solution using greedy algorithm with inventory ordering."""
    used_sheets = []
    remaining_cuts = cuts.copy()
    total_cost = 0.0
    
    while remaining_cuts:
        best_sheet = None
        best_placement = None
        best_efficiency = -1
        
        for item in sorted_inventory:
            # Try packing cuts on this sheet
            placed_cuts, waste_area = _pack_cuts_on_sheet(remaining_cuts, item, allow_rotation=True)
            
            if placed_cuts:  # If any cuts could be placed
                cuts_area = sum(cut['width'] * cut['height'] for cut in placed_cuts)
                efficiency = _calculate_cost_efficiency(item, cuts_area)
                
                if efficiency > best_efficiency:
                    best_efficiency = efficiency
                    best_sheet = item
                    best_placement = (placed_cuts, waste_area)
        
        if not best_sheet or not best_placement:
            break  # No more cuts can be placed
        
        # Use this sheet
        placed_cuts, linear_waste = best_placement
        total_cost += best_sheet.get('price', 0)
        
        # Calculate linear utilization for wood cutting
        item_length = best_sheet.get('length', 0)
        total_cut_length = sum(cut['cut']['length'] for cut in placed_cuts)
        utilization = (
            (total_cut_length / item_length * 100) if item_length > 0 else 0
        )
        
        sheet_layout = SheetLayout(
            item=best_sheet,
            cuts=placed_cuts,
            waste_area=linear_waste,  # Actually linear waste in mm
            utilization_percent=utilization,
            cost_efficiency_score=best_efficiency
        )
        used_sheets.append(sheet_layout)
        
        # Remove placed cuts from remaining cuts
        placed_cut_ids = {cut['cut']['instance_id'] for cut in placed_cuts}
        remaining_cuts = [cut for cut in remaining_cuts if cut['instance_id'] not in placed_cut_ids]
    
    if not used_sheets:
        return None

    # Calculate shipping costs
    sheet_dicts = [{'item': sheet['item']} for sheet in used_sheets]
    total_shipping_cost, shipping_by_supplier = _calculate_shipping_costs(
        sheet_dicts
    )
    total_cost += total_shipping_cost
    
    # Calculate overall metrics (LINEAR waste for wood cutting)
    total_linear_waste = sum(sheet['waste_area'] for sheet in used_sheets)
    total_material_length = sum(
        sheet['item'].get('length', 0)
        for sheet in used_sheets
    )
    # Linear waste percentage is more meaningful for wood cutting
    waste_percentage = (
        (total_linear_waste / total_material_length * 100)
        if total_material_length > 0 else 0
    )
    cost_per_cut = total_cost / len(cuts) if cuts else 0
    
    # Create shopping list - properly accumulate quantities for same items
    shopping_list: dict[str, dict[str, Any]] = {}
    for i, sheet in enumerate(used_sheets):
        item = sheet['item']
        
        # Check if this is a joined piece
        if item.get('is_joined', False):
            # For joined pieces, add the base items with correct quantities
            base_item_id = str(item.get('base_item_id', f'sheet_{i}'))
            pieces_needed = item.get('pieces_needed', 1)
            base_price = item.get('price', 0) / pieces_needed
            
            # Create a base item for shopping list
            base_item = item.copy()
            base_item['id'] = item.get('base_item_id')
            base_item['price'] = base_price
            base_item['length'] = item.get('length', 0)
            if item.get('join_direction') == 'width':
                base_item['width'] = item.get('width', 0) / pieces_needed
            else:  # join_direction == 'depth'
                base_item['depth'] = item.get('depth', 0) / pieces_needed
                base_item['height'] = item.get('height', 0) / pieces_needed
            
            # Remove joined-specific metadata from base item
            base_item.pop('is_joined', None)
            base_item.pop('base_item_id', None)
            base_item.pop('pieces_needed', None)
            base_item.pop('join_direction', None)
            
            if base_item_id in shopping_list:
                shopping_list[base_item_id]['quantity'] += pieces_needed
                shopping_list[base_item_id]['total_price'] += (
                    base_price * pieces_needed
                )
            else:
                shopping_list[base_item_id] = {
                    'item': base_item,
                    'quantity': pieces_needed,
                    'total_price': base_price * pieces_needed
                }
        else:
            # Regular item (not joined)
            item_id = str(item.get('id', f'sheet_{i}'))
            if item_id in shopping_list:
                shopping_list[item_id]['quantity'] += 1
                shopping_list[item_id]['total_price'] += item.get('price', 0)
            else:
                shopping_list[item_id] = {
                    'item': item,
                    'quantity': 1,
                    'total_price': item.get('price', 0)
                }
    
    # Create assignments for template compatibility
    assignments = []
    for sheet_index, sheet in enumerate(used_sheets):
        # Create unique sheet ID for each sheet instance
        item_id = sheet['item'].get('id', 'sheet')
        unique_sheet_id = f"{item_id}_{sheet_index + 1}"
        for cut in sheet['cuts']:
            assignment = CutAssignment(
                cut=cut['cut'],
                x=cut['x'],
                y=cut['y'],
                rotated=cut['rotated'],
                part_id=cut['part_id'],
                sheet_id=unique_sheet_id
            )
            assignments.append(assignment)
    
    solution = {
        'total_cost': total_cost,
        'material_cost': total_cost - total_shipping_cost,
        'shipping_cost': total_shipping_cost,
        'shipping_by_supplier': shipping_by_supplier,
        'waste_percentage': waste_percentage,
        'cost_per_cut': cost_per_cut,
        'shopping_list': shopping_list,
        'cutting_plan': {strategy_name: used_sheets},
        'assignments': assignments,
        'wildcard_assignments': [],  # TODO: Implement wildcard handling
        'svg_diagrams': {},  # Will be populated below
        'efficiency_metrics': {
            'strategy': strategy_name,
            'total_sheets_used': len(used_sheets),
            'average_utilization': sum(
                s['utilization_percent'] for s in used_sheets
            ) / len(used_sheets),
            'cuts_placed': len(assignments),
            'cuts_remaining': len(remaining_cuts)
        }
    }
    
    # Generate SVG diagrams
    try:
        from .svg_generator import generate_multi_sheet_cutting_diagram
        svg_diagrams = generate_multi_sheet_cutting_diagram(solution)
        solution['svg_diagrams'] = svg_diagrams
    except Exception as e:
        logger.warning("Failed to generate SVG diagrams: %s", e)
        solution['svg_diagrams'] = {}
    
    return solution


def _generate_fallback_solution(
    cuts: List[dict[str, Any]],
    inventory: List[dict[str, Any]]
) -> dict[str, Any]:
    """Generate a basic fallback solution when optimization fails."""
    if not inventory:
        return {"solutions": []}

    sheet = inventory[0]
    placements = []
    for cut in cuts:
        qty = cut.get("quantity", 1)
        for i in range(qty):
            placements.append({
                "sheet_id": sheet["id"],
                "cut_id": cut["id"],
                "label": cut["label"],
                "dimensions": {
                    "length": cut["length"],
                    "width": cut.get("width", 0),
                    "depth": cut.get("depth", cut.get("height", 0)),
                },
                "position": {"x": 0, "y": 0},
                "rotated": False,
                "part_id": f"{sheet['id']}.{i+1:02d}"
            })

    # Calculate shipping costs for fallback solution
    shipping_cost = sheet.get('shipping_cost', 0.0)
    material_cost = sheet.get("price", 0)
    total_cost = material_cost + shipping_cost

    return {
        "solutions": [
            {
                "total_cost": total_cost,
                "material_cost": material_cost,
                "shipping_cost": shipping_cost,
                "shipping_by_supplier": {
                    sheet.get('supplier_id', 'unknown'): {
                        'supplier_id': sheet.get('supplier_id'),
                        'supplier_name': sheet.get('supplier_name', 'Unknown'),
                        'shipping_cost': shipping_cost,
                        'items': [sheet.get('id')]
                    }
                } if sheet.get('supplier_id') else {},
                "waste_percentage": 0,
                "shopping_list": {
                    str(sheet.get("id", "1")): {
                        "item": sheet,
                        "quantity": 1,
                        "total_price": material_cost
                    }
                },
                "cutting_plan": {},
                "assignments": placements,
                "wildcard_assignments": [],
                "efficiency_metrics": {"strategy": "Fallback"}
            }
        ]
    }


__all__ = [
    "generate_basic_plan",
    "CutAssignment",
]
