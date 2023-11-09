-- File structure of tool

app
    -> main.py
    -> data
        -> raman
        -> nova
    -> saved_data
        -> raman
        -> nova

-- What do I need to run the tool?

You need a a way of running Python 3 code. This tool was made on Linux with Python 3.9, it should work with any Python 3.x install however. I have done no testing on Windows or Mac devices, although I can see no reason why it shouldn't work on the former (the latter who knows). You need to maintain the file structure above for the code to work. To do this, you should manually create empty saved data (and its children raman and nova) folders. This is required (I could have coded it...)

-- How do I run the tool?

Run main.py however you run Python files comfortably. I run it from the command line using `python3 main.py`. If you wanted to make a desktop shortcut attached to some shell script, you could then click on the shortcut and it would open.

-- How to input data into tool?

Place your NOVA outputted CV .txt files or Raman .txt files under data/nova or data/raman respectively. In terms of the formatting of the files, see the included demo files/code (process_file method) to understand. Spaces are allowed in the file names, but avoid periods '.'. The tool will still work, but the files will have clipped or incorrect names. For the NOVA files, the default .txt export function from NOVA for CV data should work with this tool (semicolon delimited). This tool will break if your file column headers do not mirror those of the demo file, for example if you have 'Potential Applied (kV)' not 'Potential Applied (V)'. As the source code is included, if alterations are needed feel free.

-- Features of tool

Viewing of CV and Raman graphs -> uses matplotlib inside a tkinter gui to display graphs. Navigate to the Raman/NOVA txt file inside the GUI and click it for it to be displayed.

Peak analysis of CV or Raman graph -> For any Raman or CV graph (when only one CV is selected) peak positions can be extracted. Click the new peak button and then the boxes next to 'Bound 1' or 'Bound 2' to select the bounds of the peak. The box should be highlighted yellow. When yellow, click the peak boundary on the graph. The box should be filled with the appropriate x coordinate. When two bounds are selected the peak will be calculated and the result shown. The 'pick_radius' property defines how accurate you need to be with your mouse clicks to select the point on the graph. It is set to 1 in the code, meaning you have to be very accurate. You can edit this to your preference.

Saving feature of peak analysis or CV selections -> At any point, you can save your work. If you have analysed specific peaks on a Raman, hitting save will save these peak points and create a save file under app/saved_data/raman. The gui will reflect this. By opening the save file, your previous peak analysis will be autofilled. The same process occurs with single CV graphs. You can also save specific CV selections (say CVs 1, 5, 10 and 25). This appends '_CVs' to the file name and saves it under app/saved_data/nova. You can only have one saved CV selection per NOVA file. This could be changed but would require some coding.

Autodeletion of empty save files -> Save files of Raman/CV that contain no peak data, when saved will autodelete. Example, you analyse 1 peak in a Raman file and save. You then open the save file but delete that peak and hit save. This will delete that save file (as it is empty and of no use). Additionally, if it is the only save file within its folder, it will the delete the folder. It will do this recursively whilst the parent folders continue to be empty.

CV selection -> To select specific CVs from your NOVA data, you can enter the CV numbers via a comma separated list. It can accept ranges in a variety of formats, for example (1-5, 1 - 5 etc) alongside just single CV numbers. Should you mistype or enter a number greater than the number of CVs you took, the submit button will turn red and display 'error'. You can click it again once you have corrected your mistake and it should work once more.
