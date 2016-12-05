--- OverWorld Manager ---

Current Version: 1.2.1

Compatible ROMS: All (multilingual)

Currently Supported: BPRE, BPRE(JPAN), BPRS, BPEE, AXVE

===========================================

OW Types: Types determine the dimensions of your OW

FOR ALL ROMS:
1 = 16x32 (The hero)
2 = 32x32 (The hero riding his bike)
3 = 16x16 (The PokeBall)
4 = 64x64 (The size of the ferry which transports you through the Sevy Islands)

FIRE RED ONLY:
5 = 128x64 (SS Anne)

EMERALD/RUBY ONLY:
6 = 48x48
7 = 88x32
8 = 96x40



===========================================
--- Buttons ---

[Table Menu]: This one is only for JPAN's Engine

{Insert Table}: 	Creates a new table. It need 4 addresses: OW Pointer Address (0x3FC Bytes) ### 0x4(bytes of OW pointer) x 255(Max Num. of OWs)
 							  Table Data Address (0x23DC Bytes) ### 0x24(bytes of OW Data Pointer) x 255(Max Num. of OWs)
							  Frames Pointers ### It depends on the number of frames, if for e.x. every OW has 9 frames you would need [9 x 0x8(bytes of Frame Pointer)] x 255 = 0x47B8 bytes
							  Frames ### The frame size depends on the 'type' of the frame: 1 -> 0x100 bytes
															2 -> 0x200 bytes
															3 -> 0x080 bytes
															4 -> 0x800 bytes
															
								 ### So multiply the size of the frame times the num of frames per OW(for e.x. 9), multiplied by 255(Max Num of OWs) and there you have it
			Once you insert those addresses the Table will be created

			OWM can search for free space and assign it to any of the needed addresses. This can be done by leaving the desired Address Input empty.
				ex1. If I want OWM to find all the needed addresses in the insertion table windows just click OK and leave all the inputs blank
				ex2. I want to have a specific OW Pointers and Frames address. Sure, write the offset you want for those two and leave the other two empty 

			Also, OWM checks to make sure that the offsets you give it have enough free space. If not, it searches for an address, that has enough free space, from the given address


{Remove Table}:		Deletes the entire table with all of its OWs


==========================================

[Overworld Menu]:

General: From here you can manipulate the data of your OWs

{Add OW}:	Adds an OW to the selected table. You have to select the proper thype and number of frames. The OW is added in the end of the list. For the types info see the start.
			In v1.1 you can insert multiple OWs at the same timw. If you leave the third input empty its going to add one OW

{Insert OW}:	Inserts the OW in the place of the selected OW
				In v1.1 you can insert multiple OWs at the same timw. If you leave the third input empty its going to insert one OW

{Resize}: 	Resizes the selected OW. You can change both the type and the num of frames

{Remove}:	Deletes the OW 


=========================================

[Sprite Controls]

General: These buttons help you manipulate your OWs frames. Supported image types are png, jpg, bmp.

{Import Frames Sheet}:		Imports the Sprite's frames alongside its Palette. Things to note: 	
												1) Your file must contain the exact number of frames as the OW in the table
												2) The order that the frames will be inserted will be the same as in your file
												3) If you Sprite has more than 16 colors, OWM will just use the 16 first. For maximmum quality, in such cases, decrease your image's colors with a program like IrfanView


{Import Pokemon (Spriter's Resource)}:	Imports a Pokemon's frames and its Palette. For this you have to download Spriter's Resource sheet, cut any of the pokemon you want (the dimensions must be 64x128) and insert it.
										If you want to insert one of the pokemon that are larger than the others (Dialga, Palkia, Steelix) you'll have to insert them with the first method (Type 4's dimensions are 64x64 ;) )

