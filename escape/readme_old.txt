This folder contains the code, images and sounds for the book Mission Python by Sean McManus

####

Code and sound effects by Sean McManus (www.sean.co.uk)
Images by Rafael Pimenta

You can use these assets to make your own Python games, provided that you credit the source and that you do not sell or otherwise make money from your games.

To find out more about the book, visit:
http://www.sean.co.uk/books/mission-python/

For information on Sean's other books, including Cool Scratch Projects in Easy Steps and Raspberry Pi For Dummies, visit:
http://www.sean.co.uk/books/index.shtm

####

These files include updates since the first print run of the book. 

These updates are:
Listing 7-5 has a new generate_map() instruction near the end
Listing 8-3 from the first pressing is no longer required
Later listings in chapter 8 have been renumbered (so Listing 8-4 in the first printing is now Listing 8-3 in this download)

You have a first print run if the first instruction after the #START# box on p143 is clock.schedule_interval(...). 
It should be generate_map()

####

These files were further updated in January 2021 to fix the following:

In Listing 8-2, the PLAYER_SHADOW dictionary uses animation frame 3 twice. The final image in the left dictionary should be images.spacesuit_left_4_shadow, for example, instead of images.spacesuit_left_3_shadow again. The same applies to the right, up, and down animation sequences.

On p164 in Listing 9-8, you can make the inventory easier to use by adding a delay to stop it cycling through the items too fast. After the display_inventory() instruction, add a time.sleep(0.2) instruction. This should be indented to the same depth as the display_inventory() instruction.

####