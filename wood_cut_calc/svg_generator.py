"""SVG generation utilities for cutting diagrams.

This module provides functions to generate SVG-based cutting diagrams,
which can be used to visualize cutting plans in a more professional way.
"""

import logging
from typing import Any, Dict, List, Optional

from .cutting_algorithms import CutAssignment

# Configure logging
logger = logging.getLogger(__name__)

# SVG styling constants
STYLES = {
    "sheet": {
        "fill": "#f8f9fa",
        "stroke": "#000000",
        "stroke-width": "1"
    },
    "cut": {
        "fill": "#28a745",
        "stroke": "#000000",
        "stroke-width": "1"
    },
    "waste": {
        "fill": "#dc3545",
        "fill-opacity": "0.7",
        "stroke": "#000000",
        "stroke-width": "1"
    },
    "text": {
        "font-family": "Arial, sans-serif",
        "font-size": "12px",
        "fill": "#ffffff"
    },
    "dimension-text": {
        "font-family": "Arial, sans-serif",
        "font-size": "10px",
        "fill": "#ffffff"
    }
}


def generate_cutting_diagram_svg(
    sheet_width: int,
    sheet_height: int,
    sheet_length: int,
    cut_assignments: List[CutAssignment],
    sheet_id: str
) -> str:
    """Generate an SVG cutting diagram for a single sheet.
    
    Args:
        sheet_width: Width of the sheet in mm
        sheet_height: Height (thickness) of the sheet in mm
        sheet_length: Length of the sheet in mm
        cut_assignments: List of cut assignments for this sheet
        sheet_id: ID of the sheet (e.g. "1.01")
        
    Returns:
        SVG diagram as a string
    """
    # Set up SVG dimensions and viewBox
    # We'll use a fixed height and scale the width proportionally
    svg_height = 200
    
    # Create SVG header
    svg = [
        f'<svg width="100%" height="{svg_height}" '
        f'viewBox="0 0 {sheet_length} {sheet_height}" '
        f'preserveAspectRatio="xMidYMid meet" '
        f'xmlns="http://www.w3.org/2000/svg">'
    ]
    
    # Add a style section
    svg.append('<style>')
    svg.append('.sheet { ' + 
               '; '.join([f"{k}: {v}" for k, v in STYLES["sheet"].items()]) + 
               ' }')
    svg.append('.cut { ' + 
               '; '.join([f"{k}: {v}" for k, v in STYLES["cut"].items()]) + 
               ' }')
    svg.append('.waste { ' + 
               '; '.join([f"{k}: {v}" for k, v in STYLES["waste"].items()]) + 
               ' }')
    svg.append('.cut-text { ' + 
               '; '.join([f"{k}: {v}" for k, v in STYLES["text"].items()]) + 
               ' }')
    svg.append('.dimension-text { ' + 
               '; '.join([f"{k}: {v}" 
                         for k, v in STYLES["dimension-text"].items()]) + ' }')
    svg.append('</style>')
    
    # Add sheet background
    svg.append(
        f'<rect class="sheet" width="{sheet_length}" height="{sheet_height}" />'
    )
    
    # Sort assignments by x position
    sorted_assignments = sorted(cut_assignments, key=lambda a: a["x"])
    
    # Add each cut
    for assignment in sorted_assignments:
        cut = assignment["cut"]
        x = assignment["x"]
        y = 0  # In 1D layout, all cuts start at y=0
        
        # Determine dimensions based on rotation
        if assignment["rotated"]:
            width = cut["depth"]
            height = cut["width"]
        else:
            width = cut["width"]
            height = cut["depth"]
        
        # Ensure height doesn't exceed sheet height
        height = min(height, sheet_height)
        
        # Add cut rectangle
        svg.append(
            f'<rect class="cut" x="{x}" y="{y}" '
            f'width="{cut["length"]}" height="{sheet_height}" />'
        )
        
        # Add cut label
        svg.append(
            f'<text class="cut-text" x="{x + 5}" y="{y + 15}">'
            f'{sheet_id}.{assignment["part_id"]} - {cut["label"]}'
            f'</text>'
        )
        
        # Add dimensions text
        svg.append(
            f'<text class="dimension-text" x="{x + 5}" y="{y + 30}">'
            f'{cut["length"]} × {width} × {height} mm'
            f'</text>'
        )
        
        # If rotated, add indicator
        if assignment["rotated"]:
            svg.append(
                f'<text class="dimension-text" x="{x + 5}" y="{y + 45}">'
                f'(rotated)'
                f'</text>'
            )
    
    # Add waste areas
    current_pos = 0
    for assignment in sorted_assignments:
        # Add waste before the cut if there's a gap
        if assignment["x"] > current_pos:
            waste_width = assignment["x"] - current_pos
            svg.append(
                f'<rect class="waste" x="{current_pos}" y="0" '
                f'width="{waste_width}" height="{sheet_height}" />'
            )
            
            # Add waste label if wide enough
            if waste_width > 20:
                svg.append(
                    f'<text class="cut-text" x="{current_pos + 5}" y="15">'
                    f'Waste ({waste_width} mm)'
                    f'</text>'
                )
        
        # Update position to end of this cut
        current_pos = assignment["x"] + assignment["cut"]["length"]
    
    # Add waste at the end if there's space left
    if current_pos < sheet_length:
        waste_width = sheet_length - current_pos
        svg.append(
            f'<rect class="waste" x="{current_pos}" y="0" '
            f'width="{waste_width}" height="{sheet_height}" />'
        )
        
        # Add waste label if wide enough
        if waste_width > 20:
            svg.append(
                f'<text class="cut-text" x="{current_pos + 5}" y="15">'
                f'Waste ({waste_width} mm)'
                f'</text>'
            )
    
    # Close SVG
    svg.append('</svg>')
    
    return '\n'.join(svg)