{Import OW (Spriter's Resource)}		Same as above, only it inserts OWs from Spriters Resource

{Export Frames Sheet}				Exports the indexed OW (all of its frames)

{Palette Cleanup}:		Every time you import an OW, a new palette is created for that OW. This button searches for any unused palette and deletes it. Just click it once you have inserted some OWs to make sure no palette slot is getting wasted


=========================================

How the INI works:

1.When you open your ROM, OWM checks the rom's 'name' from address 0xAC. 

2.Then it checks the ini and loads the offsets from the respective profile
	
	* At this step, OWM checks if JPAN's ips engine was installed. If yes it will load from the [JPAN] profile
	* If the name at 0xAC is MrDS it will treat the name as BPRE. Then it will check for JPAN's engine normally
	
	

You also can create your own custom profiles. When a rom is loaded OWM checks the ini for profiles of the same rom base (The last entry on each profile) and gives you the option to load the rom with that profile.

=========================================

Some General things to note:

[*]OWM DOES NOT support custom inserted tables. That means that if (for example) you used JPAN's engine and inserted tables and OWs without the tool, you'll have to delete them and re-insert them with OWM.

	This happens for 2 reasons. 
									1: When OWM imports a table it doesn't just add pointers, it fiils the tables with other bytes to ensure that no other tool interferes with them. Also, at the end of the OW Pointers Table OWM writes three pointers, these are needed for it to function properly
									2: At the end of the frames of each OW the tool writes a pointer (F0 35 21 08). That way it can calculate the num of frames each OW has (It counts the number of frames bytes until it finds that pointer). So if OWM tries to load a custom table it will keep on search for that pointer until it reaches the end of the files and gives an error

[*]The reason that 'Original OW Table Pointers' is needed is because this address is where A-MAP loads the OWS from. When the Original Table gets repointed(the first time the rom is loaded) this pointer is changed also.

[*]The way Insert Table button works is this:

	It first counts how many OW Table pointers there are and then it checks how many free slots are at the end of the existing pointers. This is why the button gets enabled with the JPAN engine and not with the vanilla roms.
	
[*]When creating a custom profile in the ini, make sure the "Original OW Pointers Address" is the correct one.

	For example: 	In my custom profile "OW Table Pointers" = 0xA00000, and in that address I have 2 pointers. The first is 0x39FDB0 (pointer to the original ow pointers table) and 0x800000 (an inserted table). In that case
					when you would try to load your rom with your custom profile, OWM would give you an error. This happens because my original ow table was repointed and my first pointer (in 0xA00000) points to 0xFFFFFF. So bear the original table repointing in mind when creating custom profiles.
	
=========================================

How to Add support for multilingual ROMS:


There are two steps that need to be made. Add the corresponding offsets to the ini and add the OW Templates in the Files folder

-Editing the INI:

Create the profile for your rom. Don't forget to change the name (the one between the []) and the "Rom Base". To find the OW Limiter Address search for this 63 F9 01 1C 97 29 in your rom. The offset where the 0x97 is located, is that address

-Creating the templates

First, create a folder in the "Files" folder whose name will be the same as the profile you added in the ini. For ex if I added the profile for BPES then my folder would be named BPES.
Second, create the templates. The templates are actually the OW Data Struct for each OW Type. The best way to find them would be this:

Find a version of your rom that is already supported. Open that rom up with OWM and let it repoint the original table. Find an OW with the type you want and remember its number.
Go to your rom (the one that is not supported) and go to the OW Pointers table. *To find the OW Pointers Table open up OW Editor Rebirth's settings.ini and find the SpriteBank Address for your rom. Now search for a pointer that points to that address. This is the OW Pointers Table that consists only from pointers.

Find the pointer for the OW you selected earlier. For ex if your OW's number was 0 then its the first pointer on the table, if it was 78, then it is the 79th pointer.
Go to the address pointed by that pointer and copy 0x24 bytes. That was the OW Data Struct

Finally create new file in your hex editor and paste that data. Save the file in the folder you created earlier with the name "TemplateX" were X stand for the type of the OW. For ex if you just copied the Data of an OW that was type 2, name your file Template2
Do that for all the types that exist in your rom. The list is on top.

Note:
[*]You must create template for type 1 to 8. If a type doesnt exist in a rom (for ex type 8 in Fire Red) just add 36 0xFFs in the file. But create a Template for all the types!

[*]If you add support for another rom send me also your ini and templates so I can update the download links and everyone can get it :)

