from flask import Blueprint

bp = Blueprint('filters', __name__)

@bp.app_template_filter('sum_previous_lengths')
def sum_previous_lengths(index, cuts, total_length):
    """Calculate the left position for each cut section in the cutting diagram.
    
    Args:
        index: Current index in the loop
        cuts: List of cuts (each cut has a 'cut' property with actual cut data)
        total_length: Total length of the item
        
    Returns:
        Percentage position from the left
    """
    sum_length = 0
    for i in range(index):
        # Access the actual cut data from cuts[i]['cut']['length']
        cut_data = cuts[i].get('cut', cuts[i])  # Backward compatibility
        if isinstance(cut_data, dict) and 'length' in cut_data:
            sum_length += cut_data['length']
        elif 'length' in cuts[i]:
            sum_length += cuts[i]['length']  # Fallback for old structure
    
    return (sum_length / total_length) * 100