def generate_multi_sheet_cutting_diagram(
    solution: Dict[str, Any]
) -> Dict[str, str]:
    """Generate SVG diagrams for all sheets in a solution.
    
    Args:
        solution: A complete cutting solution
        
    Returns:
        Dictionary mapping sheet_id to SVG diagram
    """
    diagrams: Dict[str, str] = {}
    
    # Group assignments by sheet_id
    sheets: Dict[str, List[CutAssignment]] = {}
    for assignment in solution["assignments"]:
        sheet_id = assignment["sheet_id"]
        if sheet_id not in sheets:
            sheets[sheet_id] = []
        sheets[sheet_id].append(assignment)
    
    # Generate diagram for each sheet
    for sheet_id, assignments in sheets.items():
        # Get the sheet dimensions from the first assignment's inventory item
        first_assignment = assignments[0]
        sheet_info = _find_sheet_info(first_assignment, solution)
        
        if sheet_info:
            sheet_width = sheet_info["width"]
            sheet_height = sheet_info["height"]
            sheet_length = sheet_info["length"]
            
            svg = generate_cutting_diagram_svg(
                sheet_width, sheet_height, sheet_length, assignments, sheet_id
            )
            
            diagrams[sheet_id] = svg
    
    return diagrams


def _find_sheet_info(
    assignment: CutAssignment,
    solution: Dict[str, Any]
) -> Optional[Dict[str, int]]:
    """Find sheet information from a solution based on an assignment."""
    cut_id = assignment["cut"]["id"]
    
    # First try to find in wildcard assignments
    for wa in solution.get("wildcard_assignments", []):
        if wa["cut_id"] == cut_id:
            # Look up inventory item
            inventory_id = wa["inventory_id"]
            for item_data in solution["shopping_list"].values():
                if item_data["item"]["id"] == inventory_id:
                    return {
                        "width": item_data["item"]["width"],
                        "height": item_data["item"]["height"],
                        "length": item_data["item"]["length"]
                    }
    
    # If not found in wildcard assignments, look through cutting plan
    for dimension, plans in solution["cutting_plan"].items():
        for plan in plans:
            # Check if this plan contains our cut
            for cut in plan["cuts"]:
                if cut["cut"]["id"] == cut_id:
                    return {
                        "width": plan["item"]["width"],
                        "height": plan["item"]["height"],
                        "length": plan["item"]["length"]
                    }
    
    return None
