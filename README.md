# MenuCreator
A Blender addon to quickly create custom menus for any Object.

## Features
- create a menu for any Blender object (one for each Object you want)
- add all the properties you want to the menu simply right clicking on any Blender property, and clicking Add to the Menu (operators not supported at the moment)
- collection functionality: you can create a list of collections from which the menu will list the contained objects. Add the collections right clicking 
- outfit functionality: as an extension of the collection functionality, it is possible to enable auto-masking of the objects listed in the menu. This means that you can define a Body object, and its mask modifiers will be activated when you show an Object in the collection list

## Instructions
- [check the video with the instruction](https://gofile.io/d/NPrmDS)

## FAQ
- *How can I add a property of an Object to the menu of another Object?*

By default, when you click on an Object, the addon will show the menu of the selected item. To pin the current Object Menu click on the Pin button on the first line (on the far left), and this will prevent the Menu to be changed when you select other Objects until you un-pin the Menu.

- *How can I show only one Object Menu, i.e. why does the Menu changes when I click on other Objects?*

This is the intended behaviour. To pin the current Object Menu click on the Pin button on the first line (on the far left), and this will prevent the Menu to be changed when you select other Objects until you un-pin the Menu.

- *I found an issue or I would like to suggest new functionalities*

You can open an Issue on GitHub (click on the Issue tab above). Please, try to be specific and include screenshots if possible.
