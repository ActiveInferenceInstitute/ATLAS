"""
Shared color scheme constants for the ATLAS visualization modules.

Each visualization module previously defined its own parallel color
mapping in its Visualizer class. The schemes are collected here as
named constants so the full palette is visible in one place, and a
palette change applies everywhere at once.

The visualizer classes reference these constants; the values are
preserved exactly as they were defined in each module.
"""

import matplotlib.pyplot as plt

# GraphVisualizer: node colors by ATLAS item type.
GRAPH_COLOR_SCHEMES = {
    'entity': '#1f77b4',      # Blue
    'pattern': '#ff7f0e',     # Orange
    'query': '#2ca02c',       # Green
    'attribute': '#d62728',   # Red
    'prompt_interface': '#9467bd'  # Purple
}

# MetricsVisualizer: colors for metric categories.
METRIC_COLORS = {
    'performance': '#3498db',    # Blue
    'usage': '#2ecc71',         # Green
    'quality': '#e74c3c',       # Red
    'growth': '#f39c12',        # Orange
    'efficiency': '#9b59b6'     # Purple
}

# NetworkVisualizer: colormaps for network analysis dimensions.
NETWORK_COLORS = {
    'community': plt.cm.Set3,
    'centrality': plt.cm.viridis,
    'degree': plt.cm.plasma,
    'clustering': plt.cm.coolwarm
}

# PatternVisualizer: colors for pattern hierarchy levels.
HIERARCHY_COLORS = {
    'root': '#ff6b6b',       # Red
    'intermediate': '#4ecdc4', # Teal
    'leaf': '#45b7d1',       # Blue
    'orphan': '#96ceb4'      # Green
}

# PatternVisualizer: color gradient for pattern effectiveness.
EFFECTIVENESS_COLORMAP = plt.cm.RdYlGn

# AnimationVisualizer: node colors for animation states.
ANIMATION_NODE_COLORS = {
    'entity': '#4CAF50',
    'pattern': '#2196F3',
    'query': '#FF9800',
    'attribute': '#9C27B0',
    'new': '#F44336',
    'active': '#FFC107',
    'complete': '#4CAF50'
}
