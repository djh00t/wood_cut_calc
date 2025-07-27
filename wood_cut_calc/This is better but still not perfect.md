This is better but still not perfect.

The cuts I have entered are:

Name: Lounge room side panel
Qty: 2
Length: 2260
Width: 435
Thickness: 0

Note: I expect to match all pieces of wood that are at least 2260 x 435mm If there is no match then this cut should be shown as an exception without matching timber in the inventory. Show the closest matches but don't create a cutting plan for this cut.

Name: Cat Door Front
Qty: 1
Length: 805
Width: 500
Thickness: 0

Note: I expect this to match all pieces of wood that are at least 805 x 500mm If there is no match then this cut should be shown as an exception without matching timber in the inventory. Show the closest matches but don't create a cutting plan for this cut.

Name: Cat Door Top/Bottom
Qty: 2
Length: 805
Width: 70
Thickness: 0

Note: I expect this to match all pieces of wood that are at least 805 x 70mm.
If there is no match then this cut should be shown as an exception without matching timber in the inventory. Show the closest matches but don't create a cutting plan for this cut.

Name: Cat Door Sides
Qty: 2
Length: 500
Width: 70
Thickness: 0

Note: I expect this to match all pieces of wood that are at least 500 x 70mm.
If there is no match then this cut should be shown as an exception without matching timber in the inventory. Show the closest matches but don't create a cutting plan for this cut.

Once all of these cuts are combined, the cutting plan should try and fit this
group of cuts into the most cost effective combination of inventory given the
variables provided like timber species and timber quality.

Now that we have effectively added a wildcard for thickness and or width, the
matching logic will need to return and give the user a set of possible
solutions to choose from. Initially we will look for solutions without joins,
but later we might offer solutions with joins.

In this situation if we have 3mm, 7mm, 12mm and 18mm plywood in the inventory
that is at least 2260mm Long and 805mm wide we should be able to return the
user 4 possible solutions showing cost and quality based on the available inventory.