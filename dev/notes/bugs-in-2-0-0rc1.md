# Bugs in 2.0.0-rc1

- frontend templates/controld-panel.js contains the create code for all ui controls. These should be moved to their own separate files, ideally to the already available view classes under templates/views/*-view.js.

- table
    - the column titles stay fixed but are not opaque so that when scrolling data up, it can be seen beneath the column titles.
    - when I change the width of a column, the next column to the right is just made smaller. Instead, all columns to the right should keep their size and the total table width must get larger.
    