from flask import Blueprint, current_app

bp = Blueprint('filters', __name__)

@bp.app_template_filter('sum_previous_lengths')
def sum_previous_lengths(index, cuts, total_length):
    """
    Calculate the left position for each cut section in the cutting diagram.
    
    Args:
        index: Current index in the loop
        cuts: List of cuts
        total_length: Total length of the item
        
    Returns:
        Percentage position from the left
    """
    sum_length = 0
    for i in range(index):
        sum_length += cuts[i]['length']
    
    return (sum_length / total_length) * 100