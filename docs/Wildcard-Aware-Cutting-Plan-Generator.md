# Wildcard-Aware Cutting Plan Generator

## 📌 Problem Definition

This system should:

* Takes as input a list of parts and an inventory of available timber sheets.
* Allocates parts to sheets optimally, minimizing waste and cost.
* Allows rotation of parts to maximize fit.
* Handles wildcard dimensions (0 thickness) by generating up to 5 distinct
  cutting plans with different wildcard-to-inventory assignments.
* Outputs clear, fully freestanding deliverables per solution, including bill
  of materials, labeled cutting diagrams, cost breakdowns, and waste summaries.
* Provide a flexible easy to use way of finding the best product and cutting
  solution for every project.

## 📌 Inputs

### Parts List

Each project part must include:

* Project: selector
* Timber Species: selector
* Timber Quality: selector
* Label/Description: string
* Length (mm): integer
* Width (mm): integer
* Thickness (mm): integer (0 indicates wildcard thickness)
* Quantity: integer

### Inventory

Each inventory item must include:

* Supplier: selector
* Timber Species: selector
* Product Name: string
* Quality: selector
* Length (mm): integer
* Width (mm): integer
* Thickness (mm): integer
* Price: float

Optional:

* Link: string

### Projects

* Project Name: string
* Description: string (multiline)
* Rotation Allowed: bool (default: true)
* Maximum Solutions: int (default: 5)

## 📌 Processing Phases

1. Strict Matching Phase:
  1.1 Parts with non-zero thickness must be assigned first.
  1.2 Strict thickness matching required.
  1.3 Parts can be rotated to maximize fit.
  1.4 Multiple parts can be cut from a single sheet.
2. Wildcard Matching Phase:
  2.1 Wildcard thickness parts (where thickness = 0) are matched flexibly to
      inventory thicknesses.
  2.2 Explore different wildcard assignment combinations.
  2.3 Generate up to 5 optimized full solutions based on wildcard choices.
3. Cutting Layout Optimization:
  3.1 Apply 2D bin-packing optimization.
  3.2 Rotate parts if it improves fit.
  3.3 Maximize the number of parts per sheet.
  3.4 Minimize waste.

## 📌 Outputs

Each solution (up to 5) must include the following freestanding deliverables:

### 1. 📋 Bill of Materials/Shopping List

* A list of inventory required for the solution including
  * Product Name
  * Length
  * Width
  * Thickness
  * Qty
  * Unit Price
  * Total Price

* For each piece of timber used:
  * Inventory ID eg: "1"
  * Product Name
  * Length
  * Width
  * Thickness
  * List of parts placed on the sheet.
    * Part ID should be labelled {sheet_id}.{part_id} eg: "1.01"
    * Part Label/Name E.g., Lounge Side Panel #1, Lounge Side Panel #2
    * Part Length, Width, Thickness
  * Diagram of sheet overlaid with shaded and outlined parts with measurements
  * Diagram should show waste as red shaded areas

### 2. 🖼️ Cutting Diagrams

* One SVG per sheet.
* File should be downloadable but dynamically generated so we don't save them
  to disk.
* Layout the full sheet scaled appropriately.
* Draw each part rectangle:
* Part Name and Part Number labeled inside or near rectangle.
* Dimensions (Length x Width) labeled.
* Distinct color or hatch pattern for different parts.
* Rotation shown correctly (if applied).
* Wasted space (unused areas) clearly visible (e.g., lightly shaded or marked).
* Origin of sheet is the bottom-left (0,0).

## 📌 Naming Conventions

Each identical part must be uniquely numbered for example:

* Lounge Side Panel #1
* Lounge Side Panel #2
* Cat Door Front #1
* Cat Door Top/Bottom #1
* Cat Door Top/Bottom #2

## 📌 Acceptance Criteria

### ✅ For each solution

* All fixed-thickness parts are matched and allocated first.
* Wildcard-thickness parts are assigned intelligently.
* No more than 5 full solution sets are generated.
* Each solution set is complete and self-contained.
* Parts may rotate to optimize fit.
* Bill of Materials includes:
  * sheet dimensions
  * thickness
  * parts
  * cost
  * waste
* Each part instance is uniquely numbered in BOM and diagrams.
* Cutting diagrams are readable, accurately scaled, and labeled.
* Total waste is minimized in all solutions.
* No external references required to understand or use the outputs.

## 🛠 Notes for LLM Implementation

* You must solve this as a bin-packing problem.
* Allow rotation of parts.
* The matching logic must prioritize fitting the maximum number of parts per inventory
  sheet to minimize waste.
* Solutions should differ by varying inventory items chosen.
* Inventory items must be equal to or larger than the dimensions of the parts being cut.
* Cutting diagrams must prioritize readability and professional presentation.
