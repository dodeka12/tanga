# Bugs/Features in 2.0.0-rcX

## Bugs

## Refactors

- frontend templates/controld-panel.js contains the create code for all ui controls. These should be moved to their own separate files, ideally to the already available view classes under templates/views/*-view.js.

## Features

- the table and tableview already support enum as column type. I would like to also have a type like enum, where the set of allowed elements are the de-duped values of another column. For example, the first column could be names of pupils and another column would be the selection from the pupils to list preferences for a seating plan. 
- as a generalization of the column type, there should be a custom enum type. If this type is used, the user must register a handler in the backend that provides the list of available entities, every time a cell in this column enters edit mode and must initialize the dropdown box.
