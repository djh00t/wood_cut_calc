# Product Context: Wood Cutting Calculator

## Problem Solved

The Wood Cutting Calculator addresses a critical challenge in woodworking projects: efficiently planning how to cut required parts from stock material while minimizing waste and cost. It specifically solves these problems:

1. **Efficient Material Usage**: Optimizes the allocation of cuts to minimize waste
2. **Wildcard Dimension Handling**: Supports flexible dimensions (width=0 or depth=0) where the exact measurement isn't critical
3. **Multiple Solution Generation**: Presents several viable cutting plans for user selection
4. **Visual Representation**: Provides clear visual cutting diagrams with part labeling
5. **Cost Optimization**: Helps reduce material costs through efficient planning

## User Experience Goals

The application aims to provide:

1. **Intuitive Interface**: Easily add inventory items and required cuts
2. **Clear Visualization**: Visual representation of cutting plans with proper measurements
3. **Comprehensive Information**: Shopping lists, waste calculations, and part numbering
4. **Multiple Alternatives**: Several cutting plan options with different trade-offs
5. **Flexible Specifications**: Support for wildcard dimensions when exact measurements aren't critical

## Current User Experience Issues

The frontend currently has these issues:

1. **Incomplete Visualization**: SVG diagrams are not displaying properly
2. **Missing Shopping List**: The shopping list section is not showing
3. **Missing Part Numbering**: The part identification system isn't visible
4. **Partial Wildcard Support**: Wildcard assignments appear but aren't reflected in visualizations

## User Workflows

### Creating a Cutting Plan

1. User creates or selects a project
2. User adds required cuts with dimensions
3. User sets wildcard dimensions (0) where flexibility is allowed
4. User generates cutting plan
5. System displays multiple potential solutions
6. User views detailed cutting diagrams for each sheet
7. User saves preferred solution for future reference

### Viewing and Using Cutting Plans

1. User views comprehensive shopping list for materials
2. User examines cutting diagrams for each sheet
3. User references part numbering (sheet_id.part_id) to identify specific pieces
4. User can print or save diagrams for workshop use

## Target Users

1. **Hobbyist Woodworkers**: Individuals working on DIY furniture or home projects
2. **Professional Carpenters**: Professionals looking to optimize material usage
3. **Small Woodworking Shops**: Small businesses seeking to minimize waste and costs
4. **Educational Settings**: Woodworking classes teaching efficient material planning

## Value Proposition

1. **Cost Savings**: Reduce material waste by optimizing cutting layouts
2. **Time Efficiency**: Quickly generate optimal cutting plans instead of manual planning
3. **Flexibility**: Support for wildcard dimensions when exact measurements aren't critical
4. **Multiple Options**: Generated alternatives to choose from based on different criteria
5. **Clear Instructions**: Visual guides and part numbering for workshop execution

## Current Improvement Focus

The current focus is on fixing frontend integration issues to ensure the full functionality is accessible to users:

1. Ensure SVG cutting diagrams display properly
2. Fix shopping list display
3. Implement proper part numbering visualization
4. Complete the wildcard dimension handling in the user interface
5. Address "No matching inventory" issues with better user feedback
